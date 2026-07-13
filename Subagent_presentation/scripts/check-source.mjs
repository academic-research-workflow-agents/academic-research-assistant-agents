import fs from "node:fs";
import path from "node:path";
import {
  assertCaseRoot,
  ensureDir,
  findCaseManifest,
  listFiles,
  parseArgs,
  readJson,
  resolveWorkspacePath,
  toWorkspaceRelative,
  writeJson,
  WORKSPACE_ROOT,
} from "./lib/case-utils.mjs";

const GRAPHIC_EXTENSIONS = ["", ".pdf", ".png", ".jpg", ".jpeg"];
const SOURCE_EXTENSIONS = [".tex", ".sty", ".bib", ".json", ".md"];
const ALLOWED_TRANSFORMS = new Set(["verbatim", "extract", "compress", "layout"]);

function addIssue(report, severity, message, file = null) {
  report.issues.push({ severity, message, file: file ? toWorkspaceRelative(file) : null });
}

function isWithin(parent, target) {
  const relative = path.relative(path.resolve(parent), path.resolve(target));
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function checkRootHygiene(report, banned) {
  for (const name of ["AGENTS.md", "README.md"]) {
    const filePath = path.join(WORKSPACE_ROOT, name);
    if (!fs.existsSync(filePath)) continue;
    const content = fs.readFileSync(filePath, "utf8");
    for (const term of banned) {
      if (content.includes(term)) addIssue(report, "error", `Root file contains case-specific term: ${term}`, filePath);
    }
  }
}

function resolveGraphicPath(rawPath, filePath, caseRoot) {
  if (/^https?:\/\//i.test(rawPath)) return true;
  if (path.isAbsolute(rawPath)) return false;
  const attempts = [];
  for (const extension of GRAPHIC_EXTENSIONS) {
    attempts.push(path.resolve(path.dirname(filePath), `${rawPath}${extension}`));
    attempts.push(path.resolve(caseRoot, `${rawPath}${extension}`));
    attempts.push(path.resolve(caseRoot, "source", `${rawPath}${extension}`));
  }
  return attempts.some((candidate) => fs.existsSync(candidate));
}

function checkIncludeGraphics(report, caseRoot) {
  const pattern = /\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}/g;
  for (const filePath of listFiles(caseRoot, [".tex", ".sty"])) {
    const content = fs.readFileSync(filePath, "utf8");
    for (const match of content.matchAll(pattern)) {
      const rawPath = match[1].trim();
      if (rawPath && !resolveGraphicPath(rawPath, filePath, caseRoot)) {
        addIssue(report, "error", `Missing or unsafe graphic asset: ${rawPath}`, filePath);
      }
    }
  }
}

function checkAbsolutePaths(report, caseRoot) {
  const pattern = /(?<![A-Za-z])[A-Za-z]:[\\/]/;
  for (const filePath of listFiles(caseRoot, SOURCE_EXTENSIONS)) {
    if (pattern.test(fs.readFileSync(filePath, "utf8"))) {
      addIssue(report, "error", "Source contains a machine-specific absolute path", filePath);
    }
  }
}

function readPresentationManifest(report, caseRoot) {
  const manifestPath = path.join(caseRoot, "manifests", "presentation_manifest.json");
  if (!fs.existsSync(manifestPath)) {
    addIssue(report, "error", "Missing manifests/presentation_manifest.json", manifestPath);
    return null;
  }
  try {
    return { path: manifestPath, data: readJson(manifestPath) };
  } catch (error) {
    addIssue(report, "error", `Invalid presentation manifest: ${error.message}`, manifestPath);
    return null;
  }
}

function checkManifest(report, caseRoot, manifestResult) {
  if (!manifestResult) return;
  const manifest = manifestResult.data;
  if (manifest.case_type !== "presentation") addIssue(report, "error", "case_type must be 'presentation'.", manifestResult.path);
  if (manifest.research_case !== path.basename(path.dirname(caseRoot))) addIssue(report, "error", "research_case must match the outer case directory.", manifestResult.path);
  if (manifest.case_id !== path.basename(caseRoot)) addIssue(report, "error", "case_id must match the child case directory.", manifestResult.path);
  if (manifest.content_mode !== "evidence_bound") addIssue(report, "error", "content_mode must be 'evidence_bound'.", manifestResult.path);

  const templateRef = String(manifest.template_ref || "");
  const templateRoot = resolveWorkspacePath(templateRef);
  if (!templateRef || !isWithin(WORKSPACE_ROOT, templateRoot) || !fs.existsSync(path.join(templateRoot, "source"))) {
    addIssue(report, "error", `Invalid template_ref: ${templateRef}`, manifestResult.path);
  }

  const sourceIds = new Set();
  for (const source of manifest.sources || []) {
    if (!source.id || sourceIds.has(source.id)) addIssue(report, "error", `Missing or duplicate source id: ${source.id || "<empty>"}`, manifestResult.path);
    sourceIds.add(source.id);
    const sourcePath = path.resolve(caseRoot, String(source.path || ""));
    if (!source.path || !isWithin(caseRoot, sourcePath) || !fs.existsSync(sourcePath)) {
      addIssue(report, "error", `Registered source does not exist or escapes the case: ${source.path || "<empty>"}`, manifestResult.path);
    }
  }

  const slideIds = new Set();
  for (const slide of manifest.slides || []) {
    if (!slide.id || slideIds.has(slide.id)) addIssue(report, "error", `Missing or duplicate slide id: ${slide.id || "<empty>"}`, manifestResult.path);
    slideIds.add(slide.id);
    if (!ALLOWED_TRANSFORMS.has(slide.transform)) addIssue(report, "error", `Unsupported transform for slide ${slide.id}: ${slide.transform}`, manifestResult.path);
    if (!Array.isArray(slide.source_refs) || slide.source_refs.length === 0) addIssue(report, "error", `Slide ${slide.id} has no source_refs.`, manifestResult.path);
    for (const reference of slide.source_refs || []) {
      if (!sourceIds.has(reference)) addIssue(report, "error", `Slide ${slide.id} references unknown source: ${reference}`, manifestResult.path);
    }
  }

  const frameIds = [];
  const framePattern = /\\begin\{frame\}(?:\[[^\]]*\])?(?:\{[^}]*\})?([\s\S]*?)\\end\{frame\}/g;
  const labelPattern = /\\label\{slide:([^}]+)\}/g;
  for (const filePath of listFiles(path.join(caseRoot, "source"), [".tex"])) {
    const content = fs.readFileSync(filePath, "utf8");
    for (const frame of content.matchAll(framePattern)) {
      const labels = [...frame[1].matchAll(labelPattern)].map((match) => match[1]);
      if (labels.length !== 1) addIssue(report, "error", "Every frame must contain exactly one \\label{slide:<id>}.", filePath);
      else frameIds.push(labels[0]);
    }
  }
  for (const id of frameIds) {
    if (!slideIds.has(id)) addIssue(report, "error", `Frame label is not registered in slides[]: ${id}`, manifestResult.path);
  }
  for (const id of slideIds) {
    if (!frameIds.includes(id)) addIssue(report, "error", `Registered slide has no matching frame label: ${id}`, manifestResult.path);
  }
  if (frameIds.length === 0) addIssue(report, "error", "No Beamer frames found in source files.", path.join(caseRoot, "source"));
}

