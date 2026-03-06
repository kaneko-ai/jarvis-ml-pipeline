import { Router } from "express";

import {
  isDiscordConfigured,
  sendDiscordNotification,
} from "../skills/discord-notify.js";

const router = Router();

router.get("/status", (req, res) => {
  res.json({ discord: { configured: isDiscordConfigured() } });
});

router.post("/test", async (req, res) => {
  try {
    const result = await sendDiscordNotification({
      title: "🧪 Test Notification",
      description: "JARVIS Research OS is connected to Discord.",
      color: 0xd4af37,
    });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;