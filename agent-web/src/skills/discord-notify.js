import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.join(__dirname, "..", "..", "..");

dotenv.config({ path: path.join(PROJECT_ROOT, ".env") });

const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL || "";

export function isDiscordConfigured() {
  return Boolean(
    WEBHOOK_URL && WEBHOOK_URL.startsWith("https://discord.com/api/webhooks/")
  );
}

export async function sendDiscordNotification({
  title,
  description,
  fields = [],
  color = 0xd4af37,
  url = "",
}) {
  if (!isDiscordConfigured()) {
    console.warn("[Discord] DISCORD_WEBHOOK_URL not configured, skipping notification");
    return { sent: false, reason: "not_configured" };
  }

  const embed = {
    title: String(title).slice(0, 256),
    description: String(description).slice(0, 4096),
    color,
    timestamp: new Date().toISOString(),
    footer: { text: "JARVIS Research OS" },
  };

  if (url) {
    embed.url = url;
  }

  if (fields.length > 0) {
    embed.fields = fields.slice(0, 25).map((field) => ({
      name: String(field.name).slice(0, 256),
      value: String(field.value).slice(0, 1024),
      inline: Boolean(field.inline),
    }));
  }

  const body = JSON.stringify({
    username: "JARVIS Research OS",
    embeds: [embed],
  });

  try {
    const response = await fetch(WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      console.error(`[Discord] Webhook failed: ${response.status} ${text}`);
      return { sent: false, reason: `http_${response.status}` };
    }

    console.log("[Discord] Notification sent successfully");
    return { sent: true };
  } catch (error) {
    console.error("[Discord] Webhook error:", error.message);
    return { sent: false, reason: error.message };
  }
}

export async function notifyDigestComplete(payload) {
  const {
    date,
    keywordCounts = [],
    totalDeduped = 0,
    topPapers = [],
  } = payload || {};

  const keywordSummary = keywordCounts
    .map((keywordCount) => `${keywordCount.keyword}: ${keywordCount.count}`)
    .join(", ");
  const topTitles = topPapers
    .slice(0, 3)
    .map((paper, index) => `${index + 1}. ${paper.title || "Untitled"}`)
    .join("\n");

  return sendDiscordNotification({
    title: `📰 Daily Digest Complete (${date || "unknown"})`,
    description: `Found **${totalDeduped}** unique papers across ${keywordCounts.length} keywords.`,
    color: 0x00ff88,
    fields: [
      { name: "Keywords", value: keywordSummary || "None", inline: false },
      { name: "Top Papers", value: topTitles || "None", inline: false },
    ],
  });
}

export async function notifyPipelineComplete({
  query,
  paperCount = 0,
  duration = "",
}) {
  return sendDiscordNotification({
    title: "⚙️ Pipeline Complete",
    description: `Query: **${query || "unknown"}**`,
    color: 0xd4af37,
    fields: [
      { name: "Papers Found", value: String(paperCount), inline: true },
      { name: "Duration", value: duration || "N/A", inline: true },
    ],
  });
}