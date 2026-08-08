import crypto from "node:crypto";
import type {
  CommandRunner,
  DelegateTaskInput,
  DelegateTaskResult,
  TestResult,
  WorkerConfig,
  QueueSnapshotItem,
} from "./types.js";
import { allowedTestCommand, runCommand } from "./command.js";
import { GitClient } from "./git.js";
import { buildWorkerPrompt, runProvider } from "./provider.js";
import { assertAllowedDirectory, assertRelativeFile } from "./security.js";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function outputOf(stdout: string, stderr: string): string {
  const output = (stdout + (stderr ? "\n" + stderr : "")).trim();
  if (output.length <= 8_000) return output;
  return output.slice(-8_000) + "\n...[test output truncated]";
}

export class TaskQueue {
  private active = 0;
  private readonly waiters: Array<{
    taskId: string;
    repository: string;
    queuedAt: number;
    resolve: (release: () => void) => void;
  }> = [];
  private readonly activeTasks = new Map<string, { taskId: string; repository: string; startedAt: number }>();
  private readonly activeRepositories = new Set<string>();

  constructor(private readonly limit: number) {}

  async acquire(taskId: string, repository: string): Promise<() => void> {
    return new Promise((resolve) => {
      const waiter = { taskId, repository, queuedAt: Date.now(), resolve };
      if (this.canStart(repository)) {
        this.start(waiter);
      } else {
        this.waiters.push(waiter);
      }
    });
  }

  snapshot(): QueueSnapshotItem[] {
    const now = Date.now();
    const running = [...this.activeTasks.values()].map((task, index) => ({
      task_id: task.taskId,
      repository: task.repository,
      state: "running" as const,
      position: index + 1,
      waiting_ms: Math.max(0, now - task.startedAt),
    }));
    const queued = this.waiters.map((task, index) => ({
      task_id: task.taskId,
      repository: task.repository,
      state: "queued" as const,
      position: running.length + index + 1,
      waiting_ms: Math.max(0, now - task.queuedAt),
    }));
    return [...running, ...queued];
  }

  private canStart(repository: string): boolean {
    return this.active < this.limit && !this.activeRepositories.has(repository);
  }

  private start(waiter: (typeof this.waiters)[number]): void {
    this.active += 1;
    this.activeRepositories.add(waiter.repository);
    this.activeTasks.set(waiter.taskId, {
      taskId: waiter.taskId,
      repository: waiter.repository,
      startedAt: Date.now(),
    });
    let released = false;
    waiter.resolve(() => {
      if (released) return;
      released = true;
      this.active -= 1;
      this.activeRepositories.delete(waiter.repository);
      this.activeTasks.delete(waiter.taskId);
      this.pump();
    });
  }

  private pump(): void {
    while (this.active < this.limit) {
      const index = this.waiters.findIndex((waiter) => !this.activeRepositories.has(waiter.repository));
      if (index < 0) return;
      const [next] = this.waiters.splice(index, 1);
      this.start(next);
    }
  }
}

/*
 * Keep this method separate from TaskQueue's state transitions so a future
 * queue inspection endpoint cannot accidentally release another task.
 */
function releaseQueueSlot(release: (() => void) | undefined): void {
  if (release) release();
}

export class LocalWorker {
  private readonly git: GitClient;
  private readonly queue: TaskQueue;
  private readonly taskResults = new Map<string, any>();

  constructor(
    private readonly config: WorkerConfig,
    private readonly runner: CommandRunner = runCommand,
  ) {
    this.git = new GitClient(this.runner, this.config.timeoutMs);
    this.queue = new TaskQueue(this.config.maxConcurrent);
  }

  getTaskResult(taskId: string): any {
    if (!this.taskResults.has(taskId)) {
      return { status: "not_found", error: "El ID de la tarea no existe." };
    }
    return this.taskResults.get(taskId);
  }

  startDelegate(input: DelegateTaskInput): string {
    const taskId = "task-" + crypto.randomBytes(6).toString("hex");
    this.taskResults.set(taskId, { status: "running" });

    // Iniciar tarea en segundo plano
    this.delegate(input, taskId)
      .then((result) => {
        this.taskResults.set(taskId, result);
      })
      .catch((error) => {
        this.taskResults.set(taskId, { status: "failed", error: describeWorkerError(error) });
      });

    return taskId;
  }

  queueSnapshot(): QueueSnapshotItem[] {
    return this.queue.snapshot();
  }

