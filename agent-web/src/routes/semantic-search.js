import { Router } from "express";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.join(__dirname, "..", "..", "..");

const router = Router();

function runPythonSearch(query, topK = 10) {
  return new Promise((resolve, reject) => {
    const scriptContent = `
import sys, json
try:
    from jarvis_core.chroma_manager import ChromaManager
    cm = ChromaManager()
    results = cm.search(sys.argv[1], n_results=int(sys.argv[2]))
    docs = results.get('documents', [[]])[0] if results else []
    metadatas = results.get('metadatas', [[]])[0] if results else []
    distances = results.get('distances', [[]])[0] if results else []
    output = []
    for i, doc in enumerate(docs):
        meta = metadatas[i] if i < len(metadatas) else {}
        dist = distances[i] if i < len(distances) else 1.0
        output.append({
            'text': doc[:500],
            'title': meta.get('title', ''),
            'authors': meta.get('authors', ''),
            'year': meta.get('year', ''),
            'doi': meta.get('doi', ''),
            'source': meta.get('source', 'chromadb'),
            'similarity': round(1.0 - float(dist), 4) if dist else 0
        })
    print(json.dumps(output))
except Exception as e:
    print(json.dumps({'error': str(e)}))
`;

    const py = spawn("python", ["-c", scriptContent, query, String(topK)], {
      cwd: PROJECT_ROOT,
      timeout: 30000,
      env: { ...process.env },
    });

    let stdout = "";
    let stderr = "";
    py.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    py.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    py.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Python exited with code ${code}: ${stderr.slice(0, 500)}`));
        return;
      }

      try {
        const parsed = JSON.parse(stdout.trim());
        if (parsed.error) {
          reject(new Error(parsed.error));
          return;
        }
        resolve(Array.isArray(parsed) ? parsed : []);
      } catch {
        reject(new Error("Failed to parse Python output"));
      }
    });

    py.on("error", (error) => reject(error));
  });
}

router.get("/", async (req, res) => {
  const query = String(req.query.query || "").trim();
  const limit = Math.min(Math.max(Number(req.query.limit) || 10, 1), 50);

  if (!query) {
    return res.status(400).json({ error: "query parameter is required" });
  }

  try {
    const results = await runPythonSearch(query, limit);
    return res.json({ query, results, total: results.length, searchType: "semantic" });
  } catch (error) {
    console.error("[SemanticSearch] Error:", error.message);
    return res.json({
      query,
      results: [],
      total: 0,
      searchType: "semantic",
      error: error.message,
      hint: "ChromaDB may not be available. Ensure Python venv is activated and jarvis_core is installed.",
    });
  }
});

export default router;