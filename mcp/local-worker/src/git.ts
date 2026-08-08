import fs from "node:fs/promises";
import path from "node:path";
import type { CommandRunner } from "./types.js";

export class GitError extends Error {
  constructor(
    message: string,
    public readonly args: string[],
    public readonly output: string,
  ) {
    super(message);
    this.name = "GitError";
  }
}

export interface WorktreeInfo {
  path: string;
  branch: string;
}

export class GitClient {
  constructor(
    private readonly runner: CommandRunner,
    private readonly timeoutMs: number,
  ) {}

  async run(args: string[], cwd: string): Promise<string> {
    const result = await this.runner("git", args, {
      cwd,
      timeoutMs: this.timeoutMs,
    });
    const output = (result.stdout + result.stderr).trim();
    if (result.code !== 0) {
      throw new GitError(
        "git " + args.join(" ") + " falló con código " + String(result.code),
        args,
        output,
      );
    }
    return result.stdout.trim();
  }

  async repoRoot(directory: string): Promise<string> {
    return this.run(["rev-parse", "--show-toplevel"], directory);
  }

  async status(directory: string): Promise<string> {
    return this.run(["status", "--porcelain", "--untracked-files=all"], directory);
  }

  async resolveRef(directory: string, ref: string): Promise<string> {
    return this.run(["rev-parse", "--verify", ref], directory);
  }

  async createWorktree(
    repoRoot: string,
    worktreeRoot: string,
    taskId: string,
    baseRef: string,
  ): Promise<WorktreeInfo> {
    await fs.mkdir(worktreeRoot, { recursive: true });
    const worktreePath = path.join(worktreeRoot, taskId);
    const branch = "agent/local-worker/" + taskId;
    await fs.mkdir(worktreePath);

    try {
      await this.run(
        ["worktree", "add", "-b", branch, worktreePath, baseRef],
        repoRoot,
      );
      return { path: worktreePath, branch };
    } catch (error) {
      await fs.rm(worktreePath, { recursive: true, force: true });
      throw error;
    }
  }

  async head(directory: string): Promise<string> {
    return this.resolveRef(directory, "HEAD");
  }

  async ensureCommit(
    directory: string,
    baseSha: string,
    message: string,
  ): Promise<string | null> {
    const status = await this.status(directory);
    const currentHead = await this.head(directory);

    if (!status && currentHead === baseSha) return null;

    if (status) {
      await this.run(["add", "--all"], directory);
      await this.run(["commit", "-m", message], directory);
    }
    return this.head(directory);
  }

  async changedFiles(directory: string, baseSha: string): Promise<string[]> {
    const output = await this.run(
      ["diff", "--name-only", baseSha + "..HEAD"],
      directory,
    );
    return output.split(/\r?\n/).map((file) => file.trim()).filter(Boolean);
  }

  async workingTreeFiles(directory: string, baseSha: string): Promise<string[]> {
    const tracked = await this.run(["diff", "--name-only", baseSha, "--"], directory);
    const untracked = await this.run(
      ["ls-files", "--others", "--exclude-standard"],
      directory,
    );
    return [...new Set(
      (tracked + "\n" + untracked)
        .split(/\r?\n/)
        .map((file) => file.trim())
        .filter(Boolean),
    )].sort();
  }

  async workingTreeDiffStat(directory: string, baseSha: string): Promise<string> {
    return this.run(["diff", "--stat", baseSha, "--"], directory);
  }

  async diffStat(directory: string, baseSha: string): Promise<string> {
    return this.run(["diff", "--stat", baseSha + "..HEAD"], directory);
  }

  async removeWorktree(repoRoot: string, worktreePath: string): Promise<void> {
    await this.run(["worktree", "remove", "--force", worktreePath], repoRoot);
  }
}
