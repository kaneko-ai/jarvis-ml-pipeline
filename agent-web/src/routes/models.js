import express from "express";
import { listCopilotModels } from "../llm/copilot-bridge.js";

const router = express.Router();

// Models confirmed to work on Copilot Pro (student free tier)
const PRO_COMPATIBLE = new Set([
  "gpt-4.1",
  "gpt-4.1-mini",
  "gpt-4o",
  "gpt-4o-2024-07-18",
  "gpt-4o-2024-08-06",
  "gpt-4o-2024-11-20",
  "gpt-5-mini",
  "claude-sonnet-4",
  "claude-sonnet-4.5",
  "claude-sonnet-4.6",
  "claude-haiku-4.5",
  "o4-mini",
  "o3-mini",
  "gemini-2.0-flash",
  "gemini-2.5-pro",
]);

// Models that need Pro+ ($39/mo) - show but mark as restricted
const PRO_PLUS_ONLY = new Set([
  "claude-opus-4.6-fast",
  "claude-opus-4.6",
  "claude-opus-4.5",
  "gpt-5.1",
  "gpt-5.1-codex",
  "gpt-5.1-codex-mini",
  "gpt-5.1-codex-max",
  "gpt-5.2-codex",
  "gpt-5.3-codex",
  "gemini-3-pro-preview",
  "gemini-3-flash-preview",
  "gemini-3.1-pro-preview",
]);

function getProviderName(modelId) {
  if (modelId.includes("claude")) return "Anthropic";
  if (modelId.includes("gpt") || modelId.includes("o4") || modelId.includes("o3")) return "OpenAI";
  if (modelId.includes("gemini")) return "Google";
  if (modelId.includes("grok")) return "xAI";
  return "Other";
}

const STATIC_MODELS = [
  { id: "claude-sonnet-4.6", name: "Claude Sonnet 4.6", provider: "Anthropic", default: true, tier: "pro" },
  { id: "gpt-4.1", name: "GPT-4.1", provider: "OpenAI", default: false, tier: "pro" },
  { id: "o4-mini", name: "o4-mini (Reasoning)", provider: "OpenAI", default: false, tier: "pro" },
  { id: "gemini/gemini-2.0-flash", name: "Gemini 2.0 Flash (LiteLLM)", provider: "LiteLLM", default: false, tier: "local" },
];

router.get("/", async (req, res) => {
  try {
    const copilotModels = await listCopilotModels();
    if (copilotModels.length > 0) {
      const chatModels = copilotModels.filter(m =>
        !m.id.includes("embedding") && !m.id.includes("oswe-vscode")
      );

      const models = chatModels.map(m => {
        const id = m.id;
        let tier = "unknown";
        let restricted = false;
        
        if (PRO_COMPATIBLE.has(id)) {
          tier = "pro";
        } else if (PRO_PLUS_ONLY.has(id)) {
          tier = "pro+";
          restricted = true;
        } else {
          // Unknown model - try it but mark as uncertain
          tier = "unknown";
        }

        return {
          id: id,
          name: restricted ? `${id} (Pro+ required)` : id,
          provider: getProviderName(id),
          default: id === "claude-sonnet-4.6",
          tier: tier,
          restricted: restricted
        };
      });

      // Sort: pro models first (compatible), then pro+ (restricted), then unknown
      models.sort((a, b) => {
        const order = { pro: 0, unknown: 1, "pro+": 2 };
        return (order[a.tier] || 1) - (order[b.tier] || 1);
      });

      // Add LiteLLM fallback
      models.push({
        id: "gemini/gemini-2.0-flash",
        name: "Gemini 2.0 Flash (LiteLLM Local)",
        provider: "LiteLLM",
        default: false,
        tier: "local",
        restricted: false
      });

      return res.json(models);
    }
  } catch (e) {
    // copilot-api not running
  }
  res.json(STATIC_MODELS);
});

export default router;
