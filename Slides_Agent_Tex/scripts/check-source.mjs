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

function addIssue(issues, severity, message, file = null) {
  issues.push({
    severity,
    message,
    file: file ? toWorkspaceRelative(file) : null,
  });
}

function checkRootHygiene(report, banned) {
  const rootFiles = ["AGENTS.md", "README.md", "package.json"];
  for (const name of rootFiles) {
    const filePath = path.join(WORKSPACE_ROOT, name);
    if (!fs.existsSync(filePath)) {
      continue;
    }
    const text = fs.readFileSync(filePath, "utf8");
    for (const term of banned) {
      if (text.includes(term)) {
        addIssue(report.issues, "error", `Root file contains case-specific term: ${term}`, filePath);
      }
    }
  }
}

function resolveGraphicPath(rawPath, filePath, caseRoot) {
  if (/^https?:\/\//i.test(rawPath)) {
    return true;
  }
  if (path.isAbsolute(rawPath)) {
    return fs.existsSync(rawPath);
  }

  const attempts = [];
  for (const ext of GRAPHIC_EXTENSIONS) {
    attempts.push(path.resolve(path.dirname(filePath), `${rawPath}${ext}`));
    attempts.push(path.resolve(caseRoot, `${rawPath}${ext}`));
    attempts.push(path.resolve(caseRoot, "source", `${rawPath}${ext}`));
  }

  return attempts.some((candidate) => fs.existsSync(candidate));
}

function checkIncludeGraphics(report, caseRoot) {
  const files = listFiles(caseRoot, [".tex", ".sty"]);
  const pattern = /\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}/g;

  for (const filePath of files) {
    const text = fs.readFileSync(filePath, "utf8");
    let match = pattern.exec(text);
    while (match) {
      const rawPath = match[1].trim();
      if (rawPath && !resolveGraphicPath(rawPath, filePath, caseRoot)) {
        addIssue(report.issues, "error", `Missing graphic asset: ${rawPath}`, filePath);
      }
      match = pattern.exec(text);
    }
  }
}

function checkAbsolutePaths(report, caseRoot) {
  const files = listFiles(caseRoot, SOURCE_EXTENSIONS);
  const absolutePattern = /(?<![A-Za-z])[A-Za-z]:[\\/]/;

  for (const filePath of files) {
    const text = fs.readFileSync(filePath, "utf8");
    if (absolutePattern.test(text)) {
      addIssue(report.issues, "warning", "Source contains a machine-specific absolute path", filePath);
    }
  }
}

function checkManifest(report, caseRoot) {
  const manifestDir = path.join(caseRoot, "manifests");
  if (!fs.existsSync(manifestDir)) {
    addIssue(report.issues, "error", "Missing manifests directory", caseRoot);
    return null;
  }

  for (const name of fs.readdirSync(manifestDir).filter((item) => item.endsWith(".json"))) {
    const filePath = path.join(manifestDir, name);
    try {
      readJson(filePath);
    } catch (error) {
      addIssue(report.issues, "error", `Invalid JSON: ${error.message}`, filePath);
    }
  }

  const found = findCaseManifest(caseRoot);
  if (!found) {
    addIssue(report.issues, "error", "No case manifest with case_type or case_id found", manifestDir);
    return null;
  }

  const manifest = found.data;
  if (!manifest.case_type) {
    addIssue(report.issues, "error", "Manifest is missing case_type", found.path);
  }

  if (manifest.case_type === "deck") {
    if (!manifest.template_case) {
      addIssue(report.issues, "error", "Deck manifest is missing template_case", found.path);
    } else {
      const templateRoot = resolveWorkspacePath(manifest.template_case);
      if (!fs.existsSync(templateRoot)) {
        addIssue(report.issues, "error", `Template case does not exist: ${manifest.template_case}`, found.path);
      }
    }
  }

  return found;
}

const args = parseArgs(process.argv.slice(2));
const caseRoot = resolveWorkspacePath(args.casePath);
assertCaseRoot(caseRoot);

const report = {
  case: toWorkspaceRelative(caseRoot),
  status: "pass",
  issues: [],
};

const manifest = checkManifest(report, caseRoot);
checkRootHygiene(report, manifest?.data?.root_forbidden_terms || []);

const sourceMain = path.join(caseRoot, "source", "main.tex");
if (manifest?.data?.case_type && ["template_source", "deck"].includes(manifest.data.case_type)) {
  if (!fs.existsSync(sourceMain)) {
    addIssue(report.issues, "error", "Missing source/main.tex", sourceMain);
  }
}

checkIncludeGraphics(report, caseRoot);
checkAbsolutePaths(report, caseRoot);

if (report.issues.some((issue) => issue.severity === "error")) {
  report.status = "fail";
} else if (report.issues.length > 0) {
  report.status = "warn";
}

const outDir = path.join(caseRoot, "outputs", "check");
ensureDir(outDir);
writeJson(path.join(outDir, "source_check_report.json"), report);
fs.writeFileSync(
  path.join(outDir, "source_check_report.md"),
  [
    `# Source Check Report`,
    ``,
    `- Case: \`${report.case}\``,
    `- Status: \`${report.status}\``,
    ``,
    ...report.issues.map((issue) => `- ${issue.severity}: ${issue.message}${issue.file ? ` (${issue.file})` : ""}`),
    report.issues.length === 0 ? "- No issues found." : "",
    "",
  ].join("\n"),
  "utf8",
);

console.log(JSON.stringify(report, null, 2));
if (report.status === "fail") {
  process.exitCode = 1;
}
