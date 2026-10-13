import { describe, expect, it } from "vitest";
import {
  checkCssPointerEvents,
  extractHtmlScripts,
  verifyHtmlRuntime,
} from "./verifier.js";

describe("verifier", () => {
  it("extracts script tags excluding external src scripts", () => {
    const html = `
      <html>
        <head>
          <script src="external.js"></script>
        </head>
        <body>
          <script>console.log("hello");</script>
          <script type="module">const x = 42;</script>
        </body>
      </html>
    `;
    const scripts = extractHtmlScripts(html);
    expect(scripts).toContain('console.log("hello");');
    expect(scripts).toContain("const x = 42;");
    expect(scripts).not.toContain("external.js");
  });

  it("detects unclickable overlays caused by pointer-events: none", () => {
    const brokenHtml = `
      <style>
        #overlay { pointer-events: none; }
      </style>
      <div id="overlay"><button id="start">Start</button></div>
    `;
    const fixedHtml = `
      <style>
        #overlay { pointer-events: none; }
        #overlay button { pointer-events: auto; }
      </style>
      <div id="overlay"><button id="start">Start</button></div>
    `;

    expect(checkCssPointerEvents(brokenHtml).length).toBeGreaterThan(0);
    expect(checkCssPointerEvents(fixedHtml).length).toBe(0);
  });

  it("catches runtime scoping errors like Qwen 9B's undefined buttons", async () => {
    const htmlWithScopingBug = `
      <html>
        <body>
          <script>
            (function() {
              const buttons = [1, 2, 3];
            })();
            // buttons is out of scope here!
            buttons.forEach(b => console.log(b));
          </script>
        </body>
      </html>
    `;

    const result = await verifyHtmlRuntime(htmlWithScopingBug);
    expect(result.passed).toBe(false);
    expect(result.error).toMatch(/ReferenceError/);
  });

  it("passes clean scripts that use browser APIs in simulated DOM", async () => {
    const cleanHtml = `
      <html>
        <body>
          <script>
            const canvas = document.getElementById("canvas");
            const ctx = canvas.getContext("2d");
            localStorage.setItem("score", "100");
            window.addEventListener("resize", () => {});
            const audioCtx = new AudioContext();
            audioCtx.resume();
          </script>
        </body>
      </html>
    `;

    const result = await verifyHtmlRuntime(cleanHtml);
    expect(result.passed).toBe(true);
    expect(result.error).toBeUndefined();
  });
});
