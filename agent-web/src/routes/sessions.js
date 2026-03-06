import express from "express";

import {
  createSession,
  deleteSession,
  getMessages,
  getSession,
  listSessions,
} from "../db/database.js";

const router = express.Router();

router.get("/", (req, res) => {
  const limit = req.query.limit ? Number(req.query.limit) : 50;
  res.json(listSessions(limit));
});

router.get("/:id/export", (req, res) => {
  try {
    const session = getSession(req.params.id);

    if (!session) {
      return res.status(404).json({ error: "Session not found or empty" });
    }

    const messages = getMessages(session.id);
    if (!messages.length) {
      return res.status(404).json({ error: "Session not found or empty" });
    }

    const lines = [
      "# JARVIS Chat Export",
      `**Session**: ${session.id}`,
      `**Exported**: ${new Date().toISOString()}`,
      "---",
      "",
    ];

    for (const message of messages) {
      const label = message.role === "user" ? "👤 User" : "🤖 JARVIS";
      lines.push(`## ${label}`);
      lines.push(`*${message.created_at || ""}*`);
      lines.push("");
      lines.push(message.content || "");
      lines.push("");
      lines.push("---");
      lines.push("");
    }

    res.setHeader("Content-Type", "text/markdown; charset=utf-8");
    res.setHeader("Content-Disposition", `attachment; filename="jarvis-chat-${session.id}.md"`);
    return res.send(lines.join("\n"));
  } catch (error) {
    return res.status(500).json({ error: error?.message || "Failed to export session" });
  }
});

router.get("/:id", (req, res) => {
  const session = getSession(req.params.id);

  if (!session) {
    return res.status(404).json({ error: "Session not found" });
  }

  return res.json(session);
});

router.delete("/:id", (req, res) => {
  const deleted = deleteSession(req.params.id);

  if (!deleted) {
    return res.status(404).json({ error: "Session not found" });
  }

  return res.json({ success: true });
});

router.post("/", (req, res) => {
  const { title = "New Session", model = "gemini/gemini-2.0-flash" } = req.body ?? {};
  const session = createSession(title, model);
  res.status(201).json(session);
});

export default router;



