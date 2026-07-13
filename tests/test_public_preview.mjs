import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  DEFAULT_SOURCE_ROOT,
  SYNC_MANIFEST_FILE,
  syncPublicPreview,
} from "../scripts/public-preview-lib.mjs";
import {
  checkPresentationCase,
  DEFAULT_CASE_ROOT,
  PREVIEW_ROOT,
} from "../distribution/public-preview/scripts/check-demo.mjs";

const TEST_ROOT = path.dirname(fileURLToPath(import.meta.url));

function runGit(targetRoot, args) {
  const result = spawnSync("git", ["-C", targetRoot, ...args], { encoding: "utf8", shell: false });
  if ((result.status ?? 1) !== 0) throw new Error(result.stderr || result.stdout);
}

function initTarget() {
  const targetRoot = fs.mkdtempSync(path.join(os.tmpdir(), "public-preview-target-"));
  runGit(targetRoot, ["init"]);
  fs.writeFileSync(path.join(targetRoot, "retired-tracked.txt"), "retired\n", "utf8");
  runGit(targetRoot, ["add", "."]);
  runGit(targetRoot, ["-c", "user.name=Preview Test", "-c", "user.email=preview@example.invalid", "commit", "-m", "initial"]);
  return targetRoot;
}

function commitTarget(targetRoot, message) {
  const manifest = JSON.parse(fs.readFileSync(path.join(targetRoot, SYNC_MANIFEST_FILE), "utf8"));
  runGit(targetRoot, ["add", "-u"]);
  runGit(targetRoot, ["add", "--", SYNC_MANIFEST_FILE, ...manifest.files.map((file) => file.path)]);
  runGit(targetRoot, ["-c", "user.name=Preview Test", "-c", "user.email=preview@example.invalid", "commit", "-m", message]);
}

test("preview synchronization removes stale tracked files and preserves unrelated untracked files", () => {
  const targetRoot = initTarget();
  try {
    const localAsset = path.join(targetRoot, "assets", "legacy-local.png");
    fs.mkdirSync(path.dirname(localAsset), { recursive: true });
    fs.writeFileSync(localAsset, "local-only", "utf8");

    const result = syncPublicPreview({ targetRoot, skipRemoteCheck: true });
    assert.equal(result.status, "synchronized");
    assert.equal(fs.existsSync(path.join(targetRoot, "retired-tracked.txt")), false);
    assert.equal(fs.readFileSync(localAsset, "utf8"), "local-only");
    assert.equal(fs.existsSync(path.join(targetRoot, SYNC_MANIFEST_FILE)), true);

    const workingTreeCheck = syncPublicPreview({ targetRoot, skipRemoteCheck: true, check: true });
    assert.equal(workingTreeCheck.status, "in_sync");
    const managedRepeat = syncPublicPreview({ targetRoot, skipRemoteCheck: true });
    assert.equal(managedRepeat.status, "in_sync");

    commitTarget(targetRoot, "synchronize preview");
    const check = syncPublicPreview({ targetRoot, skipRemoteCheck: true, check: true });
    assert.equal(check.status, "in_sync");
    assert.deepEqual(check.copies, []);
    assert.deepEqual(check.removals, []);
    const terminology = spawnSync(process.execPath, [path.join(targetRoot, "scripts", "check-terminology.mjs")], {
      cwd: targetRoot,
      encoding: "utf8",
      shell: false,
    });
    assert.equal(terminology.status, 0, terminology.stderr || terminology.stdout);

    fs.appendFileSync(path.join(targetRoot, "README.md"), "local tracked edit\n", "utf8");
    assert.throws(
      () => syncPublicPreview({ targetRoot, skipRemoteCheck: true }),
      /tracked change/,
    );
  } finally {
    fs.rmSync(targetRoot, { recursive: true, force: true });
  }
});

test("preview synchronization refuses a conflicting untracked allowlist path", () => {
  const targetRoot = initTarget();
  try {
    fs.writeFileSync(path.join(targetRoot, "README.md"), "unrelated local file\n", "utf8");
    assert.throws(
      () => syncPublicPreview({ targetRoot, skipRemoteCheck: true }),
      /Refusing to overwrite untracked preview file: README.md/,
    );
  } finally {
    fs.rmSync(targetRoot, { recursive: true, force: true });
  }
});

function copyDemoFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "public-preview-demo-"));
  fs.cpSync(path.join(PREVIEW_ROOT, "examples"), path.join(root, "examples"), {
    recursive: true,
    filter: (source) => !source.includes(`${path.sep}outputs${path.sep}`) && !source.endsWith(`${path.sep}outputs`),
  });
  return {
    root,
    caseRoot: path.join(root, path.relative(PREVIEW_ROOT, DEFAULT_CASE_ROOT)),
  };
}

function mutateManifest(caseRoot, callback) {
  const manifestPath = path.join(caseRoot, "manifests", "presentation_manifest.json");
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  callback(manifest);
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
}

test("public presentation fixture passes provenance checks", () => {
  const report = checkPresentationCase({ root: PREVIEW_ROOT, caseRoot: DEFAULT_CASE_ROOT, writeReport: false });
  assert.equal(report.status, "pass");
  assert.deepEqual(report.issues, []);
});

for (const scenario of [
  {
    name: "unknown source reference",
    mutate: (fixture) => mutateManifest(fixture.caseRoot, (manifest) => { manifest.slides[0].source_refs = ["missing-source"]; }),
    code: "unknown_source_ref",
  },
  {
    name: "empty source references",
    mutate: (fixture) => mutateManifest(fixture.caseRoot, (manifest) => { manifest.slides[0].source_refs = []; }),
    code: "empty_source_refs",
  },
  {
    name: "missing frame label",
    mutate: (fixture) => {
      const mainPath = path.join(fixture.caseRoot, "source", "main.tex");
      fs.writeFileSync(mainPath, fs.readFileSync(mainPath, "utf8").replace("\\label{slide:title}", ""), "utf8");
    },
    code: "invalid_frame_label_count",
  },
  {
    name: "unregistered frame",
    mutate: (fixture) => {
      const mainPath = path.join(fixture.caseRoot, "source", "main.tex");
      fs.writeFileSync(mainPath, fs.readFileSync(mainPath, "utf8").replace("\\label{slide:title}", "\\label{slide:not-registered}"), "utf8");
    },
    code: "unregistered_frame",
  },
]) {
  test(`public presentation fixture rejects ${scenario.name}`, () => {
    const fixture = copyDemoFixture();
    try {
      scenario.mutate(fixture);
      const report = checkPresentationCase({ root: fixture.root, caseRoot: fixture.caseRoot, writeReport: false });
      assert.equal(report.status, "fail");
      assert.equal(report.issues.some((issue) => issue.code === scenario.code), true);
    } finally {
      fs.rmSync(fixture.root, { recursive: true, force: true });
    }
  });
}

test("preview source allowlist is readable from the private source of truth", () => {
  assert.equal(fs.existsSync(path.join(DEFAULT_SOURCE_ROOT, ".public-preview-allowlist.json")), true);
  assert.equal(path.resolve(TEST_ROOT, "..", "distribution", "public-preview"), DEFAULT_SOURCE_ROOT);
});
