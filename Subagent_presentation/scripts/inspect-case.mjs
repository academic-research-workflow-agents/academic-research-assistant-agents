import fs from "node:fs";
import path from "node:path";
import {
  assertCaseRoot,
  findCaseManifest,
  parseArgs,
  resolveWorkspacePath,
  toWorkspaceRelative,
} from "./lib/case-utils.mjs";

const args = parseArgs(process.argv.slice(2));
const caseRoot = resolveWorkspacePath(args.casePath);
assertCaseRoot(caseRoot);

const manifest = findCaseManifest(caseRoot);
const sourceMain = path.join(caseRoot, "source", "main.tex");
const outputs = path.join(caseRoot, "outputs");

const summary = {
  case: toWorkspaceRelative(caseRoot),
  manifest: manifest ? toWorkspaceRelative(manifest.path) : null,
  case_type: manifest?.data?.case_type || null,
  case_id: manifest?.data?.case_id || null,
  has_source_main: fs.existsSync(sourceMain),
  has_outputs_dir: fs.existsSync(outputs),
  research_case: manifest?.data?.research_case || null,
  content_mode: manifest?.data?.content_mode || null,
  template_ref: manifest?.data?.template_ref || null,
};

console.log(JSON.stringify(summary, null, 2));
