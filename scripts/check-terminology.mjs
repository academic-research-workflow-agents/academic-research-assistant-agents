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
const retiredPaidToken = ["p", "aid"].join("");
const retiredSourceRepository = ["agents", retiredPaidToken, "source"].join("-");
const retiredPreviewRepository = ["agents", "preview"].join("-");
const retiredPreviewConcept = ["public", "preview"].join("[\\s_-]+");
const retiredPreviewSlug = ["public", "preview"].join("-");
const retiredDistributionPath = ["distribution", retiredPreviewSlug].join("/");
const retiredSyncScript = ["sync", retiredPreviewSlug].join("-");
const retiredSyncLibrary = [retiredPreviewSlug, "lib"].join("-");
const retiredPreviewTest = ["test", "public", "preview"].join("_");
const retiredArchiveScript = ["New", "PaidReleasePackage"].join("-");
const retiredPurchaseDocument = ["BU", "Y.md"].join("");
const archiveSuffix = [".", "zip"].join("");
const commercialEnglish = [
  ["b", "uy"].join(""),
  ["b", "uyer"].join(""),
  ["p", "aid"].join(""),
  ["s", "elling"].join(""),
  ["p", "urchase"].join(""),
  ["p", "ayment"].join(""),
  ["r", "esale"].join(""),
  ["r", "esell"].join(""),
].join("|");
const pathRules = [
  { label: "legacy product term", pattern: new RegExp(`(^|[/_.-])${legacyProduct}([/_.-]|$)`, "i") },
  { label: "legacy slide product", pattern: new RegExp(legacySlideProduct, "i") },
  { label: "removed prose skill", pattern: new RegExp(removedProseSkill, "i") },
  { label: "removed formatter name", pattern: new RegExp(removedFormatter, "i") },
  { label: "removed evidence name", pattern: new RegExp(removedEvidenceName, "i") },
  { label: "retired distribution tree", pattern: new RegExp(`^${retiredDistributionPath}(?:/|$)`, "i") },
  { label: "retired synchronization script", pattern: new RegExp(`${retiredSyncScript}|${retiredSyncLibrary}|${retiredPreviewTest}`, "i") },
  { label: "retired archive script", pattern: new RegExp(retiredArchiveScript, "i") },
  { label: "retired commercial document", pattern: new RegExp(`^(?:${retiredPurchaseDocument}|TERMS\\.md|RELEASE\\.md)$`, "i") },
  { label: "archive must not be tracked", pattern: new RegExp(`${archiveSuffix.replace(".", "\\.")}$`, "i") },
];
const textRules = [
  { label: "legacy product term", pattern: new RegExp(`\\b${legacyProduct}\\b`, "i") },
  { label: "legacy case key", pattern: new RegExp(legacyCaseKey, "i") },
  { label: "legacy slide product", pattern: new RegExp(legacySlideProduct, "i") },
  { label: "removed prose skill", pattern: new RegExp(removedProseSkill, "i") },
  { label: "removed formatter name", pattern: new RegExp(removedFormatter, "i") },
  { label: "removed evidence name", pattern: new RegExp(removedEvidenceName, "i") },
  { label: "removed content term", pattern: new RegExp("\\u8bba\\u6587", "u") },
  { label: "retired source repository", pattern: new RegExp(retiredSourceRepository, "i") },
  { label: "retired preview repository", pattern: new RegExp(retiredPreviewRepository, "i") },
  { label: "retired preview channel", pattern: new RegExp(retiredPreviewConcept, "i") },
  { label: "commercial language", pattern: new RegExp("\\u8d2d\\u4e70|\\u4ed8\\u8d39|\\u552e\\u5356|\\u9500\\u552e|\\u8f6c\\u5356|\\u4ed8\\u6b3e|\\u4ef7\\u683c|\\u6388\\u6743\\u4ea4\\u4ed8", "u") },
  { label: "commercial language", pattern: new RegExp(`\\b(?:${commercialEnglish})\\b`, "i") },
  { label: "email address", pattern: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i },
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
