import type {
  CommandRunner,
  ProviderRunResult,
  RunCommandOptions,
  WorkerConfig,
} from "./types.js";

const SUMMARY_LIMIT = 8_000;

function compact(text: string): string {
  const normalized = text.trim();
  if (normalized.length <= SUMMARY_LIMIT) return normalized;
  return normalized.slice(-SUMMARY_LIMIT) + "\n...[summary truncated]";
}

function textFromUnknown(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map(textFromUnknown).filter(Boolean).join("\n");
  }
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    for (const key of ["text", "content", "result", "summary", "message"]) {
      const text = textFromUnknown(record[key]);
      if (text) return text;
    }
  }
  return "";
}

export function extractProviderSummary(stdout: string, stderr: string): string {
  const lines = stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);

  for (let index = lines.length - 1; index >= 0; index -= 1) {
    try {
      const parsed: unknown = JSON.parse(lines[index]);
      const text = textFromUnknown(parsed);
      if (text) return compact(text);
    } catch {
      // Some provider versions emit a mixture of JSON and human-readable lines.
    }
  }

  return compact(stdout || stderr || "El proveedor terminó sin resumen.");
}

export function buildWorkerPrompt(
  task: string,
  worktreePath: string,
  relevantFiles: string[],
  acceptanceCriteria: string[],
  testCommand: string | undefined,
  maxIterations: number,
  maxChangedFiles: number,
): string {
  const files = relevantFiles.length
    ? relevantFiles.map((file) => "- " + file).join("\n")
    : "- No se especificaron archivos: inspeccioná primero y elegí como máximo los archivos mínimos necesarios; no edites hasta delimitar el alcance.";
  const criteria = acceptanceCriteria.length
    ? acceptanceCriteria.map((criterion) => "- " + criterion).join("\n")
    : "- Implementá la tarea y verificá que no rompa el comportamiento existente.";
  const test = testCommand ?? "No hay comando de prueba proporcionado.";

  return [
    "Sos un worker local de código. Esta es una sesión nueva y aislada.",
    "Trabajá exclusivamente dentro de este worktree: " + worktreePath,
    "No uses ni modifiques rutas fuera del worktree.",
    "",
    "OBJETIVO",
    task,
    "",
    "ARCHIVOS RELEVANTES",
    files,
    "",
    "CRITERIOS DE ACEPTACIÓN",
    criteria,
    "",
    "VALIDACIÓN SOLICITADA",
    test,
    "",
    "REGLAS",
    "- Inspeccioná el código antes de editarlo.",
    "- Trabajá archivo por archivo: inspeccioná, editá y validá un archivo antes de pasar al siguiente.",
    `- No modifiques más de ${maxChangedFiles} archivo(s) en esta sesión.`,
    "- Mantené el cambio acotado a la tarea y no edites archivos fuera de ARCHIVOS RELEVANTES.",
    "- Antes de finalizar, asegurate SIEMPRE de verificar que el código generado no tenga errores de sintaxis y que funcione correctamente.",
    "- Si la tarea requiere más archivos o crece de tamaño, detenete y reportá una siguiente subtarea.",
    "- Ejecutá las pruebas disponibles cuando sea seguro hacerlo.",
    "- No hagas commits ni push; dejá los cambios en el working tree para que el orquestador (Antigravity) valide el alcance.",
    "- No cambies credenciales y no borres datos.",
    "- Trabajá en un máximo de " + String(maxIterations) + " turnos de herramientas.",
    "- Antes de terminar, dejá todos los cambios listos y describí qué hiciste y qué falta.",
  ].join("\n");
}

export function providerInvocation(
  provider: WorkerConfig["provider"],
  config: WorkerConfig,
  prompt: string,
  maxIterations: number,
): { file: string; args: string[] } {
  if (provider === "qwen") {
    return {
      file: config.qwenBin,
      args: [
        "--bare",
        "--model",
        config.qwenModel,
        "--approval-mode",
        config.qwenApprovalMode,
        "--auth-type",
        config.qwenAuthType,
		"--openai-base-url",
		config.qwenOpenaiBaseUrl,
		"--output-format",
        "json",
        "--max-session-turns",
        String(maxIterations),
        "--max-tool-calls",
        String(maxIterations * 8),
        prompt,
      ],
    };
  }

  return {
    file: config.opencodeBin,
    args: [
      "run",
      "--model",
      config.opencodeModel,
      "--agent",
      config.opencodeAgent,
      "--format",
      "json",
      "--auto",
      prompt,
    ],
  };
}

function providerEnvironment(
	provider: WorkerConfig["provider"],
	config: WorkerConfig,
): NodeJS.ProcessEnv {
	const environment: NodeJS.ProcessEnv = {};
	for (const key of [
	  "PATH", "HOME", "USER", "USERPROFILE", "TMPDIR", "TEMP", "TMP",
	  "SystemRoot", "ComSpec", "LANG",
	]) {
	  if (process.env[key]) environment[key] = process.env[key];
	}
	if (provider === "qwen") {
	  // Environment variables do not appear in process listings, unlike the
	  // previous --openai-api-key command-line argument.
	  environment.OPENAI_API_KEY = config.qwenOpenaiApiKey;
	  environment.QWEN_OPENAI_API_KEY = config.qwenOpenaiApiKey;
	}
	return environment;
}

export async function runProvider(
  provider: WorkerConfig["provider"],
  config: WorkerConfig,
  prompt: string,
  maxIterations: number,
  cwd: string,
  runner: CommandRunner,
): Promise<ProviderRunResult> {
  const invocation = providerInvocation(provider, config, prompt, maxIterations);
  const options: RunCommandOptions = {
	cwd,
	timeoutMs: config.timeoutMs,
	maxOutputChars: config.maxOutputChars,
	env: providerEnvironment(provider, config),
  };
  const result = await runner(invocation.file, invocation.args, options);
  return {
    ...result,
    command: invocation.file,
    args: invocation.args,
    summary: extractProviderSummary(result.stdout, result.stderr),
  };
}