  async delegate(input: DelegateTaskInput, preassignedTaskId?: string): Promise<DelegateTaskResult> {
    const taskId = preassignedTaskId ?? "task-" + crypto.randomBytes(6).toString("hex");
    const baseRef = input.base_ref ?? "HEAD";
    const relevantFiles = input.relevant_files ?? [];
    const acceptanceCriteria = input.acceptance_criteria ?? [];
    let worktreePath = "";
    let branch = "agent/local-worker/" + taskId;
    let release: (() => void) | undefined;

    try {
      if (input.test_command && !this.config.allowTestCommands) {
        throw new Error(
          "test_command está deshabilitado. Configurá LOCAL_WORKER_ALLOW_TEST_COMMANDS=1.",
        );
      }
      if (input.test_command && input.test_command.length > 2_000) {
        throw new Error("test_command supera el límite de 2.000 caracteres.");
      }
      for (const file of relevantFiles) assertRelativeFile(file);

      const requestedDirectory = await assertAllowedDirectory(
        input.working_directory,
        this.config.allowedRoots,
      );
      const repoRoot = await this.git.repoRoot(requestedDirectory);
      await assertAllowedDirectory(repoRoot, this.config.allowedRoots);

      if (input.task.length > 6_000) {
        throw new Error("task supera el límite de 6.000 caracteres; dividilo en subtareas.");
      }
      if (relevantFiles.length > this.config.maxRelevantFiles) {
        throw new Error(
          `relevant_files supera el límite de ${this.config.maxRelevantFiles}; dividí la tarea por archivos.`,
        );
      }
      if (input.max_changed_files && input.max_changed_files > this.config.maxChangedFiles) {
        throw new Error(
          `max_changed_files no puede superar ${this.config.maxChangedFiles}.`,
        );
      }

      release = await this.queue.acquire(taskId, repoRoot);

      const baseSha = await this.git.resolveRef(repoRoot, baseRef);
      if (this.config.requireCleanBase && !input.allow_dirty_base) {
        const status = await this.git.status(repoRoot);
        if (status) {
          throw new Error(
            "El repositorio base tiene cambios sin commit. Confirmá allow_dirty_base=true solo si querés trabajar desde HEAD sin incluir esos cambios.",
          );
        }
      }

      const worktree = await this.git.createWorktree(
        repoRoot,
        this.config.worktreeRoot,
        taskId,
        baseRef,
      );
      worktreePath = worktree.path;
      branch = worktree.branch;

      const maxIterations = input.max_iterations ?? this.config.defaultMaxIterations;
      if (maxIterations > this.config.maxIterations) {
        throw new Error(
          `max_iterations no puede superar ${this.config.maxIterations}; dividí la tarea.`,
        );
      }
      const maxChangedFiles = input.max_changed_files ?? this.config.maxChangedFiles;
      const prompt = buildWorkerPrompt(
        input.task,
        worktreePath,
        relevantFiles,
        acceptanceCriteria,
        input.test_command,
        maxIterations,
        maxChangedFiles,
      );
      const providerResult = await runProvider(
        this.config.provider,
        this.config,
        prompt,
        maxIterations,
        worktreePath,
        this.runner,
      );

      const allowedFiles = new Set(relevantFiles.map((file) => file.replaceAll("\\", "/")));
      const validateScope = async (): Promise<void> => {
        const changedFiles = await this.git.workingTreeFiles(worktreePath, baseSha);
        const unlistedFiles = relevantFiles.length
          ? changedFiles.filter((file) => !allowedFiles.has(file))
          : [];
        if (changedFiles.length > maxChangedFiles || unlistedFiles.length > 0) {
          const details = [
            `archivos modificados: ${changedFiles.length}/${maxChangedFiles}`,
            unlistedFiles.length ? `fuera de alcance: ${unlistedFiles.join(", ")}` : "",
          ].filter(Boolean).join("; ");
          throw new Error(
            `La tarea excedió su alcance (${details}). El worker no hará commit; dividí la tarea en subtareas por archivo. Worktree: ${worktreePath}`,
          );
        }
      };

      await validateScope();

      const test = input.test_command
        ? await this.runTest(input.test_command, worktreePath)
        : null;
      // Tests can generate snapshots, coverage or other files; enforce scope again
      // immediately before staging so those artifacts can never enter the commit.
      await validateScope();
      const commit = await this.git.ensureCommit(
        worktreePath,
        baseSha,
        "agent: complete " + taskId,
      );
      const filesChanged = commit
        ? await this.git.changedFiles(worktreePath, baseSha)
        : [];
      const diffStat = commit
        ? await this.git.diffStat(worktreePath, baseSha)
        : "";
      const warnings: string[] = [];

      if (providerResult.code !== 0 || providerResult.timedOut) {
        warnings.push(
          "El proveedor terminó con código " +
            String(providerResult.code) +
            (providerResult.timedOut ? " por timeout." : "."),
        );
      }
      if (providerResult.stderr.trim()) {
        warnings.push("stderr del proveedor: " + outputOf("", providerResult.stderr));
      }
      if (test && !test.passed) {
        warnings.push("La validación externa falló.");
      }
      if (!commit) warnings.push("El worker no produjo cambios para commit.");

      const success =
        providerResult.code === 0 &&
        !providerResult.timedOut &&
        (!test || test.passed);
      let cleanupPerformed = false;
      if (success && input.keep_worktree === false) {
        await this.git.removeWorktree(repoRoot, worktreePath);
        cleanupPerformed = true;
      }

      return {
        status: success ? "success" : "failed",
        task_id: taskId,
        provider: this.config.provider,
        summary: providerResult.summary,
        files_changed: filesChanged,
        commit,
        branch,
        base_ref: baseRef,
        worktree_path: worktreePath,
        test,
        git_diff_stat: diffStat,
        warnings,
        cleanup_performed: cleanupPerformed,
      };
    } finally {
      releaseQueueSlot(release);
    }
  }

  private async runTest(command: string, cwd: string): Promise<TestResult> {
	const invocation = allowedTestCommand(command);
	const environment = { ...process.env };
	for (const key of Object.keys(environment)) {
	  if (/(?:TOKEN|SECRET|PASSWORD|API_KEY|CREDENTIAL)/i.test(key)) delete environment[key];
	}
	const result = await this.runner(
	  invocation.file,
	  invocation.args,
	  {
		cwd,
		env: environment,
        timeoutMs: this.config.testTimeoutMs,
        maxOutputChars: this.config.maxOutputChars,
      },
    );
    return {
      command,
      code: result.code,
      signal: result.signal,
      passed: result.code === 0 && !result.timedOut,
      timed_out: result.timedOut,
      output: outputOf(result.stdout, result.stderr),
    };
  }
}

export function createWorker(config: WorkerConfig): LocalWorker {
  return new LocalWorker(config);
}

export function describeWorkerError(error: unknown): string {
  return errorMessage(error);
}
