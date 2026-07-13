import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_ROOT = path.dirname(fileURLToPath(import.meta.url));
export const PREVIEW_ROOT = path.resolve(SCRIPT_ROOT, "..");
export const DEFAULT_CASE_ROOT = path.join(PREVIEW_ROOT, "examples", "example_research", "example_presentation");
const ALLOWED_TRANSFORMS = new Set(["verbatim", "extract", "compress", "layout"]);

function isWithin(parent, target) {
  const relative = path.relative(path.resolve(parent), path.resolve(target));
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function listTexFiles(sourceRoot) {
  if (!fs.existsSync(sourceRoot)) return [];
  const results = [];
  const stack = [sourceRoot];
  while (stack.length > 0) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(fullPath);
      else if (entry.isFile() && entry.name.toLowerCase().endsWith(".tex")) results.push(fullPath);
    }
  }
  return results.sort();
}

function addIssue(report, code, message, file = null) {
  report.issues.push({
    severity: "error",
    code,
    message,
    file: file ? path.relative(report.root, file).replaceAll(path.sep, "/") : null,
  });
}

function writeJsonAtomic(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const temporary = `${filePath}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(temporary, filePath);
}

export function checkPresentationCase({ root = PREVIEW_ROOT, caseRoot = DEFAULT_CASE_ROOT, writeReport = true } = {}) {
  const resolvedRoot = path.resolve(root);
  const resolvedCase = path.resolve(caseRoot);
  if (!isWithin(resolvedRoot, resolvedCase)) throw new Error("Presentation case must stay inside the preview root.");

  const report = {
    schema_version: 1,
    root: resolvedRoot,
    case: path.relative(resolvedRoot, resolvedCase).replaceAll(path.sep, "/"),
    status: "pass",
    issues: [],
  };
  const manifestPath = path.join(resolvedCase, "manifests", "presentation_manifest.json");
  let manifest = null;
  if (!fs.existsSync(manifestPath)) {
    addIssue(report, "missing_manifest", "Missing manifests/presentation_manifest.json.", manifestPath);
  } else {
    try {
      manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    } catch (error) {
      addIssue(report, "invalid_manifest", `Invalid presentation manifest: ${error.message}`, manifestPath);
    }
  }

  if (manifest) {
    const expectedResearchCase = path.basename(path.dirname(resolvedCase));
    const expectedCaseId = path.basename(resolvedCase);
    if (manifest.research_case !== expectedResearchCase) addIssue(report, "research_case_mismatch", "research_case must match the outer case directory.", manifestPath);
    if (manifest.case_id !== expectedCaseId) addIssue(report, "case_id_mismatch", "case_id must match the child case directory.", manifestPath);
    if (manifest.case_type !== "presentation") addIssue(report, "invalid_case_type", "case_type must be presentation.", manifestPath);
    if (manifest.content_mode !== "evidence_bound") addIssue(report, "invalid_content_mode", "content_mode must be evidence_bound.", manifestPath);

    const templateRef = String(manifest.template_ref || "");
    const templateRoot = path.resolve(resolvedRoot, templateRef);
    if (!templateRef || !isWithin(resolvedRoot, templateRoot) || !fs.existsSync(path.join(templateRoot, "source"))) {
      addIssue(report, "invalid_template", `Invalid template_ref: ${templateRef || "<empty>"}.`, manifestPath);
    }

    const sourceIds = new Set();
    if (!Array.isArray(manifest.sources) || manifest.sources.length === 0) {
      addIssue(report, "empty_sources", "sources[] must contain at least one registered source.", manifestPath);
    }
    for (const source of manifest.sources || []) {
      const sourceId = String(source.id || "");
      if (!sourceId || sourceIds.has(sourceId)) addIssue(report, "invalid_source_id", `Missing or duplicate source id: ${sourceId || "<empty>"}.`, manifestPath);
      sourceIds.add(sourceId);
      const sourcePath = path.resolve(resolvedCase, String(source.path || ""));
      if (!source.path || !source.type || !isWithin(resolvedCase, sourcePath) || !fs.existsSync(sourcePath)) {
        addIssue(report, "invalid_source", `Registered source is incomplete, missing, or outside the case: ${source.path || "<empty>"}.`, manifestPath);
      }
    }

    const slideIds = new Set();
    if (!Array.isArray(manifest.slides) || manifest.slides.length === 0) {
      addIssue(report, "empty_slides", "slides[] must contain at least one registered slide.", manifestPath);
    }
    for (const slide of manifest.slides || []) {
      const slideId = String(slide.id || "");
      if (!slideId || slideIds.has(slideId)) addIssue(report, "invalid_slide_id", `Missing or duplicate slide id: ${slideId || "<empty>"}.`, manifestPath);
      slideIds.add(slideId);
      if (!ALLOWED_TRANSFORMS.has(slide.transform)) addIssue(report, "invalid_transform", `Unsupported transform for slide ${slideId || "<empty>"}: ${slide.transform || "<empty>"}.`, manifestPath);
      if (!Array.isArray(slide.source_refs) || slide.source_refs.length === 0) {
        addIssue(report, "empty_source_refs", `Slide ${slideId || "<empty>"} has no source_refs.`, manifestPath);
      }
      for (const sourceRef of slide.source_refs || []) {
        if (!sourceIds.has(sourceRef)) addIssue(report, "unknown_source_ref", `Slide ${slideId || "<empty>"} references unknown source: ${sourceRef}.`, manifestPath);
      }
    }

    const frameIds = [];
    const framePattern = /\\begin\{frame\}(?:\[[^\]]*\])?(?:\{[^}]*\})?([\s\S]*?)\\end\{frame\}/g;
    const labelPattern = /\\label\{slide:([^}]+)\}/g;
    const sourceRoot = path.join(resolvedCase, "source");
    for (const texPath of listTexFiles(sourceRoot)) {
      const content = fs.readFileSync(texPath, "utf8");
      for (const frame of content.matchAll(framePattern)) {
        const labels = [...frame[1].matchAll(labelPattern)].map((match) => match[1]);
        if (labels.length !== 1) addIssue(report, "invalid_frame_label_count", "Every frame must contain exactly one slide:<id> label.", texPath);
        else frameIds.push(labels[0]);
      }
    }
    if (frameIds.length === 0) addIssue(report, "no_frames", "No Beamer frames were found.", sourceRoot);
    for (const frameId of frameIds) {
      if (!slideIds.has(frameId)) addIssue(report, "unregistered_frame", `Frame label is not registered in slides[]: ${frameId}.`, manifestPath);
    }
    for (const slideId of slideIds) {
      if (!frameIds.includes(slideId)) addIssue(report, "missing_frame", `Registered slide has no matching frame label: ${slideId}.`, manifestPath);
    }
  }

  if (report.issues.length > 0) report.status = "fail";
  delete report.root;
  if (writeReport) {
    writeJsonAtomic(path.join(resolvedCase, "outputs", "check", "source_check_report.json"), report);
  }
  return report;
}

function parseArgs(argv) {
  let caseRoot = DEFAULT_CASE_ROOT;
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] !== "--case" || !argv[index + 1]) throw new Error(`Unknown or incomplete argument: ${argv[index]}`);
    caseRoot = path.resolve(PREVIEW_ROOT, argv[index + 1]);
    index += 1;
  }
  return { caseRoot };
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  try {
    const report = checkPresentationCase(parseArgs(process.argv.slice(2)));
    console.log(JSON.stringify(report, null, 2));
    if (report.status !== "pass") process.exitCode = 1;
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
