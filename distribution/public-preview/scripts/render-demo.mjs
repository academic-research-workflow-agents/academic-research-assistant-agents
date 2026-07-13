import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { checkPresentationCase, DEFAULT_CASE_ROOT, PREVIEW_ROOT } from "./check-demo.mjs";

function isWithin(parent, target) {
  const relative = path.relative(path.resolve(parent), path.resolve(target));
  return relative !== "" && !relative.startsWith("..") && !path.isAbsolute(relative);
}

function safeRemove(parent, target) {
  if (!isWithin(parent, target)) throw new Error(`Refusing to remove unsafe path: ${target}`);
  fs.rmSync(target, { recursive: true, force: true });
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { encoding: "utf8", shell: false, ...options });
  if ((result.status ?? 1) !== 0) {
    throw new Error(`${command} failed:\n${result.stderr || result.stdout || "No diagnostic output."}`);
  }
  return result;
}

function compile(caseRoot, manifest) {
  const outputsRoot = path.join(caseRoot, "outputs");
  const buildRoot = path.join(outputsRoot, "build");
  const worktree = path.join(buildRoot, "worktree");
  const latexOut = path.join(buildRoot, "latex");
  safeRemove(outputsRoot, buildRoot);
  fs.mkdirSync(worktree, { recursive: true });
  fs.mkdirSync(latexOut, { recursive: true });

  const templateRoot = path.resolve(PREVIEW_ROOT, manifest.template_ref, "source");
  fs.cpSync(templateRoot, worktree, { recursive: true });
  fs.cpSync(path.join(caseRoot, "source"), worktree, { recursive: true });
  const result = run("latexmk", ["-xelatex", "-interaction=nonstopmode", "-halt-on-error", `-outdir=${latexOut}`, "main.tex"], { cwd: worktree });

  const pdfDir = path.join(outputsRoot, "pdf");
  const logDir = path.join(outputsRoot, "logs");
  fs.mkdirSync(pdfDir, { recursive: true });
  fs.mkdirSync(logDir, { recursive: true });
  const pdfTarget = path.join(pdfDir, `${manifest.case_id}.pdf`);
  const logTarget = path.join(logDir, `${manifest.case_id}.log`);
  fs.copyFileSync(path.join(latexOut, "main.pdf"), pdfTarget);
  if (fs.existsSync(path.join(latexOut, "main.log"))) fs.copyFileSync(path.join(latexOut, "main.log"), logTarget);
  fs.writeFileSync(path.join(logDir, "latexmk.stdout.txt"), result.stdout || "", "utf8");
  return pdfTarget;
}

function exportPng(caseRoot, pdfPath) {
  const outputsRoot = path.join(caseRoot, "outputs");
  const pngDir = path.join(outputsRoot, "png");
  safeRemove(outputsRoot, pngDir);
  fs.mkdirSync(pngDir, { recursive: true });
  run("pdftoppm", ["-png", "-r", "160", pdfPath, path.join(pngDir, "slide")]);
  const generated = fs.readdirSync(pngDir).filter((name) => /^slide-\d+\.png$/.test(name)).sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]));
  generated.forEach((name, index) => {
    fs.renameSync(path.join(pngDir, name), path.join(pngDir, `slide.${String(index + 1).padStart(3, "0")}.png`));
  });
  return generated.length;
}

function parseArgs(argv) {
  let caseRoot = DEFAULT_CASE_ROOT;
  let png = false;
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--png") png = true;
    else if (argv[index] === "--case" && argv[index + 1]) {
      caseRoot = path.resolve(PREVIEW_ROOT, argv[index + 1]);
      index += 1;
    } else throw new Error(`Unknown or incomplete argument: ${argv[index]}`);
  }
  return { caseRoot, png };
}

try {
  const options = parseArgs(process.argv.slice(2));
  const report = checkPresentationCase({ caseRoot: options.caseRoot });
  if (report.status !== "pass") throw new Error("Presentation source check failed; inspect outputs/check/source_check_report.json.");
  const manifest = JSON.parse(fs.readFileSync(path.join(options.caseRoot, "manifests", "presentation_manifest.json"), "utf8"));
  const pdfPath = compile(options.caseRoot, manifest);
  const result = {
    status: "pass",
    case_id: manifest.case_id,
    pdf: path.relative(PREVIEW_ROOT, pdfPath).replaceAll(path.sep, "/"),
    png_slides: options.png ? exportPng(options.caseRoot, pdfPath) : 0,
  };
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
