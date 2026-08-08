import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { runCommand } from "./command.js";
import { LocalWorker, TaskQueue } from "./worker.js";
import type { CommandRunner, WorkerConfig } from "./types.js";

const temporaryDirectories: string[] = [];

afterEach(async () => {
  await Promise.all(
    temporaryDirectories.splice(0).map((directory) =>
      fs.rm(directory, { recursive: true, force: true }),
    ),
  );
});

describe("LocalWorker", () => {
  it("creates an isolated worktree, commits changes, and runs an external test", async () => {
    const root = await fs.mkdtemp(path.join(os.tmpdir(), "local-worker-test-"));
    temporaryDirectories.push(root);
    const repo = path.join(root, "repo");
    await fs.mkdir(repo);

    const git = async (args: string[]) =>
      runCommand("git", args, { cwd: repo, timeoutMs: 10_000 });
    expect((await git(["init", "-q"])).code).toBe(0);
    expect((await git(["config", "user.name", "Local Worker Test"])).code).toBe(0);
    expect((await git(["config", "user.email", "worker-test@example.invalid"])).code).toBe(0);
    await fs.writeFile(path.join(repo, "README.md"), "base\n");
    expect((await git(["add", "--all"])).code).toBe(0);
    expect((await git(["commit", "-m", "base", "-q"])).code).toBe(0);

    const config: WorkerConfig = {
      provider: "qwen",
      allowedRoots: [root],
      worktreeRoot: path.join(root, "worktrees"),
      qwenBin: "fake-provider",
      qwenModel: "test-model",
      qwenApprovalMode: "auto",
      opencodeBin: "opencode",
      opencodeModel: "test-model",
      opencodeAgent: "local-worker",
      maxConcurrent: 1,
      timeoutMs: 30_000,
      testTimeoutMs: 30_000,
      allowTestCommands: true,
      requireCleanBase: true,
      maxOutputChars: 10_000,
      defaultMaxIterations: 6,
      maxIterations: 12,
      maxChangedFiles: 2,
      maxRelevantFiles: 5,
    };

    const runner: CommandRunner = async (file, args, options) => {
      if (file === "fake-provider") {
        await fs.writeFile(path.join(options.cwd, "worker.txt"), "generated\n");
        return {
          code: 0,
          signal: null,
          stdout: JSON.stringify({ summary: "Cambio implementado." }),
          stderr: "",
          timedOut: false,
        };
      }
      return runCommand(file, args, options);
    };

    const result = await new LocalWorker(config, runner).delegate({
      task: "Crear un archivo de prueba.",
      working_directory: repo,
      acceptance_criteria: ["El archivo existe."],
      test_command: "git diff --check",
      max_iterations: 4,
    });

    expect(result.status).toBe("success");
    expect(result.commit).toMatch(/^[0-9a-f]{40}$/);
    expect(result.files_changed).toEqual(["worker.txt"]);
    expect(result.git_diff_stat).toContain("worker.txt");
    expect(result.test?.passed).toBe(true);
    expect(result.worktree_path).toContain("worktrees");
  });
});

describe("TaskQueue", () => {
  it("serializes tasks from the same repository and exposes their state", async () => {
    const queue = new TaskQueue(2);
    const releaseFirst = await queue.acquire("task-1", "/repo");
    const second = queue.acquire("task-2", "/repo");

    expect(queue.snapshot()).toEqual([
      {
        task_id: "task-1",
        repository: "/repo",
        state: "running",
        position: 1,
        waiting_ms: expect.any(Number),
      },
      {
        task_id: "task-2",
        repository: "/repo",
        state: "queued",
        position: 2,
        waiting_ms: expect.any(Number),
      },
    ]);

    let secondStarted = false;
    const secondRelease = second.then((release) => {
      secondStarted = true;
      return release;
    });

    await Promise.resolve();
    expect(secondStarted).toBe(false);
    releaseFirst();
    const releaseSecond = await secondRelease;
    expect(secondStarted).toBe(true);
    releaseSecond();
    expect(queue.snapshot()).toEqual([]);
  });

  it("uses available slots for different repositories", async () => {
    const queue = new TaskQueue(2);
    const releaseFirst = await queue.acquire("task-1", "/repo-a");
    const releaseSecond = await queue.acquire("task-2", "/repo-b");

    expect(queue.snapshot().map((item) => item.task_id)).toEqual(["task-1", "task-2"]);
    releaseFirst();
    releaseSecond();
  });
});
