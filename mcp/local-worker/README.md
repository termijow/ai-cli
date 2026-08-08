# Local Worker MCP

Servidor MCP local para delegar subtareas de código a una sesión nueva de Qwen Code. Cada tarea se ejecuta en un git worktree separado, se valida fuera del agente y devuelve un resultado JSON corto para que la IA grande decida si aplica el commit.

OpenCode también está soportado como fallback mediante LOCAL_WORKER_PROVIDER=opencode.

## Qué hace

delegate_local_task recibe:

- task: objetivo concreto.
- working_directory: repositorio donde trabajar.
- relevant_files: archivos que conviene inspeccionar.
- acceptance_criteria: condiciones comprobables.
- test_command: validación externa elegida de una allowlist cerrada.
- max_iterations: límite de turnos del worker.
- max_changed_files: máximo de archivos que puede modificar esta subtarea.
- keep_worktree: conserva el worktree para inspección; por defecto sí.
- base_ref: referencia base; por defecto HEAD.

El flujo es:

1. Verifica que el repositorio esté dentro de LOCAL_WORKER_ALLOWED_ROOTS.
2. Rechaza un repositorio base sucio por defecto para no mezclar cambios existentes.
3. Crea una rama agent/local-worker/<task-id> y un worktree temporal.
4. Inicia una ejecución nueva de Qwen Code, sin --continue ni --resume.
5. Ejecuta test_command sin shell y únicamente si coincide con la allowlist integrada.
6. Rechaza cualquier cambio que exceda el número de archivos permitido o salga de relevant_files.
7. Crea un commit aislado, calcula archivos y diff.
8. Devuelve resumen, resultado de tests, commit y ruta del worktree.

## Subtareas pequeñas y cola

El contrato está diseñado para que la IA grande divida el trabajo antes de delegarlo:

- Por defecto Qwen recibe hasta 6 turnos, puede modificar como máximo 2 archivos y se aceptan hasta 5 archivos relevantes.
- Dentro de la sesión se le pide inspeccionar, editar y validar un archivo antes de pasar al siguiente.
- Si necesita más archivos, debe detenerse y reportar la siguiente subtarea.
- Una tarea que intenta superar los límites no obtiene commit.
- Las tareas del mismo repositorio se ejecutan una detrás de otra; repositorios distintos pueden usar los cupos disponibles de `LOCAL_WORKER_MAX_CONCURRENT`.

La herramienta `inspect_local_queue` muestra las tareas activas y pendientes. Para un cambio grande, usá varias llamadas a `delegate_local_task`, una por archivo o por pequeño grupo de archivos, y aplicá cada commit únicamente después de revisar su resultado.

El worker no hace push, no toca el repositorio base y no puede usar rutas fuera del allowlist. Las claves del proveedor se pasan por entorno y se eliminan del entorno de los tests. Aun así, ejecuta un agente con permisos para editar y ejecutar comandos: configurá este MCP únicamente como servidor local de confianza y, para clientes no confiables, dentro de un contenedor sin red y con el filesystem mínimo.

Los únicos valores admitidos para `test_command` son: `git diff --check`, `go test ./...`, `npm test`, `npm run build`, `npm run typecheck`, `npm run lint`, `cargo test` y `python -m pytest`. No se aceptan pipes, redirecciones, variables ni concatenación de comandos.

## Instalación

~~~bash
cd /home/tu-usuario/proyectos/local-worker-mcp
npm install
npm run build
~~~

Copiá .env.example a .env o configurá las variables en el proceso que inicia Codex:

~~~bash
export LOCAL_WORKER_PROVIDER=qwen
export LOCAL_WORKER_ALLOWED_ROOTS=/home/tu-usuario/proyectos
export LOCAL_WORKER_ALLOW_TEST_COMMANDS=1
export LOCAL_WORKER_DEFAULT_MAX_ITERATIONS=6
export LOCAL_WORKER_MAX_CHANGED_FILES=2
export LOCAL_WORKER_MAX_RELEVANT_FILES=5
~~~

Qwen Code es el proveedor predeterminado:

~~~bash
qwen --version
~~~

Para usar OpenCode:

~~~bash
LOCAL_WORKER_PROVIDER=opencode \
LOCAL_WORKER_ALLOWED_ROOTS=/home/tu-usuario/proyectos \
npm start
~~~

## Configuración en Codex

En ~/.codex/config.toml o en la configuración MCP del proyecto:

~~~toml
[mcp_servers.local_qwen_worker]
command = "node"
args = ["/home/tu-usuario/proyectos/local-worker-mcp/dist/index.js"]

[mcp_servers.local_qwen_worker.env]
LOCAL_WORKER_PROVIDER = "qwen"
LOCAL_WORKER_ALLOWED_ROOTS = "/home/tu-usuario/proyectos"
LOCAL_WORKER_ALLOW_TEST_COMMANDS = "1"
LOCAL_WORKER_WORKTREE_ROOT = "/tmp/local-worker-worktrees"
~~~

No es necesario registrar el MCP dentro del propio Qwen Code para este flujo. Codex llama al servidor por STDIO; el servidor llama a Qwen Code en una sesión nueva.

## Ejemplo de llamada

~~~json
{
  "task": "Agregar un test para el caso de código de barras inexistente.",
  "working_directory": "/home/tu-usuario/proyectos/mi-app",
  "relevant_files": [
    "src/catalog/repository_test.go"
  ],
  "acceptance_criteria": [
    "El test cubre el caso inexistente.",
    "No cambiar el comportamiento de los casos existentes."
  ],
  "test_command": "go test ./...",
  "max_iterations": 6,
  "max_changed_files": 1,
  "keep_worktree": true
}
~~~

Resultado resumido:

~~~json
{
  "status": "success",
  "commit": "abc123...",
  "files_changed": ["src/lib/validation.ts"],
  "test": {"passed": true},
  "worktree_path": "/tmp/local-worker-worktrees/task-..."
}
~~~

Después, la IA grande puede revisar el diff y aplicar el commit:

~~~bash
git cherry-pick abc123...
~~~

## Comandos de desarrollo

~~~bash
npm test
npm run build
npm start
~~~

No se incluye una integración que haga cherry-pick automáticamente: esa decisión debe seguir siendo de la IA grande o del usuario.

## Recomendación para el orquestador

Una tarea adecuada es concreta, por ejemplo: “agregar un test para el caso de código de barras inexistente en `src/catalog/repository_test.go`”. Una tarea como “revisar y arreglar todo el módulo de licencias” debe dividirse en varias llamadas: primero inspección, luego un archivo por tarea, después tests y finalmente una revisión.
