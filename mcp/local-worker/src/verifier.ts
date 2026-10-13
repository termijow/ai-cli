import fs from "node:fs/promises";
import path from "node:path";
import type { CommandRunner } from "./types.js";
import { runCommand } from "./command.js";

export interface VerificationReport {
  passed: boolean;
  syntaxOk: boolean;
  runtimeOk: boolean;
  errors: string[];
  warnings: string[];
}

export function extractHtmlScripts(htmlContent: string): string {
  const scriptRegex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
  const scripts: string[] = [];
  let match: RegExpExecArray | null;

  while ((match = scriptRegex.exec(htmlContent)) !== null) {
    const scriptTag = match[0];
    // Ignore external scripts like <script src="...">
    if (/src\s*=\s*['"]/i.test(scriptTag)) continue;
    const body = match[1].trim();
    if (body) scripts.push(body);
  }

  return scripts.join("\n;\n");
}

export function checkCssPointerEvents(htmlContent: string): string[] {
  const issues: string[] = [];
  const lower = htmlContent.toLowerCase();

  // Bug pattern found in benchmarks: overlay has pointer-events: none, but interactive elements lack pointer-events: auto
  if (lower.includes("pointer-events: none") || lower.includes("pointer-events:none")) {
    const hasOverlay = lower.includes("overlay") || lower.includes("modal");
    const hasPointerAuto = lower.includes("pointer-events: auto") || lower.includes("pointer-events:auto");

    if (hasOverlay && !hasPointerAuto) {
      issues.push(
        "UI clickability bug detected: overlay has 'pointer-events: none' without 'pointer-events: auto' on interactive elements/buttons, preventing user clicks.",
      );
    }
  }

  return issues;
}

const MOCK_DOM_PREAMBLE = `
global.window = global;
global.addEventListener = () => {};
global.removeEventListener = () => {};
global.innerHeight = 800;
global.innerWidth = 1200;
const mockElem = {
  addEventListener: () => {},
  removeEventListener: () => {},
  style: {},
  classList: { add: () => {}, remove: () => {} },
  textContent: '',
  innerText: '',
  getContext: () => ({
    fillRect(){}, strokeRect(){}, clearRect(){},
    beginPath(){}, moveTo(){}, lineTo(){}, arc(){},
    fill(){}, stroke(){}, save(){}, restore(){},
    translate(){}, scale(){}, createLinearGradient: () => ({ addColorStop(){} })
  }),
  clientWidth: 600,
  clientHeight: 600
};
global.document = {
  getElementById: () => mockElem,
  querySelector: () => mockElem,
  querySelectorAll: () => [mockElem],
  addEventListener: () => {},
  createElement: () => mockElem,
  body: mockElem
};
global.localStorage = { getItem: () => '0', setItem: () => {} };
global.AudioContext = class {
  constructor(){ this.currentTime = 0; this.destination = {}; this.state = 'running'; }
  createOscillator() { return { connect(){}, start(){}, stop(){}, frequency: { setValueAtTime(){} } }; }
  createGain() { return { connect(){}, gain: { setValueAtTime(){}, exponentialRampToValueAtTime(){} } }; }
  resume() { return Promise.resolve(); }
};
global.webkitAudioContext = global.AudioContext;
global.performance = { now: () => Date.now() };
global.requestAnimationFrame = () => 1;
global.cancelAnimationFrame = () => {};
`;

export async function verifyHtmlRuntime(
  htmlContent: string,
  runner: CommandRunner = runCommand,
): Promise<{ passed: boolean; error?: string }> {
  const js = extractHtmlScripts(htmlContent);
  if (!js.trim()) {
    return { passed: true };
  }

  const script = `${MOCK_DOM_PREAMBLE}\n${js}`;
  const result = await runner(
    "node",
    ["-e", script],
    {
      cwd: process.cwd(),
      timeoutMs: 8_000,
      maxOutputChars: 8_000,
    },
  );

  if (result.code !== 0) {
    const stderr = (result.stderr || result.stdout).trim();
    const lines = stderr.split(/\r?\n/).filter(Boolean);
    const errLine = lines.find((l) => /Error:/.test(l)) || lines[0] || "Unknown JavaScript runtime exception";
    return {
      passed: false,
      error: `JavaScript execution error in simulated DOM: ${errLine}`,
    };
  }

  return { passed: true };
}

export async function verifyFileSyntax(
  fullPath: string,
  runner: CommandRunner = runCommand,
): Promise<{ passed: boolean; error?: string }> {
  const ext = path.extname(fullPath).toLowerCase();

  if (ext === ".js" || ext === ".mjs" || ext === ".cjs") {
    const res = await runner("node", ["--check", fullPath], {
      cwd: path.dirname(fullPath),
      timeoutMs: 8_000,
    });
    if (res.code !== 0) {
      return {
        passed: false,
        error: `Syntax error in ${path.basename(fullPath)}: ${(res.stderr || res.stdout).trim()}`,
      };
    }
  } else if (ext === ".py") {
    const res = await runner("python", ["-m", "py_compile", fullPath], {
      cwd: path.dirname(fullPath),
      timeoutMs: 8_000,
    });
    if (res.code !== 0) {
      return {
        passed: false,
        error: `Python syntax error in ${path.basename(fullPath)}: ${(res.stderr || res.stdout).trim()}`,
      };
    }
  }

  return { passed: true };
}

export async function verifyWorktreeFiles(
  worktreePath: string,
  changedFiles: string[],
  runner: CommandRunner = runCommand,
): Promise<VerificationReport> {
  const errors: string[] = [];
  const warnings: string[] = [];
  let syntaxOk = true;
  let runtimeOk = true;

  for (const relFile of changedFiles) {
    const fullPath = path.join(worktreePath, relFile);
    let content = "";
    try {
      content = await fs.readFile(fullPath, "utf-8");
    } catch {
      continue; // Deleted file or unreadable
    }

    const ext = path.extname(relFile).toLowerCase();

    // 1. Static Syntax Checks
    const syntaxCheck = await verifyFileSyntax(fullPath, runner);
    if (!syntaxCheck.passed && syntaxCheck.error) {
      syntaxOk = false;
      errors.push(syntaxCheck.error);
    }

    // 2. HTML / DOM checks
    if (ext === ".html" || ext === ".htm") {
      const cssIssues = checkCssPointerEvents(content);
      if (cssIssues.length > 0) {
        runtimeOk = false;
        errors.push(...cssIssues);
      }

      const domCheck = await verifyHtmlRuntime(content, runner);
      if (!domCheck.passed && domCheck.error) {
        runtimeOk = false;
        errors.push(domCheck.error);
      }
    }
  }

  return {
    passed: errors.length === 0,
    syntaxOk,
    runtimeOk,
    errors,
    warnings,
  };
}
