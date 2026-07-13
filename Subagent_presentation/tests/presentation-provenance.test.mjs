import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";


const subagentRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const checker = path.join(subagentRoot, "scripts", "check-source.mjs");
const fixture = path.join(subagentRoot, "examples", "example_research", "example_presentation");


function copyFixture() {
  const temporaryRoot = fs.mkdtempSync(path.join(os.tmpdir(), "presentation-provenance-"));
  const caseRoot = path.join(temporaryRoot, "example_research", "example_presentation");
  fs.mkdirSync(path.dirname(caseRoot), { recursive: true });
  fs.cpSync(fixture, caseRoot, { recursive: true });
  return { caseRoot, temporaryRoot };
}


function runCheck(caseRoot) {
  return spawnSync(process.execPath, [checker, "--case", caseRoot], { encoding: "utf8" });
}


test("registered frame provenance passes", (context) => {
  const { caseRoot, temporaryRoot } = copyFixture();
  context.after(() => fs.rmSync(temporaryRoot, { recursive: true, force: true }));
  const result = runCheck(caseRoot);
  assert.equal(result.status, 0, result.stdout + result.stderr);
});


test("slide without source refs fails", (context) => {
  const { caseRoot, temporaryRoot } = copyFixture();
  context.after(() => fs.rmSync(temporaryRoot, { recursive: true, force: true }));
  const manifestPath = path.join(caseRoot, "manifests", "presentation_manifest.json");
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  manifest.slides[0].source_refs = [];
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  const result = runCheck(caseRoot);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout, /has no source_refs/);
});


test("unregistered frame label fails", (context) => {
  const { caseRoot, temporaryRoot } = copyFixture();
  context.after(() => fs.rmSync(temporaryRoot, { recursive: true, force: true }));
  const sourcePath = path.join(caseRoot, "source", "main.tex");
  const source = fs.readFileSync(sourcePath, "utf8").replace("slide:workflow", "slide:unknown");
  fs.writeFileSync(sourcePath, source, "utf8");
  const result = runCheck(caseRoot);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout, /not registered/);
});
