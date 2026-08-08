import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { loadConfig } from "./config.js";
import { createWorker, describeWorkerError } from "./worker.js";

const config = loadConfig();
const worker = createWorker(config);
const server = new McpServer({
  name: "local-worker-mcp",
  version: "0.1.0",
});

const textResult = (value: unknown, isError = false) => ({
  content: [
    {
      type: "text" as const,
      text: JSON.stringify(value, null, 2),
    },
  ],
  isError,
});

server.tool(
  "delegate_local_task",
  [
    "Delegá una tarea pequeña y verificable a una sesión nueva de Qwen. La idea es ahorrar tokens de contexto",
    "usando Qwen 35B para la generación de código. El worker trabaja en un git worktree aislado,",
    "limita el contexto a un MÁXIMO de 5 archivos específicos, realiza las ediciones, verifica errores de sintaxis y devuelve los resultados.",
  ].join(" "),
  {
    task: z.string().min(1).max(12_000),
    working_directory: z.string().min(1),
    relevant_files: z.array(z.string().min(1).max(500)).max(5).optional(),
    acceptance_criteria: z.array(z.string().min(1).max(1_000)).max(30).optional(),
	test_command: z.enum([
	  "git diff --check",
	  "go test ./...",
	  "npm test",
	  "npm run build",
	  "npm run typecheck",
	  "npm run lint",
	  "cargo test",
	  "python -m pytest",
	]).optional(),
    max_iterations: z.number().int().min(1).max(50).optional(),
    max_changed_files: z.number().int().min(1).max(20).optional(),
    keep_worktree: z.boolean().optional(),
    base_ref: z.string().min(1).max(200).optional(),
    allow_dirty_base: z.boolean().optional(),
  },
  async (input) => {
    try {
      const taskId = worker.startDelegate(input);
      return textResult({
        status: "queued",
        task_id: taskId,
        message: "La tarea se ha encolado correctamente. Usa check_local_task con este task_id para consultar el estado."
      });
    } catch (error) {
      return textResult(
        {
          status: "failed",
          error: describeWorkerError(error),
        },
        true,
      );
    }
  },
);

server.tool(
  "check_local_task",
  "Revisa el estado o resultado de una tarea previamente delegada usando su task_id.",
  {
    task_id: z.string().min(1),
  },
  async ({ task_id }) => {
    const result = worker.getTaskResult(task_id);
    return textResult(result, result.status === "failed" || result.status === "not_found");
  },
);

server.tool(
  "inspect_local_queue",
  "Muestra las tareas Qwen/OpenCode activas y en cola. Las tareas del mismo repositorio se ejecutan en orden y nunca en paralelo.",
  {},
  async () => textResult(worker.queueSnapshot()),
);

const transport = new StdioServerTransport();
await server.connect(transport);
