export type WorkerProvider = "qwen" | "opencode";

export interface DelegateTaskInput {
  task: string;
  working_directory: string;
  relevant_files?: string[];
  acceptance_criteria?: string[];
  test_command?: string;
  max_iterations?: number;
  max_changed_files?: number;
  keep_worktree?: boolean;
  base_ref?: string;
  allow_dirty_base?: boolean;
}

export interface CommandResult {
  code: number | null;
  signal: string | null;
  stdout: string;
  stderr: string;
  timedOut: boolean;
}

export interface RunCommandOptions {
  cwd: string;
  env?: NodeJS.ProcessEnv;
  timeoutMs: number;
  maxOutputChars?: number;
}

export type CommandRunner = (
  file: string,
  args: string[],
  options: RunCommandOptions,
) => Promise<CommandResult>;

export interface WorkerConfig {
  provider: WorkerProvider;
  allowedRoots: string[];
  worktreeRoot: string;
  qwenBin: string;
  qwenModel: string;
  qwenApprovalMode: string;
  qwenAuthType: string;
  qwenOpenaiBaseUrl: string;
  qwenOpenaiApiKey: string;
  opencodeBin: string;
  opencodeModel: string;
  opencodeAgent: string;
  maxConcurrent: number;
  timeoutMs: number;
  testTimeoutMs: number;
  allowTestCommands: boolean;
  requireCleanBase: boolean;
  maxOutputChars: number;
  defaultMaxIterations: number;
  maxIterations: number;
  maxChangedFiles: number;
  maxRelevantFiles: number;
}

export interface ProviderRunResult extends CommandResult {
  command: string;
  args: string[];
  summary: string;
}

export interface TestResult {
  command: string;
  code: number | null;
  signal: string | null;
  passed: boolean;
  timed_out: boolean;
  output: string;
}

export interface DelegateTaskResult {
  status: "success" | "failed";
  task_id: string;
  provider: WorkerProvider;
  summary: string;
  files_changed: string[];
  commit: string | null;
  branch: string;
  base_ref: string;
  worktree_path: string;
  test: TestResult | null;
  git_diff_stat: string;
  warnings: string[];
  cleanup_performed: boolean;
}

export interface QueueSnapshotItem {
  task_id: string;
  repository: string;
  state: "queued" | "running";
  position: number;
  waiting_ms: number;
}
