import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const SCRIPT_ROOT = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.resolve(SCRIPT_ROOT, "..");
export const DEFAULT_SOURCE_ROOT = path.join(REPO_ROOT, "distribution", "public-preview");
export const DEFAULT_TARGET_ROOT = path.resolve(REPO_ROOT, "..", "Academic_Research_Workflow_Agents_Preview");
export const CONTROL_FILE = ".public-preview-allowlist.json";
export const SYNC_MANIFEST_FILE = ".preview-sync-manifest.json";

function sha256Buffer(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function sha256File(filePath) {
  return sha256Buffer(fs.readFileSync(filePath));
}

function normalizeRelativePath(value) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error("Preview allowlist entries must be non-empty strings.");
  }
  const normalized = value.replaceAll("\\", "/");
  if (path.posix.isAbsolute(normalized) || normalized.startsWith("../") || normalized.includes("/../") || normalized === "..") {
    throw new Error(`Preview path escapes the source root: ${value}`);
  }
  if (normalized === CONTROL_FILE || normalized === SYNC_MANIFEST_FILE) {
    throw new Error(`Generated control files cannot be allowlisted: ${normalized}`);
  }
  return normalized;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJsonAtomic(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const temporary = `${filePath}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(temporary, filePath);
}

function runGit(targetRoot, args, { allowFailure = false } = {}) {
  const result = spawnSync("git", ["-C", targetRoot, ...args], {
    encoding: "utf8",
    shell: false,
  });
  if (!allowFailure && (result.status ?? 1) !== 0) {
    throw new Error(`git ${args.join(" ")} failed: ${result.stderr || result.stdout}`);
  }
  return result;
}

function assertTargetRepository(targetRoot, { skipRemoteCheck = false } = {}) {
  if (!fs.existsSync(path.join(targetRoot, ".git"))) {
    throw new Error(`Preview target is not a Git repository: ${targetRoot}`);
  }
  if (!skipRemoteCheck) {
    const remote = runGit(targetRoot, ["config", "--get", "remote.origin.url"]).stdout.trim();
    if (!/academic-research-workflow-agents[\\/]agents-preview(?:\.git)?$/i.test(remote)) {
      throw new Error(`Refusing unexpected preview remote: ${remote || "<missing>"}`);
    }
  }
}

function trackedFiles(targetRoot) {
  const output = runGit(targetRoot, ["ls-files", "-z"]).stdout;
  return new Set(output.split("\0").filter(Boolean).map((item) => item.replaceAll("\\", "/")));
}

export function buildPreviewSourceState({ sourceRoot = DEFAULT_SOURCE_ROOT, repoRoot = REPO_ROOT } = {}) {
  const controlPath = path.join(sourceRoot, CONTROL_FILE);
  if (!fs.existsSync(controlPath)) {
    throw new Error(`Missing preview allowlist: ${controlPath}`);
  }
  const control = readJson(controlPath);
  if (control.schema_version !== 1 || control.product !== "Academic Research Assistant AI Agents") {
    throw new Error("Invalid public preview allowlist metadata.");
  }
  const repoVersion = fs.readFileSync(path.join(repoRoot, "VERSION.txt"), "utf8").trim();
  if (control.version !== repoVersion) {
    throw new Error(`Preview version ${control.version} does not match private version ${repoVersion}.`);
  }

  const seen = new Set();
  const files = [];
  for (const rawPath of control.files || []) {
    const relativePath = normalizeRelativePath(rawPath);
    if (seen.has(relativePath)) throw new Error(`Duplicate preview allowlist path: ${relativePath}`);
    seen.add(relativePath);
    const sourcePath = path.resolve(sourceRoot, ...relativePath.split("/"));
    const relativeCheck = path.relative(path.resolve(sourceRoot), sourcePath);
    if (relativeCheck.startsWith("..") || path.isAbsolute(relativeCheck)) {
      throw new Error(`Preview path escapes the source root: ${relativePath}`);
    }
    if (!fs.existsSync(sourcePath) || !fs.statSync(sourcePath).isFile()) {
      throw new Error(`Allowlisted preview file is missing: ${relativePath}`);
    }
    if (fs.lstatSync(sourcePath).isSymbolicLink()) {
      throw new Error(`Symbolic links are not allowed in public preview: ${relativePath}`);
    }
    files.push({ path: relativePath, sha256: sha256File(sourcePath), sourcePath });
  }
  files.sort((a, b) => a.path.localeCompare(b.path));
  const sourceTreeHash = sha256Buffer(files.map((file) => `${file.path}\0${file.sha256}\n`).join(""));
  const manifest = {
    schema_version: 1,
    product: control.product,
    version: control.version,
    source_tree_hash: sourceTreeHash,
    files: files.map(({ path: filePath, sha256 }) => ({ path: filePath, sha256 })),
  };
  return { control, files, manifest, sourceRoot };
}

export function planPreviewSync({
  sourceRoot = DEFAULT_SOURCE_ROOT,
  targetRoot = DEFAULT_TARGET_ROOT,
  repoRoot = REPO_ROOT,
  skipRemoteCheck = false,
  check = false,
} = {}) {
  const resolvedTarget = path.resolve(targetRoot);
  assertTargetRepository(resolvedTarget, { skipRemoteCheck });
  const sourceState = buildPreviewSourceState({ sourceRoot, repoRoot });
  const tracked = trackedFiles(resolvedTarget);
  const desired = new Set(sourceState.files.map((file) => file.path));
  desired.add(SYNC_MANIFEST_FILE);

  const manifestPath = path.join(resolvedTarget, SYNC_MANIFEST_FILE);
  let previousManifest = null;
  if (fs.existsSync(manifestPath)) {
    try {
      const candidate = readJson(manifestPath);
      if (candidate.schema_version === 1 && candidate.product === sourceState.manifest.product && Array.isArray(candidate.files)) {
        previousManifest = candidate;
      }
    } catch {
      previousManifest = null;
    }
  }
  const previousManagedHashes = new Map((previousManifest?.files || []).map((file) => [file.path, file.sha256]));
  if (previousManifest) {
    previousManagedHashes.set(SYNC_MANIFEST_FILE, sha256Buffer(`${JSON.stringify(previousManifest, null, 2)}\n`));
  }

  if (!check) {
    const staged = runGit(resolvedTarget, ["diff", "--cached", "--quiet"], { allowFailure: true });
    if (staged.status !== 0) {
      throw new Error("Preview target has staged changes; commit or restore them before synchronization.");
    }
    const unstaged = runGit(resolvedTarget, ["diff", "--quiet"], { allowFailure: true });
    if (unstaged.status !== 0) {
      if (!previousManifest) {
        throw new Error("Preview target has tracked changes; commit or restore them before synchronization.");
      }
      for (const trackedPath of tracked) {
        const targetPath = path.join(resolvedTarget, ...trackedPath.split("/"));
        const previousHash = previousManagedHashes.get(trackedPath);
        if (previousHash) {
          if (!fs.existsSync(targetPath) || sha256File(targetPath) !== previousHash) {
            throw new Error(`Preview target has an unmanaged tracked change: ${trackedPath}`);
          }
        } else if (fs.existsSync(targetPath)) {
          throw new Error(`Preview target has an unmanaged tracked change: ${trackedPath}`);
        }
      }
    }
  }

  const removals = [...tracked]
    .filter((filePath) => !desired.has(filePath))
    .filter((filePath) => fs.existsSync(path.join(resolvedTarget, ...filePath.split("/"))))
    .sort();
  const copies = [];
  for (const file of sourceState.files) {
    const targetPath = path.join(resolvedTarget, ...file.path.split("/"));
    if (fs.existsSync(targetPath) && !tracked.has(file.path)) {
      const currentHash = sha256File(targetPath);
      if (currentHash === file.sha256) {
        continue;
      }
      if (previousManagedHashes.get(file.path) !== currentHash) {
        throw new Error(`Refusing to overwrite untracked preview file: ${file.path}`);
      }
      copies.push(file.path);
      continue;
    }
    if (!fs.existsSync(targetPath) || sha256File(targetPath) !== file.sha256) {
      copies.push(file.path);
    }
  }

  const expectedManifest = `${JSON.stringify(sourceState.manifest, null, 2)}\n`;
  if (fs.existsSync(manifestPath) && !tracked.has(SYNC_MANIFEST_FILE) && fs.readFileSync(manifestPath, "utf8") !== expectedManifest && !previousManifest) {
    throw new Error(`Refusing to overwrite untracked preview file: ${SYNC_MANIFEST_FILE}`);
  }
  const manifestChanged = !fs.existsSync(manifestPath) || fs.readFileSync(manifestPath, "utf8") !== expectedManifest;

  return {
    sourceState,
    targetRoot: resolvedTarget,
    removals,
    copies,
    manifestChanged,
    inSync: removals.length === 0 && copies.length === 0 && !manifestChanged,
  };
}

export function syncPublicPreview(options = {}) {
  const plan = planPreviewSync(options);
  const dryRun = options.dryRun === true || options.check === true;
  if (!dryRun) {
    for (const relativePath of plan.removals) {
      const targetPath = path.join(plan.targetRoot, ...relativePath.split("/"));
      if (fs.existsSync(targetPath)) fs.rmSync(targetPath, { force: true });
    }
    for (const relativePath of plan.copies) {
      const file = plan.sourceState.files.find((candidate) => candidate.path === relativePath);
      const targetPath = path.join(plan.targetRoot, ...relativePath.split("/"));
      fs.mkdirSync(path.dirname(targetPath), { recursive: true });
      fs.copyFileSync(file.sourcePath, targetPath);
    }
    if (plan.manifestChanged) {
      writeJsonAtomic(path.join(plan.targetRoot, SYNC_MANIFEST_FILE), plan.sourceState.manifest);
    }
  }
  return {
    status: plan.inSync ? "in_sync" : dryRun ? "drift" : "synchronized",
    target: plan.targetRoot,
    version: plan.sourceState.manifest.version,
    source_tree_hash: plan.sourceState.manifest.source_tree_hash,
    copies: plan.copies,
    removals: plan.removals,
    manifest_changed: plan.manifestChanged,
  };
}
