import express from "express";
import dotenv from "dotenv";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import yaml from "js-yaml";

import { getDb } from "./db/database.js";
import chatRouter from "./routes/chat.js";
import sessionsRouter from "./routes/sessions.js";
import modelsRouter from "./routes/models.js";
import skillsRouter from "./routes/skills.js";
import mcpRouter from "./routes/mcp.js";
import usageRouter from "./routes/usage.js";
import pipelineRouter from "./routes/pipeline.js";
import monitorRouter from "./routes/monitor.js";
import digestRouter from "./routes/digest.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const agentWebRoot = path.join(__dirname, "..");
const projectRoot = path.join(__dirname, "..", "..");
const publicDir = path.join(agentWebRoot, "public");
const envPath = path.join(projectRoot, ".env");
const configPath = path.join(projectRoot, "config.yaml");

dotenv.config({ path: envPath });

function loadConfig() {
  try {
    const raw = fs.readFileSync(configPath, "utf8");
    return yaml.load(raw) ?? {};
  } catch (error) {
    console.warn(`Failed to load config.yaml: ${error.message}`);
    return {};
  }
}

const config = loadConfig();
getDb();

const app = express();
const port = Number(process.env.PORT || 3000);

app.locals.config = config;
app.locals.version = "1.0.0";
app.locals.paths = {
  agentWebRoot,
  projectRoot,
  publicDir,
  envPath,
  configPath,
};

app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") {
    return res.sendStatus(204);
  }
  return next();
});

app.use(express.json({ limit: "10mb" }));
app.use(express.static(publicDir));
app.use("/data", express.static(path.join(agentWebRoot, "data")));

app.use("/api/chat", chatRouter);
app.use("/api/sessions", sessionsRouter);
app.use("/api/models", modelsRouter);
app.use("/api/skills", skillsRouter);
app.use("/api/mcp", mcpRouter);
app.use("/api/usage", usageRouter);
app.use("/api/pipeline", pipelineRouter);
app.use("/api/monitor", monitorRouter);
app.use("/api/digest", digestRouter);

app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    version: app.locals.version,
    timestamp: new Date().toISOString(),
  });
});

app.listen(port, () => {
  console.log(`JARVIS Agent Web v1.0.0 running on http://localhost:${port}`);
});

export default app;




