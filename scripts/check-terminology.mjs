import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ignoredDirectories = new Set([
  ".git",
  "node_modules",
  "outputs",
  "__pycache__",
  ".pytest_cache",
  ".venv",
  "archive",
]);
const textExtensions = new Set([".md", ".json", ".yaml", ".yml", ".py", ".mjs", ".js", ".ps1", ".tex", ".sty"]);
const legacyProduct = ["th", "esis"].join("");
const legacyCaseKey = `${legacyProduct}_case`;
const legacySlideProduct = ["Slides", "Agent", "Tex"].join("_");
const removedProseSkill = ["human", "izer"].join("");
const removedFormatter = ["Subagent", "write", "latex"].join("_");
const removedEvidenceName = ["Subagent", "read", "paper"].join("_");
const pathRules = [
  { label: "legacy product term", pattern: new RegExp(`(^|[/_.-])${legacyProduct}([/_.-]|$)`, "i") },
  { label: "legacy slide product", pattern: new RegExp(legacySlideProduct, "i") },
  { label: "removed prose skill", pattern: new RegExp(removedProseSkill, "i") },
  { label: "removed formatter name", pattern: new RegExp(removedFormatter, "i") },
  { label: "removed evidence name", pattern: new RegExp(removedEvidenceName, "i") },
];
const textRules = [
  { label: "legacy product term", pattern: new RegExp(`\\b${legacyProduct}\\b`, "i") },
  { label: "legacy case key", pattern: new RegExp(legacyCaseKey, "i") },
  { label: "legacy slide product", pattern: new RegExp(legacySlideProduct, "i") },
  { label: "removed prose skill", pattern: new RegExp(removedProseSkill, "i") },
  { label: "removed formatter name", pattern: new RegExp(removedFormatter, "i") },
  { label: "removed evidence name", pattern: new RegExp(removedEvidenceName, "i") },
  { label: "removed content term", pattern: new RegExp("\\u8bba\\u6587", "u") },
];
const promptRules = [
  { label: "disallowed capability promise", pattern: new RegExp("\\u5199\\u4f5c|\\u6da6\\u8272|\\u6539\\u5199|\\u6269\\u5199|\\u751f\\u6210\\u5185\\u5bb9", "u") },
  { label: "disallowed prose workflow", pattern: /\bmanuscript\b|\bauthoring\b/i },
];

function walk(directory, results = []) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(fullPath, results);
    else results.push(fullPath);
  }
  return results;
}

function isPromptSurface(relativePath) {
  const name = path.basename(relativePath).toLowerCase();
  return name === "agents.md" || name === "readme.md" || name === "skill.md" || relativePath === "TERMS.md" || relativePath === "RELEASE.md";
}

const issues = [];
for (const filePath of walk(root)) {
  const relativePath = path.relative(root, filePath).replaceAll(path.sep, "/");
  for (const rule of pathRules) {
    if (rule.pattern.test(relativePath)) issues.push(`${relativePath}: ${rule.label} in path`);
  }
  if (!textExtensions.has(path.extname(filePath).toLowerCase())) continue;
  const content = fs.readFileSync(filePath, "utf8");
  for (const rule of textRules) {
    if (rule.pattern.test(content)) issues.push(`${relativePath}: ${rule.label}`);
  }
  if (isPromptSurface(relativePath)) {
    for (const rule of promptRules) {
      if (rule.pattern.test(content)) issues.push(`${relativePath}: ${rule.label}`);
    }
  }
}

if (issues.length > 0) {
  console.error(issues.join("\n"));
  process.exit(1);
}
console.log("Terminology and capability boundary check passed.");
