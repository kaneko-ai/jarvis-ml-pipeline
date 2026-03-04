import express from "express";
import { getMCPServers, getMCPTools } from "../mcp-bridge/mcp-status.js";

const router = express.Router();

router.get("/servers", (req, res) => {
  res.json(getMCPServers());
});

router.get("/tools", (req, res) => {
  res.json(getMCPTools());
});

export default router;
