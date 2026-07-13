import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const controlPath = path.join(root, ".public-preview-allowlist.json");
const textExtensions = new Set([".md", ".json", ".mjs", ".js", ".tex", ".sty", ".svg", ".yaml", ".yml"]);
const retiredLongFormTerm = ["th", "esis"].join("");
const retiredSlideProduct = ["Slides", "Agent", "Tex"].join("_");
const retiredProseSkill = ["human", "izer"].join("");
const retiredFormatter = ["Subagent", "write", "latex"].join("_");
const retiredEvidenceName = ["Subagent", "read", "paper"].join("_");

function listedFiles() {
  if (fs.existsSync(controlPath)) {
    const control = JSON.parse(fs.readFileSync(controlPath, "utf8"));
    return (control.files || []).map((filePath) => filePath.replaceAll("\\", "/"));
  }
  const result = spawnSync("git", ["-C", root, "ls-files", "-z"], { encoding: "utf8", shell: false });
  if ((result.status ?? 1) !== 0) throw new Error(`Unable to list tracked preview files: ${result.stderr || result.stdout}`);
  const files = new Set(result.stdout.split("\0").filter(Boolean).map((filePath) => filePath.replaceAll("\\", "/")));
  const syncManifestPath = path.join(root, ".preview-sync-manifest.json");
  if (fs.existsSync(syncManifestPath)) {
    const manifest = JSON.parse(fs.readFileSync(syncManifestPath, "utf8"));
    for (const file of manifest.files || []) files.add(String(file.path).replaceAll("\\", "/"));
  }
  return [...files].filter((filePath) => fs.existsSync(path.join(root, ...filePath.split("/"))));
}

const pathRules = [
  { label: "retired long-form product term", pattern: new RegExp(`(^|[/_.-])${retiredLongFormTerm}([/_.-]|$)`, "i") },
  { label: "retired slide product", pattern: new RegExp(retiredSlideProduct, "i") },
  { label: "retired prose skill", pattern: new RegExp(retiredProseSkill, "i") },
  { label: "retired formatter", pattern: new RegExp(retiredFormatter, "i") },
  { label: "retired evidence name", pattern: new RegExp(retiredEvidenceName, "i") },
];
const textRules = [
  { label: "retired long-form product term", pattern: new RegExp(`\\b${retiredLongFormTerm}\\b`, "i") },
  { label: "retired slide product", pattern: new RegExp(retiredSlideProduct, "i") },
  { label: "retired prose skill", pattern: new RegExp(retiredProseSkill, "i") },
  { label: "retired formatter", pattern: new RegExp(retiredFormatter, "i") },
  { label: "retired evidence name", pattern: new RegExp(retiredEvidenceName, "i") },
  { label: "retired Chinese product term", pattern: new RegExp("\\u8bba\\u6587", "u") },
];
const capabilityRule = new RegExp("\\u5199\\u4f5c|\\u6da6\\u8272|\\u6539\\u5199|\\u6269\\u5199|\\u751f\\u6210\\u5185\\u5bb9", "u");
const proseWorkflowRule = /\bmanuscript\b|\bauthoring\b/i;

const issues = [];
for (const relativePath of listedFiles()) {
  for (const rule of pathRules) {
    if (rule.pattern.test(relativePath)) issues.push(`${relativePath}: ${rule.label} in path`);
  }
  const filePath = path.join(root, ...relativePath.split("/"));
  if (!fs.existsSync(filePath) || !textExtensions.has(path.extname(filePath).toLowerCase())) continue;
  const content = fs.readFileSync(filePath, "utf8");
  for (const rule of textRules) {
    if (rule.pattern.test(content)) issues.push(`${relativePath}: ${rule.label}`);
  }
  if (path.extname(filePath).toLowerCase() === ".md" && (capabilityRule.test(content) || proseWorkflowRule.test(content))) {
    issues.push(`${relativePath}: disallowed prose capability`);
  }
}

if (issues.length > 0) {
  console.error(issues.join("\n"));
  process.exit(1);
}
console.log("Public preview terminology and capability boundary check passed.");
