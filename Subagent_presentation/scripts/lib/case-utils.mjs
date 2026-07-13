import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const WORKSPACE_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
);

export function parseArgs(argv) {
  const args = {
    casePath: null,
    pngOnly: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--case") {
      args.casePath = argv[i + 1];
      i += 1;
    } else if (arg === "--png-only") {
      args.pngOnly = true;
    }
  }

  if (!args.casePath) {
    throw new Error("Missing required argument: --case <child_case>");
  }

  return args;
}

export function resolveWorkspacePath(inputPath) {
  if (path.isAbsolute(inputPath)) {
    return path.resolve(inputPath);
  }
  return path.resolve(WORKSPACE_ROOT, inputPath);
}

export function toWorkspaceRelative(absPath) {
  return path.relative(WORKSPACE_ROOT, absPath).replaceAll(path.sep, "/");
}

export function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

export function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

export function writeJson(filePath, value) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(`${filePath}.tmp`, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(`${filePath}.tmp`, filePath);
}

export function findCaseManifest(caseRoot) {
  const manifestDir = path.join(caseRoot, "manifests");
  if (!fs.existsSync(manifestDir)) {
    return null;
  }

  const candidates = fs
    .readdirSync(manifestDir)
    .filter((name) => name.endsWith(".json"))
    .sort();

  for (const name of candidates) {
    const manifestPath = path.join(manifestDir, name);
    try {
      const data = readJson(manifestPath);
      if (data.case_type || data.case_id) {
        return { path: manifestPath, data };
      }
    } catch {
      // Ignore invalid JSON here; check-source reports it separately.
    }
  }

  return null;
}

export function listFiles(root, extensions) {
  if (!fs.existsSync(root)) {
    return [];
  }

  const results = [];
  const stack = [root];
  while (stack.length > 0) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "outputs" || entry.name === ".git") {
          continue;
        }
        stack.push(fullPath);
      } else if (extensions.includes(path.extname(entry.name).toLowerCase())) {
        results.push(fullPath);
      }
    }
  }
  return results.sort();
}

export function copyDir(src, dst) {
  if (!fs.existsSync(src)) {
    return;
  }
  ensureDir(dst);
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, dstPath);
    } else if (entry.isFile()) {
      ensureDir(path.dirname(dstPath));
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

export function safeRemoveInside(parent, target) {
  const resolvedParent = path.resolve(parent);
  const resolvedTarget = path.resolve(target);
  const rel = path.relative(resolvedParent, resolvedTarget);
  if (rel === "" || rel.startsWith("..") || path.isAbsolute(rel)) {
    throw new Error(`Refusing to remove path outside ${resolvedParent}: ${resolvedTarget}`);
  }
  fs.rmSync(resolvedTarget, { recursive: true, force: true });
}

export function caseIdFromManifest(caseRoot, manifest) {
  const raw = manifest?.case_id || path.basename(caseRoot);
  return raw.replace(/[^A-Za-z0-9_.-]+/g, "_");
}

export function assertCaseRoot(caseRoot) {
  if (!fs.existsSync(caseRoot)) {
    throw new Error(`Case does not exist: ${caseRoot}`);
  }
  if (!fs.statSync(caseRoot).isDirectory()) {
    throw new Error(`Case path is not a directory: ${caseRoot}`);
  }
}
