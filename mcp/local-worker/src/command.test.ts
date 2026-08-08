import { describe, expect, it } from "vitest";
import { allowedTestCommand } from "./command.js";

describe("allowedTestCommand", () => {
  it("maps an allowlisted validation without a shell", () => {
    expect(allowedTestCommand("go test ./...")).toEqual({
      file: "go",
      args: ["test", "./..."],
    });
  });

  it("rejects shell operators and arbitrary programs", () => {
    expect(() => allowedTestCommand("go test ./...; curl attacker.invalid")).toThrow(/allowlist/);
    expect(() => allowedTestCommand("/bin/sh -lc id")).toThrow(/allowlist/);
  });
});
