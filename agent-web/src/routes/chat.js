import express from "express";
import { addMessage, createSession, getMessages } from "../db/database.js";
import { callCopilotLLMStream, callCopilotLLM } from "../llm/copilot-bridge.js";

let callPythonLLM;
try {
  const pythonBridge = await import("../llm/python-bridge.js");
  callPythonLLM = pythonBridge.callLLM;
} catch (e) {
  callPythonLLM = null;
}

let jarvisTools;
try {
  jarvisTools = await import("../llm/jarvis-tools.js");
} catch (e) {
  jarvisTools = null;
}

const router = express.Router();

function sendSSE(res, event, data) {
  res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const RESEARCH_KEYWORDS = [
  "\u691c\u7d22",
  "\u8abf\u3079",
  "\u8ad6\u6587",
  "search",
  "PD-1",
  "spermidine",
  "autophagy",
  "immunotherapy",
  "\u30e1\u30bf\u5206\u6790",
  "paper",
  "research",
  "\u514d\u75ab",
  "\u30aa\u30fc\u30c8\u30d5\u30a1\u30b8\u30fc",
  "\u30b9\u30da\u30eb\u30df\u30b8\u30f3",
];

const MAX_HISTORY_MESSAGES = 20;

function isResearchQuery(message) {
  const lower = message.toLowerCase();
  return RESEARCH_KEYWORDS.some((kw) => lower.includes(kw.toLowerCase()));
}

function isLiteLLMModel(model) {
  return model && model.includes("/") && !model.startsWith("[copilot]");
}function buildHistory(sessionId) {
  if (!sessionId) return [];
  try {
    const allMsgs = getMessages(sessionId);
    const relevant = allMsgs
      .filter(m => m.role === "user" || m.role === "assistant")
      .slice(-MAX_HISTORY_MESSAGES)
      .map(m => ({ role: m.role, content: m.content }));
    return relevant;
  } catch (e) {
    console.error("buildHistory error:", e.message);
    return [];
  }
}

router.post("/stream", async (req, res) => {
  let { sessionId, message, model } = req.body;

  if (!message) {
    return res.status(400).json({ error: "message is required" });
  }

  model = model || "claude-sonnet-4.6";

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders();

  try {
    if (!sessionId) {
      const session = createSession(message.substring(0, 50), model);
      sessionId = session.id;
    }
    sendSSE(res, "session", { sessionId });
    addMessage(sessionId, "user", message, null, null);

    const startTime = Date.now();

    sendSSE(res, "activity", { step: "thinking", status: "running" });
    await delay(100);
    sendSSE(res, "activity", { step: "thinking", status: "done", time: `${Date.now() - startTime}ms` });

    let augmentedMessage = message;
    const usedTools = [];
    let browseContent = "";
    let searchContent = "";

    // --- URL Detection (ALWAYS, independent of research keywords) ---
    const urlMatch = message.match(/(https?:\/\/[^\s]+)/);
    if (urlMatch && jarvisTools) {
      const browseStart = Date.now();
      sendSSE(res, "activity", { step: "browse_url", status: "running" });
      try {
        const browseResult = await jarvisTools.browsePage(urlMatch[1]);
        const browseTime = Date.now() - browseStart;
        if (browseResult.stdout && browseResult.stdout.trim()) {
          browseContent = browseResult.stdout.replace(/[\uD800-\uDFFF]/g, "").substring(0, 1500);
          sendSSE(res, "activity", { step: "browse_url", status: "done", time: `${browseTime}ms` });
          sendSSE(res, "tool_call", { name: "browse_url", result: browseContent.substring(0, 300) });
          usedTools.push({ name: "browse_url", result: browseContent.substring(0, 300) });
        } else {
          sendSSE(res, "activity", { step: "browse_url", status: "error", time: `${browseTime}ms` });
          sendSSE(res, "warning", { message: "URL\u306e\u53d6\u5f97\u306b\u5931\u6557\u3057\u307e\u3057\u305f\u3002LLM\u306e\u307f\u3067\u56de\u7b54\u3057\u307e\u3059\u3002" });
        }
      } catch (browseErr) {
        const browseTime = Date.now() - browseStart;
        sendSSE(res, "activity", { step: "browse_url", status: "error", time: `${browseTime}ms` });
        sendSSE(res, "warning", { message: `URL\u53d6\u5f97\u30a8\u30e9\u30fc: ${browseErr.message}\u3002LLM\u306e\u307f\u3067\u56de\u7b54\u3057\u307e\u3059\u3002` });
      }
    }

    // --- Research Mode (semantic search) ---
    if (isResearchQuery(message) && jarvisTools) {
      const searchStart = Date.now();
      sendSSE(res, "activity", { step: "semantic_search", status: "running" });
      try {
        const searchResult = await jarvisTools.semanticSearch(message, 3);
        const searchTime = Date.now() - searchStart;
        sendSSE(res, "activity", { step: "semantic_search", status: "done", time: `${searchTime}ms` });
        if (searchResult.stdout && searchResult.stdout.trim()) {
          searchContent = searchResult.stdout.replace(/[\uD800-\uDFFF]/g, "").substring(0, 2000);
          sendSSE(res, "tool_call", { name: "semantic_search", result: searchContent.substring(0, 500) });
          usedTools.push({ name: "semantic_search", result: searchContent.substring(0, 500) });
        }
      } catch (searchErr) {
        sendSSE(res, "activity", { step: "semantic_search", status: "error", time: `${Date.now() - searchStart}ms` });
      }

      if (message.match(/\u30a8\u30d3\u30c7\u30f3\u30b9|evidence|grade|CEBM|\u30ec\u30d9\u30eb/i) && jarvisTools) {
        sendSSE(res, "activity", { step: "evidence_grade", status: "running" });
        sendSSE(res, "activity", { step: "evidence_grade", status: "skipped", time: "N/A (requires file)" });
      }
    }

    // --- Build augmented prompt ---
    if (browseContent && searchContent) {
      augmentedMessage = `\u4ee5\u4e0b\u306e\u60c5\u5831\u3092\u53c2\u8003\u306b\u3057\u3066\u56de\u7b54\u3057\u3066\u304f\u3060\u3055\u3044:\n\nURL\u5185\u5bb9:\n${browseContent}\n\n\u95a2\u9023\u8ad6\u6587:\n${searchContent}\n\n\u30e6\u30fc\u30b6\u30fc\u306e\u8cea\u554f: ${message}`;
    } else if (browseContent) {
      augmentedMessage = `\u4ee5\u4e0b\u306eURL\u306e\u5185\u5bb9\u3092\u53c2\u8003\u306b\u3057\u3066\u56de\u7b54\u3057\u3066\u304f\u3060\u3055\u3044:\n${browseContent}\n\n\u30e6\u30fc\u30b6\u30fc\u306e\u8cea\u554f: ${message}`;
    } else if (searchContent) {
      augmentedMessage = `\u4ee5\u4e0b\u306e\u95a2\u9023\u8ad6\u6587\u60c5\u5831\u3092\u53c2\u8003\u306b\u3057\u3066\u56de\u7b54\u3057\u3066\u304f\u3060\u3055\u3044:\n${searchContent}\n\n\u30e6\u30fc\u30b6\u30fc\u306e\u8cea\u554f: ${message}`;
    }

    // --- Generate LLM Response ---
    const genStart = Date.now();
    sendSSE(res, "activity", { step: "generate_response", status: "running" });

    let fullContent = "";
    let usedModel = model;
    let usedProvider = isLiteLLMModel(model) ? "litellm" : "copilot";
    const cleanMessage = augmentedMessage.replace(/[\uD800-\uDFFF]/g, "");

    if (isLiteLLMModel(model)) {
      if (callPythonLLM) {
        try {
          const pyResult = await callPythonLLM({ message: cleanMessage, model });
          if (pyResult.success) {
            fullContent = pyResult.content;
            for (const char of fullContent) {
              sendSSE(res, "delta", { content: char });
              await delay(10);
            }
          } else {
            throw new Error(pyResult.error);
          }
        } catch (pyErr) {
          sendSSE(res, "error", { message: `LiteLLM error: ${pyErr.message}` });
          sendSSE(res, "activity", { step: "generate_response", status: "error", time: `${Date.now() - genStart}ms` });
          res.end();
          return;
        }
      } else {
        sendSSE(res, "error", { message: "LiteLLM Python bridge not available" });
        res.end();
        return;
      }
    } else {
      try {
        const history = buildHistory(sessionId);
        const stream = await callCopilotLLMStream({ message: cleanMessage, model, history });
        const reader = stream.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim();
              if (data === "[DONE]") continue;
              try {
                const parsed = JSON.parse(data);
                const delta = parsed.choices?.[0]?.delta?.content || "";
                if (delta) {
                  fullContent += delta;
                  sendSSE(res, "delta", { content: delta });
                }
              } catch (e) {
                // skip
              }
            }
          }
        }
      } catch (streamErr) {
        // Streaming failed — try non-streaming fallback
        try {
          const result = await callCopilotLLM({ message: cleanMessage, model });
          if (result.success && result.content) {
            fullContent = result.content;
            for (const char of fullContent) {
              sendSSE(res, "delta", { content: char });
              await delay(10);
            }
          } else {
            throw new Error(result.error || "Empty response");
          }
        } catch (nonStreamErr) {
          // Both streaming and non-streaming failed
          const isTimeout = nonStreamErr.name === "AbortError" || nonStreamErr.message.includes("abort");
          const errMsg = isTimeout
            ? `\u30e2\u30c7\u30eb "${model}" \u304c\u5fdc\u7b54\u30bf\u30a4\u30e0\u30a2\u30a6\u30c8\u3057\u307e\u3057\u305f\u3002\u5225\u306e\u30e2\u30c7\u30eb\u3092\u8a66\u3059\u304b\u3001"Gemini 2.0 Flash (LiteLLM)" \u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002`
            : `Copilot API error for model "${model}": ${nonStreamErr.message}. Try a different model or select "Gemini 2.0 Flash (LiteLLM)" from the dropdown.`;
          sendSSE(res, "error", { message: errMsg });
          sendSSE(res, "activity", { step: "generate_response", status: "error", time: `${Date.now() - genStart}ms` });
          res.end();
          return;
        }
      }
    }

    if (!fullContent) {
      sendSSE(res, "error", { message: `No response from ${model}. Try another model.` });
      sendSSE(res, "activity", { step: "generate_response", status: "error", time: `${Date.now() - genStart}ms` });
      res.end();
      return;
    }

    const genTime = Date.now() - genStart;
    sendSSE(res, "activity", { step: "generate_response", status: "done", time: `${genTime}ms` });
    sendSSE(res, "done", { fullContent, model: `${usedModel} (${usedProvider})` });

    const activityLog = [
      { step: "thinking", status: "done" },
      ...(usedTools.some(t => t.name === "browse_url") ? [{ step: "browse_url", status: "done" }] : []),
      ...(usedTools.some(t => t.name === "semantic_search") ? [{ step: "semantic_search", status: "done" }] : []),
      { step: "generate_response", status: "done", time: `${genTime}ms`, provider: usedProvider, model: usedModel }
    ];
    addMessage(sessionId, "assistant", fullContent, activityLog, usedTools.length ? usedTools : null);
  } catch (err) {
    sendSSE(res, "error", { message: err.message || "Unknown error" });
  }

  res.end();
});

export default router;
