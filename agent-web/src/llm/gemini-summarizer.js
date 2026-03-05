const GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function extractGeminiText(payload) {
  const parts = payload?.candidates?.[0]?.content?.parts;
  if (!Array.isArray(parts)) {
    return "";
  }

  return parts
    .map((part) => (typeof part?.text === "string" ? part.text : ""))
    .join("\n")
    .trim();
}

function buildPrompt(paper) {
  const title = paper?.title || "(no title)";
  const authors = paper?.authors || "Unknown";
  const journal = paper?.journal || paper?.source || "Unknown";
  const year = paper?.year || "Unknown";
  const abstractText = paper?.abstract || paper?.snippet || "";

  return [
    "Summarize this research paper in 3-4 concise sentences for a literature review dashboard.",
    "Focus on objective, method, and key finding. Keep it factual and avoid hype.",
    "",
    `Title: ${title}`,
    `Authors: ${authors}`,
    `Journal/Source: ${journal}`,
    `Year: ${year}`,
    abstractText ? `Abstract: ${abstractText}` : "Abstract: (not provided)",
  ].join("\n");
}

async function summarizeSinglePaper(paper, { apiKey, model, timeoutMs }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(
      `${GEMINI_API_BASE}/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(apiKey)}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contents: [
            {
              role: "user",
              parts: [{ text: buildPrompt(paper) }],
            },
          ],
          generationConfig: {
            temperature: 0.2,
            maxOutputTokens: 220,
          },
        }),
        signal: controller.signal,
      }
    );

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status} ${response.statusText}`);
    }

    const payload = await response.json();
    const summary = extractGeminiText(payload);
    return {
      ...paper,
      summary: summary || null,
    };
  } finally {
    clearTimeout(timer);
  }
}

export async function summarizeBatch(papers, { concurrency = 2, delayMs = 1000, onProgress, timeoutMs = 30000 } = {}) {
  const list = Array.isArray(papers) ? papers : [];
  if (list.length === 0) {
    return [];
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error("GEMINI_API_KEY is not set.");
  }

  const model = String(process.env.GEMINI_MODEL || "gemini-2.0-flash").trim();
  const safeConcurrency = Math.min(Math.max(Number(concurrency) || 1, 1), 8);
  const safeDelayMs = Math.max(0, Number(delayMs) || 0);
  const safeTimeoutMs = Math.max(1000, Number(timeoutMs) || 30000);
  const progressHandler = typeof onProgress === "function" ? onProgress : null;

  const results = new Array(list.length);
  let nextIndex = 0;
  let completed = 0;

  async function runWorker() {
    while (true) {
      const index = nextIndex;
      if (index >= list.length) {
        return;
      }
      nextIndex += 1;

      const paper = list[index];
      try {
        results[index] = await summarizeSinglePaper(paper, {
          apiKey,
          model,
          timeoutMs: safeTimeoutMs,
        });
      } catch (error) {
        results[index] = {
          ...paper,
          summary: null,
          summaryError: error?.message || "Summarization failed",
        };
      }

      completed += 1;
      if (progressHandler) {
        try {
          progressHandler({
            current: completed,
            total: list.length,
            index: index + 1,
            paper: results[index],
          });
        } catch {
          // Ignore progress callback errors to keep batch processing stable.
        }
      }

      if (safeDelayMs > 0 && completed < list.length) {
        await sleep(safeDelayMs);
      }
    }
  }

  const workers = Array.from({ length: Math.min(safeConcurrency, list.length) }, () => runWorker());
  await Promise.all(workers);
  return results;
}
