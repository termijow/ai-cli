import { describe, expect, it } from "vitest";
import { assertRelativeFile, isWithin } from "./security.js";

describe("isWithin", () => {
  it("accepts a directory and its descendants", () => {
    expect(isWithin("/tmp/project", "/tmp/project")).toBe(true);
    expect(isWithin("/tmp/project", "/tmp/project/src/file.ts")).toBe(true);
  });

  it("rejects sibling and parent traversal paths", () => {
    expect(isWithin("/tmp/project", "/tmp/project-old")).toBe(false);
    expect(isWithin("/tmp/project", "/tmp/project/../secrets")).toBe(false);
  });
});

describe("assertRelativeFile", () => {
  it("rejects absolute paths and traversal", () => {
    expect(() => assertRelativeFile("/etc/passwd")).toThrow();
    expect(() => assertRelativeFile("../secrets")).toThrow();
  });

  it("accepts repository-relative files", () => {
    expect(() => assertRelativeFile("src/lib/validation.ts")).not.toThrow();
  });
});
