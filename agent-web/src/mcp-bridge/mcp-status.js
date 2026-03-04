import fs from "fs";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");
const PYTHON_EXE = path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe");

const MCP_SERVERS = [
  { name: "pubmed", tools: ["pubmed_search", "pubmed_fetch", "pubmed_citations"], status: "available" },
  { name: "openalex", tools: ["openalex_search", "openalex_work", "openalex_author", "openalex_institution"], status: "available" },
  { name: "semantic_scholar", tools: ["s2_search", "s2_paper", "s2_citations", "s2_references"], status: "available" },
  { name: "arxiv", tools: ["arxiv_search", "arxiv_fetch"], status: "available" },
  { name: "crossref", tools: ["crossref_search", "crossref_doi"], status: "available" }
];

export function getMCPServers() {
  return MCP_SERVERS;
}

export function getMCPTools() {
  return MCP_SERVERS.flatMap((s) => s.tools.map((t) => ({ server: s.name, tool: t })));
}

export async function invokeMCPTool(tool, params) {
  return new Promise((resolve, reject) => {
    const args = ["-m", "jarvis_cli", "mcp", "invoke", tool];
    if (params) {
      const tmpFile = path.join(PROJECT_ROOT, "agent-web", "tmp_mcp_params.json");
      fs.writeFileSync(tmpFile, JSON.stringify(params));
      args.push("--params-file", tmpFile);
    }

    const proc = spawn(PYTHON_EXE, args, {
      cwd: PROJECT_ROOT,
      env: { ...process.env, PYTHONPATH: PROJECT_ROOT }
    });

    let stdout = "";
    let stderr = "";
    const timeout = setTimeout(() => {
      proc.kill();
      reject(new Error("MCP timeout"));
    }, 60000);

    proc.stdout.on("data", (d) => { stdout += d.toString(); });
    proc.stderr.on("data", (d) => { stderr += d.toString(); });
    proc.on("close", (code) => {
      clearTimeout(timeout);
      resolve({ code, stdout, stderr });
    });
  });
}
