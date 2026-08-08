import { spawn } from "node:child_process";
import type { CommandResult, RunCommandOptions } from "./types.js";

const DEFAULT_MAX_OUTPUT = 24_000;

function appendOutput(current: string, chunk: Buffer, maxChars: number): string {
  const next = current + chunk.toString("utf8");
  if (next.length <= maxChars) return next;
  return next.slice(0, maxChars) + "\n...[output truncated]";
}

export function runCommand(
  file: string,
  args: string[],
  options: RunCommandOptions,
): Promise<CommandResult> {
  const maxChars = options.maxOutputChars ?? DEFAULT_MAX_OUTPUT;

  return new Promise((resolve, reject) => {
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    let settled = false;

    const child = spawn(file, args, {
      cwd: options.cwd,
      env: options.env ?? process.env,
      shell: false,
      stdio: ["ignore", "pipe", "pipe"],
	  detached: process.platform !== "win32",
    });

	const terminate = (signal: NodeJS.Signals): void => {
	  if (process.platform !== "win32" && child.pid) {
		try {
		  process.kill(-child.pid, signal);
		  return;
		} catch {
		  // Fall back to the direct child if the process group already exited.
		}
	  }
	  child.kill(signal);
	};

    const timer = setTimeout(() => {
      timedOut = true;
	  terminate("SIGTERM");
      setTimeout(() => {
		if (!child.killed) terminate("SIGKILL");
      }, 2_000).unref();
    }, options.timeoutMs);

    child.stdout.on("data", (chunk: Buffer) => {
      stdout = appendOutput(stdout, chunk, maxChars);
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr = appendOutput(stderr, chunk, maxChars);
    });
    child.once("error", (error) => {
      clearTimeout(timer);
      if (!settled) {
        settled = true;
        reject(error);
      }
    });
    child.once("close", (code, signal) => {
      clearTimeout(timer);
      if (!settled) {
        settled = true;
        resolve({ code, signal, stdout, stderr, timedOut });
      }
    });
  });
}

const allowedTestCommands = new Map<string, { file: string; args: string[] }>([
	["git diff --check", { file: "git", args: ["diff", "--check"] }],
	["go test ./...", { file: "go", args: ["test", "./..."] }],
	["npm test", { file: "npm", args: ["test"] }],
	["npm run build", { file: "npm", args: ["run", "build"] }],
	["npm run typecheck", { file: "npm", args: ["run", "typecheck"] }],
	["npm run lint", { file: "npm", args: ["run", "lint"] }],
	["cargo test", { file: "cargo", args: ["test"] }],
	["python -m pytest", { file: "python", args: ["-m", "pytest"] }],
]);

export function allowedTestCommand(command: string): { file: string; args: string[] } {
	const resolved = allowedTestCommands.get(command.trim());
	if (!resolved) {
	  throw new Error(
		"test_command no pertenece a la allowlist. Valores permitidos: " +
		  [...allowedTestCommands.keys()].join(", "),
	  );
	}
	return { file: resolved.file, args: [...resolved.args] };
}
