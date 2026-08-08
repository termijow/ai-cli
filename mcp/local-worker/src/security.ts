import fs from "node:fs/promises";
import path from "node:path";

export function isWithin(parent: string, candidate: string): boolean {
  const relative = path.relative(parent, candidate);
  return relative === "" ||
    (relative !== ".." &&
      !relative.startsWith(".." + path.sep) &&
      !path.isAbsolute(relative));
}

export async function existingRealPath(input: string): Promise<string> {
  return fs.realpath(input);
}

export async function assertAllowedDirectory(
  directory: string,
  allowedRoots: string[],
): Promise<string> {
  const resolvedDirectory = await existingRealPath(directory);
  const resolvedRoots = await Promise.all(
    allowedRoots.map(async (root) => {
      try {
        return await existingRealPath(root);
      } catch {
        return path.resolve(root);
      }
    }),
  );

  if (!resolvedRoots.some((root) => isWithin(root, resolvedDirectory))) {
    throw new Error(
      "working_directory está fuera de LOCAL_WORKER_ALLOWED_ROOTS: " + resolvedDirectory,
    );
  }
  return resolvedDirectory;
}

export function assertRelativeFile(file: string): void {
  if (
    path.isAbsolute(file) ||
    file === ".." ||
    file.startsWith(".." + path.sep) ||
    file.includes("\0")
  ) {
    throw new Error("relevant_files contiene una ruta insegura: " + file);
  }
}
