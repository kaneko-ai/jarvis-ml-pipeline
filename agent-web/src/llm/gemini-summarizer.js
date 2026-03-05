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

function createResultWithIssue(paper, issueField, message) {
  return {
    ...paper,
    summary: null,
    [issueField]: message,
  };
}

function isNetworkFetchError(error) {
  if (!error) {
    return false;
  }
  if (error.name === "TypeError") {
    return true;
  }
  const message = String(error.message || "").toLowerCase();
  return message.includes("fetch failed") || message.includes("network");
}

async function summarizeSinglePaper(paper, { apiKey, model, timeoutMs }) {
  if (!apiKey) {
    return createResultWithIssue(paper, "summaryError", "GEMINI_API_KEY is not set.");
  }

  const maxAttempts = 2;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
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

      if (response.ok) {
        const payload = await response.json();
        const summary = extractGeminiText(payload);
        return {
          ...paper,
          summary: summary || null,
        };
      }

      if (response.status === 429) {
        if (attempt < maxAttempts) {
          await sleep(15000);
          continue;
        }
        return createResultWithIssue(
          paper,
          "summaryError",
          "Gemini rate limit (429) persisted after one retry. Skipped."
        );
      }

      if (response.status === 500 || response.status === 503) {
        if (attempt < maxAttempts) {
          await sleep(5000);
          continue;
        }
        return createResultWithIssue(
          paper,
          "summaryError",
          `Gemini server error (${response.status}) persisted after one retry. Skipped.`
        );
      }

      return createResultWithIssue(
        paper,
        "summaryError",
        `Gemini API error: ${response.status} ${response.statusText || "unknown"}`
      );
    } catch (error) {
      if (error?.name === "AbortError") {
        return createResultWithIssue(
          paper,
          "summaryWarning",
          `Gemini request timed out after ${Math.round(timeoutMs / 1000)}s. Skipped.`
        );
      }

      if (isNetworkFetchError(error)) {
        return createResultWithIssue(
          paper,
          "summaryWarning",
          `Network error while calling Gemini: ${error?.message || "fetch failed"}. Skipped.`
        );
      }

      return createResultWithIssue(
        paper,
        "summaryError",
        error?.message || "Summarization failed"
      );
    } finally {
      clearTimeout(timer);
    }
  }

  return createResultWithIssue(paper, "summaryError", "Summarization failed.");
}

export async function summarizeBatch(
  papers,
  { concurrency = 1, delayMs = 4500, onProgress, timeoutMs = 30000 } = {}
) {
  const list = Array.isArray(papers) ? papers : [];
  if (list.length === 0) {
    return [];
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return list.map((paper) =>
      createResultWithIssue(paper, "summaryError", "GEMINI_API_KEY is not set.")
    );
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
        results[index] = createResultWithIssue(
          paper,
          "summaryError",
          error?.message || "Summarization failed"
        );
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

  const workers = Array.from(
    { length: Math.min(safeConcurrency, list.length) },
    () => runWorker()
  );
  await Promise.all(workers);
  return results;
}

