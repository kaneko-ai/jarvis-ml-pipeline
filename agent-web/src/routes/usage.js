import express from "express";

const router = express.Router();
const COPILOT_API_URL = process.env.COPILOT_API_URL || "http://localhost:4141";

router.get("/", async (req, res) => {
  try {
    const response = await fetch(`${COPILOT_API_URL}/usage`, {
      headers: { "Authorization": "Bearer dummy" }
    });
    if (!response.ok) {
      return res.json({ available: false, error: `Status ${response.status}` });
    }
    const data = await response.json();
    return res.json({ available: true, ...data });
  } catch (e) {
    return res.json({ available: false, error: e.message });
  }
});

export default router;
