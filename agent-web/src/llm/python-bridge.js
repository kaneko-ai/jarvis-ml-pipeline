import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PYTHON_SCRIPT = path.join(__dirname, "llm_caller.py");
const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");
const PYTHON_EXE = path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe");

export function callLLM({ message, model = "gemini/gemini-2.0-flash", history = [] }) {
  return new Promise((resolve, reject) => {
    const proc = spawn(PYTHON_EXE, [PYTHON_SCRIPT], {
      cwd: PROJECT_ROOT,
      env: { ...process.env, PYTHONPATH: PROJECT_ROOT },
    });

    let stdout = "";
    let stderr = "";
    const timeout = setTimeout(() => {
      proc.kill();
      reject(new Error("LLM call timed out after 60s"));
    }, 60000);

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
      if (code !== 0) {
        reject(new Error(`Python error: ${stderr || stdout}`));
        return;
      }

      try {
        const cleaned = stdout.replace(/^\uFEFF/, "").trim();
        const lines = cleaned.split("\n").filter(Boolean);
        const lastLine = lines[lines.length - 1];
        const result = JSON.parse(lastLine);
        resolve(result);
      } catch {
        reject(new Error(`Parse error: ${stdout}`));
      }
    });

    proc.stdin.write(JSON.stringify({ message, model, history }));
    proc.stdin.end();
  });
}
