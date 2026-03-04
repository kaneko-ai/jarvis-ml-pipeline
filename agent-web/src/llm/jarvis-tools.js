import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");
const PYTHON_EXE = path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe");

function callJarvisCLI(command, args = []) {
  const normalizedArgs = Array.isArray(args)
    ? args
    : String(args)
        .split(" ")
        .filter(Boolean);

  return new Promise((resolve, reject) => {
    const fullArgs = ["-m", "jarvis_cli", command, ...normalizedArgs];
    const proc = spawn(PYTHON_EXE, fullArgs, {
      cwd: PROJECT_ROOT,
      env: { ...process.env, PYTHONPATH: PROJECT_ROOT },
    });

    let stdout = "";
    let stderr = "";
    const timeout = setTimeout(() => {
      proc.kill();
      reject(new Error("CLI timed out after 120s"));
    }, 120000);

    proc.stdout.on("data", (data) => {
      stdout += data.toString("utf8");
    });
    proc.stderr.on("data", (data) => {
      stderr += data.toString("utf8");
    });
    proc.on("error", (error) => {
      clearTimeout(timeout);
      reject(error);
    });

    proc.on("close", (code) => {
      clearTimeout(timeout);
      resolve({ code, stdout, stderr });
    });
  });
}

export async function searchPapers(query, max = 5) {
  return callJarvisCLI("search", [query, "--max", String(max), "--sources", "pubmed,s2"]);
}

export async function semanticSearch(query, top = 5) {
  return callJarvisCLI("semantic-search", [query, "--top", String(top)]);
}

export async function browsePage(url) {
  return callJarvisCLI("browse", [url, "--json"]);
}

export async function evidenceGrade(filePath) {
  return callJarvisCLI("evidence", [filePath]);
}
