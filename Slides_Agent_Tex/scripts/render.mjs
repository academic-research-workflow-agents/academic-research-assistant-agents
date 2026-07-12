import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import {
  assertCaseRoot,
  caseIdFromManifest,
  copyDir,
  ensureDir,
  findCaseManifest,
  parseArgs,
  resolveWorkspacePath,
  safeRemoveInside,
  toWorkspaceRelative,
  writeJson,
} from "./lib/case-utils.mjs";

function buildWorktree(caseRoot, manifest) {
  const buildRoot = path.join(caseRoot, "outputs", "build");
  ensureDir(buildRoot);

  if (manifest.case_type === "deck") {
    const templateRoot = resolveWorkspacePath(manifest.template_case);
    const templateSource = path.join(templateRoot, "source");
    const worktree = path.join(buildRoot, "template-worktree");
    safeRemoveInside(buildRoot, worktree);
    copyDir(templateSource, worktree);
    copyDir(path.join(caseRoot, "source"), worktree);
    copyDir(path.join(caseRoot, "assets"), path.join(worktree, "assets"));
    return worktree;
  }

  const worktree = path.join(buildRoot, "source-worktree");
  safeRemoveInside(buildRoot, worktree);
  copyDir(path.join(caseRoot, "source"), worktree);
  return worktree;
}

function runLatexmk(worktree, latexOut) {
  ensureDir(latexOut);
  const result = spawnSync(
    "latexmk",
    ["-xelatex", "-interaction=nonstopmode", "-halt-on-error", `-outdir=${latexOut}`, "main.tex"],
    {
      cwd: worktree,
      encoding: "utf8",
      shell: false,
    },
  );

  return {
    status: result.status ?? 1,
    stdout: result.stdout || "",
    stderr: result.stderr || "",
  };
}

function collectLatexSignals(logPath) {
  if (!fs.existsSync(logPath)) {
    return {
      missing_log: true,
      fatal_errors: [],
      undefined_citations: [],
      undefined_references: [],
      overfull_boxes: [],
    };
  }

  const text = fs.readFileSync(logPath, "utf8");
  const lines = text.split(/\r?\n/);
  return {
    missing_log: false,
    fatal_errors: lines.filter((line) => /^! /.test(line)).slice(0, 20),
    undefined_citations: lines.filter((line) => /Citation .* undefined/.test(line)).slice(0, 20),
    undefined_references: lines.filter((line) => /Reference .* undefined/.test(line)).slice(0, 20),
    overfull_boxes: lines.filter((line) => /Overfull \\hbox/.test(line)).slice(0, 20),
  };
}

function copyRenderOutputs(caseRoot, caseId, latexOut) {
  const pdfDir = path.join(caseRoot, "outputs", "pdf");
  const logDir = path.join(caseRoot, "outputs", "logs");
  ensureDir(pdfDir);
  ensureDir(logDir);

  const pdfSource = path.join(latexOut, "main.pdf");
  const logSource = path.join(latexOut, "main.log");
  const pdfTarget = path.join(pdfDir, `${caseId}.pdf`);
  const logTarget = path.join(logDir, `${caseId}.log`);

  if (fs.existsSync(pdfSource)) {
    fs.copyFileSync(pdfSource, pdfTarget);
  }
  if (fs.existsSync(logSource)) {
    fs.copyFileSync(logSource, logTarget);
  }

  return { pdfTarget, logTarget };
}

function compileCase(caseRoot, manifest) {
  const caseId = caseIdFromManifest(caseRoot, manifest);
  const worktree = buildWorktree(caseRoot, manifest);
  const latexOut = path.join(caseRoot, "outputs", "build", "latex");
  safeRemoveInside(path.join(caseRoot, "outputs", "build"), latexOut);
  ensureDir(latexOut);

  const result = runLatexmk(worktree, latexOut);
  const outputs = copyRenderOutputs(caseRoot, caseId, latexOut);
  const signals = collectLatexSignals(outputs.logTarget);
  const report = {
    case: toWorkspaceRelative(caseRoot),
    case_id: caseId,
    status: result.status === 0 ? "pass" : "fail",
    worktree: toWorkspaceRelative(worktree),
    pdf: fs.existsSync(outputs.pdfTarget) ? toWorkspaceRelative(outputs.pdfTarget) : null,
    log: fs.existsSync(outputs.logTarget) ? toWorkspaceRelative(outputs.logTarget) : null,
    latex_signals: signals,
  };

  writeJson(path.join(caseRoot, "outputs", "logs", "render_report.json"), report);
  if (result.status !== 0) {
    fs.writeFileSync(path.join(caseRoot, "outputs", "logs", `${caseId}.stdout.txt`), result.stdout, "utf8");
    fs.writeFileSync(path.join(caseRoot, "outputs", "logs", `${caseId}.stderr.txt`), result.stderr, "utf8");
  }

  return report;
}

function findPdfForCase(caseRoot, manifest) {
  const caseId = caseIdFromManifest(caseRoot, manifest);
  const pdfPath = path.join(caseRoot, "outputs", "pdf", `${caseId}.pdf`);
  return fs.existsSync(pdfPath) ? pdfPath : null;
}

function exportPngs(caseRoot, manifest, pdfPath) {
  const pngDir = path.join(caseRoot, "outputs", "png");
  safeRemoveInside(path.join(caseRoot, "outputs"), pngDir);
  ensureDir(pngDir);

  const prefix = path.join(pngDir, "slide");
  const result = spawnSync("pdftoppm", ["-png", "-r", "160", pdfPath, prefix], {
    encoding: "utf8",
    shell: false,
  });

  if ((result.status ?? 1) !== 0) {
    throw new Error(`pdftoppm failed: ${result.stderr || result.stdout}`);
  }

  const generated = fs
    .readdirSync(pngDir)
    .filter((name) => /^slide-\d+\.png$/.test(name))
    .sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]));

  generated.forEach((name, index) => {
    const target = `slide.${String(index + 1).padStart(3, "0")}.png`;
    fs.renameSync(path.join(pngDir, name), path.join(pngDir, target));
  });

  const report = {
    case: toWorkspaceRelative(caseRoot),
    pdf: toWorkspaceRelative(pdfPath),
    png_dir: toWorkspaceRelative(pngDir),
    slides: generated.length,
  };
  writeJson(path.join(caseRoot, "outputs", "logs", "png_report.json"), report);
  return report;
}

const args = parseArgs(process.argv.slice(2));
const caseRoot = resolveWorkspacePath(args.casePath);
assertCaseRoot(caseRoot);

const manifestResult = findCaseManifest(caseRoot);
if (!manifestResult) {
  throw new Error(`No case manifest found under ${caseRoot}`);
}

const manifest = manifestResult.data;
let pdfPath = findPdfForCase(caseRoot, manifest);
let compileReport = null;

if (!args.pngOnly || !pdfPath) {
  compileReport = compileCase(caseRoot, manifest);
  if (compileReport.status !== "pass") {
    console.log(JSON.stringify(compileReport, null, 2));
    process.exit(1);
  }
  pdfPath = findPdfForCase(caseRoot, manifest);
}

if (args.pngOnly) {
  if (!pdfPath) {
    throw new Error("No PDF is available for PNG export");
  }
  const pngReport = exportPngs(caseRoot, manifest, pdfPath);
  console.log(JSON.stringify(pngReport, null, 2));
} else {
  console.log(JSON.stringify(compileReport, null, 2));
}
