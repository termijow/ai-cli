import { describe, expect, it } from "vitest";
import { loadConfig } from "./config.js";

describe("loadConfig", () => {
  it("uses Qwen Code and safe defaults", () => {
    const config = loadConfig({
      LOCAL_WORKER_ALLOWED_ROOTS: "/tmp/projects",
    });
    expect(config.provider).toBe("qwen");
    expect(config.qwenModel).toBe("localmodel");
    expect(config.allowTestCommands).toBe(false);
    expect(config.requireCleanBase).toBe(true);
    expect(config.defaultMaxIterations).toBe(6);
    expect(config.maxIterations).toBe(12);
    expect(config.maxChangedFiles).toBe(2);
    expect(config.maxRelevantFiles).toBe(5);
  });

  it("normalizes the full AI chat-completions URL for Qwen Code", () => {
    const config = loadConfig({
      AI_API_URL: "http://localhost:1234/v1/chat/completions",
      LOCAL_WORKER_ALLOWED_ROOTS: "/tmp/projects",
    });
    expect(config.qwenOpenaiBaseUrl).toBe("http://localhost:1234/v1");
  });

  it("allows selecting OpenCode through the environment", () => {
    const config = loadConfig({
      LOCAL_WORKER_PROVIDER: "opencode",
      LOCAL_WORKER_ALLOWED_ROOTS: "/tmp/projects",
      LOCAL_WORKER_ALLOW_TEST_COMMANDS: "1",
    });
    expect(config.provider).toBe("opencode");
    expect(config.allowTestCommands).toBe(true);
  });

	it("requires an explicit key for a non-local Qwen endpoint", () => {
	  expect(() => loadConfig({
		LOCAL_WORKER_QWEN_OPENAI_BASE_URL: "https://provider.example/v1",
		LOCAL_WORKER_ALLOWED_ROOTS: "/tmp/projects",
	  })).toThrow(/API_KEY/);
	});
});
