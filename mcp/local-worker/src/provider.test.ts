import { describe, expect, it } from "vitest";
import { buildWorkerPrompt, providerInvocation } from "./provider.js";
import type { WorkerConfig } from "./types.js";

const config: WorkerConfig = {
  provider: "qwen",
  allowedRoots: ["/tmp"],
  worktreeRoot: "/tmp/worktrees",
  qwenBin: "qwen",
  qwenModel: "localmodel",
  qwenApprovalMode: "auto",
  qwenAuthType: "openai",
  qwenOpenaiBaseUrl: "http://localhost:1234/v1",
  qwenOpenaiApiKey: "local",
  opencodeBin: "opencode",
  opencodeModel: "ollama/qwen3.5:9b",
  opencodeAgent: "local-worker",
  maxConcurrent: 1,
  timeoutMs: 1_000,
  testTimeoutMs: 1_000,
  allowTestCommands: true,
  requireCleanBase: true,
  maxOutputChars: 10_000,
  defaultMaxIterations: 6,
  maxIterations: 12,
  maxChangedFiles: 2,
  maxRelevantFiles: 5,
};

describe("providerInvocation", () => {
  it("starts a fresh Qwen Code session without resume flags", () => {
    const invocation = providerInvocation("qwen", config, "prompt", 12);
    expect(invocation.file).toBe("qwen");
    expect(invocation.args).toContain("--output-format");
    expect(invocation.args).toContain("json");
    expect(invocation.args).toContain("--max-session-turns");
	expect(invocation.args).not.toContain("--openai-api-key");
	expect(invocation.args).not.toContain(config.qwenOpenaiApiKey);
    expect(invocation.args).not.toContain("--continue");
    expect(invocation.args).not.toContain("--resume");
  });

  it("supports OpenCode as a fallback provider", () => {
    const invocation = providerInvocation("opencode", config, "prompt", 12);
    expect(invocation.file).toBe("opencode");
    expect(invocation.args.slice(0, 5)).toEqual([
      "run",
      "--model",
      "ollama/qwen3.5:9b",
      "--agent",
      "local-worker",
    ]);
    expect(invocation.args).toContain("--format");
    expect(invocation.args).toContain("json");
    expect(invocation.args).toContain("--auto");
  });
});

describe("buildWorkerPrompt", () => {
  it("includes the bounded task contract", () => {
    const prompt = buildWorkerPrompt(
      "Implementá el formulario",
      "/tmp/worktree",
      ["src/Form.tsx"],
      ["Los tests pasan"],
    "npm test",
    12,
    2,
  );
    expect(prompt).toContain("Implementá el formulario");
    expect(prompt).toContain("src/Form.tsx");
    expect(prompt).toContain("Los tests pasan");
    expect(prompt).toContain("npm test");
    expect(prompt).toContain("máximo de 12 turnos");
    expect(prompt).toContain("Trabajá archivo por archivo");
    expect(prompt).toContain("más de 2 archivo(s)");
    expect(prompt).toContain("No hagas commits ni push");
    expect(prompt).toContain("/tmp/worktree");
  });
});