const args = parseArgs(process.argv.slice(2));
const caseRoot = resolveWorkspacePath(args.casePath);
assertCaseRoot(caseRoot);
const report = { case: toWorkspaceRelative(caseRoot), status: "pass", issues: [] };
const manifestResult = readPresentationManifest(report, caseRoot);
checkManifest(report, caseRoot, manifestResult);
checkRootHygiene(report, manifestResult?.data?.root_forbidden_terms || []);

const sourceMain = path.join(caseRoot, "source", "main.tex");
if (!fs.existsSync(sourceMain)) addIssue(report, "error", "Missing source/main.tex", sourceMain);
checkIncludeGraphics(report, caseRoot);
checkAbsolutePaths(report, caseRoot);

if (report.issues.some((issue) => issue.severity === "error")) report.status = "fail";
else if (report.issues.length > 0) report.status = "warn";

const outDir = path.join(caseRoot, "outputs", "check");
ensureDir(outDir);
writeJson(path.join(outDir, "source_check_report.json"), report);
fs.writeFileSync(path.join(outDir, "source_check_report.md"), [
  "# Presentation Source Check Report",
  "",
  `- Case: \`${report.case}\``,
  `- Status: \`${report.status}\``,
  "",
  ...report.issues.map((issue) => `- ${issue.severity}: ${issue.message}${issue.file ? ` (${issue.file})` : ""}`),
  report.issues.length === 0 ? "- No issues found." : "",
  "",
].join("\n"), "utf8");
console.log(JSON.stringify(report, null, 2));
if (report.status === "fail") process.exitCode = 1;
