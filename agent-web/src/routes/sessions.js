import express from "express";

import {
  createSession,
  deleteSession,
  getSession,
  listSessions,
} from "../db/database.js";

const router = express.Router();

router.get("/", (req, res) => {
  const limit = req.query.limit ? Number(req.query.limit) : 50;
  res.json(listSessions(limit));
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
