import os from "node:os";
import path from "node:path";
import type { WorkerConfig, WorkerProvider } from "./types.js";

function positiveInt(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function booleanEnv(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) return fallback;
  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

function providerEnv(value: string | undefined): WorkerProvider {
  if (value === "qwen" || value === "opencode") return value;
  return "qwen";
}

function openaiBaseUrl(env: NodeJS.ProcessEnv): string {
  const configured = env.LOCAL_WORKER_QWEN_OPENAI_BASE_URL ?? env.AI_API_URL;
  const value = configured?.trim() || "http://localhost:1234/v1";
  return value.replace(/\/chat\/completions\/?$/, "");
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): WorkerConfig {
  const configuredRoots = env.LOCAL_WORKER_ALLOWED_ROOTS
    ?.split(path.delimiter)
    .map((root) => root.trim())
    .filter(Boolean);
	const baseURL = openaiBaseUrl(env);
	const apiKey = env.LOCAL_WORKER_QWEN_OPENAI_API_KEY ?? "local";

  return {
    provider: providerEnv(env.LOCAL_WORKER_PROVIDER),
    allowedRoots: configuredRoots?.length ? configuredRoots : [process.cwd()],
    worktreeRoot: path.resolve(
      env.LOCAL_WORKER_WORKTREE_ROOT ?? path.join(os.tmpdir(), "local-worker-worktrees"),
    ),
    qwenBin: env.LOCAL_WORKER_QWEN_BIN ?? "qwen",
    qwenModel: env.LOCAL_WORKER_QWEN_MODEL ?? "localmodel",
    qwenApprovalMode: env.LOCAL_WORKER_QWEN_APPROVAL_MODE ?? "auto",
    qwenAuthType: env.LOCAL_WORKER_QWEN_AUTH_TYPE ?? "openai",
	qwenOpenaiBaseUrl: baseURL,
	qwenOpenaiApiKey: apiKey,
    opencodeBin: env.LOCAL_WORKER_OPENCODE_BIN ?? "opencode",
    opencodeModel: env.LOCAL_WORKER_OPENCODE_MODEL ?? "ollama/qwen3.5:9b",
    opencodeAgent: env.LOCAL_WORKER_OPENCODE_AGENT ?? "local-worker",
    maxConcurrent: positiveInt(env.LOCAL_WORKER_MAX_CONCURRENT, 1),
    timeoutMs: positiveInt(env.LOCAL_WORKER_TIMEOUT_MS, 30 * 60 * 1000),
    testTimeoutMs: positiveInt(env.LOCAL_WORKER_TEST_TIMEOUT_MS, 10 * 60 * 1000),
    allowTestCommands: booleanEnv(env.LOCAL_WORKER_ALLOW_TEST_COMMANDS, false),
    requireCleanBase: booleanEnv(env.LOCAL_WORKER_REQUIRE_CLEAN_BASE, true),
    maxOutputChars: positiveInt(env.LOCAL_WORKER_MAX_OUTPUT_CHARS, 24_000),
    defaultMaxIterations: positiveInt(env.LOCAL_WORKER_DEFAULT_MAX_ITERATIONS, 6),
    maxIterations: positiveInt(env.LOCAL_WORKER_MAX_ITERATIONS, 12),
    maxChangedFiles: positiveInt(env.LOCAL_WORKER_MAX_CHANGED_FILES, 2),
    maxRelevantFiles: positiveInt(env.LOCAL_WORKER_MAX_RELEVANT_FILES, 5),
  };
}
