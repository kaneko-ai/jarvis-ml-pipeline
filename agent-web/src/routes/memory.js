import express from "express";
import {
  deleteFact,
  getAllFacts,
  getAllPreferences,
  getFact,
  getMemoryContext,
  setPreference,
  storeFact,
} from "../db/memory-store.js";

const router = express.Router();

router.get("/facts", (req, res) => {
  try {
    return res.json(getAllFacts());
  } catch (error) {
    return res.status(500).json({ error: error?.message || "Internal Server Error" });
  }
});

router.get("/facts/:key", (req, res) => {
  try {
    const fact = getFact(req.params.key);
    if (!fact) {
      return res.status(404).json({ error: "Fact not found" });
    }
    return res.json(fact);
  } catch (error) {
    return res.status(500).json({ error: error?.message || "Internal Server Error" });
  }
});

router.post("/facts", (req, res) => {
  try {
    const { key, value, category, confidence } = req.body || {};
    storeFact({ key, value, category, confidence });
    return res.json({ success: true });
  } catch (error) {
    return res.status(500).json({ error: error?.message || "Internal Server Error" });
  }
});

router.delete("/facts/:key", (req, res) => {
  try {
    deleteFact(req.params.key);
    return res.json({ success: true });
  } catch (error) {
    return res.status(500).json({ error: error?.message || "Internal Server Error" });
  }
});

router.get("/preferences", (req, res) => {
  try {
    return res.json(getAllPreferences());
  } catch (error) {
    return res.status(500).json({ error: error?.message || "Internal Server Error" });
  }
});

router.post("/preferences", (req, res) => {
  try {
    const { key, value } = req.body || {};
    setPreference(key, value);
    return res.json({ success: true });
  } catch (error) {
    return res.status(500).json({ error: error?.message || "Internal Server Error" });
  }
});

router.get("/context", (req, res) => {
  try {
    return res.json({ context: getMemoryContext() });
  } catch (error) {
    return res.status(500).json({ error: error?.message || "Internal Server Error" });
  }
});

export default router;