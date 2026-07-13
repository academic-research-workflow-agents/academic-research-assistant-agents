import path from "node:path";
import { fileURLToPath } from "node:url";
import { DEFAULT_TARGET_ROOT, syncPublicPreview } from "./public-preview-lib.mjs";

function parseArgs(argv) {
  const options = { targetRoot: DEFAULT_TARGET_ROOT, check: false, dryRun: false };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--target") {
      if (!argv[index + 1]) throw new Error("Missing value for --target.");
      options.targetRoot = path.resolve(argv[index + 1]);
      index += 1;
    } else if (arg === "--check") {
      options.check = true;
    } else if (arg === "--dry-run") {
      options.dryRun = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (options.check && options.dryRun) throw new Error("Use either --check or --dry-run, not both.");
  return options;
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  try {
    const options = parseArgs(process.argv.slice(2));
    const result = syncPublicPreview(options);
    console.log(JSON.stringify(result, null, 2));
    if (options.check && result.status !== "in_sync") process.exitCode = 1;
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
