import { after, before, describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createServer } from "node:http";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const agentWebRoot = path.join(__dirname, "..");

function toFileImport(...segments) {
  return pathToFileURL(path.join(agentWebRoot, ...segments)).href;
}

describe("Discord Notify Module", () => {
  it("discord-notify.js exists and exports expected functions", async () => {
    const filePath = path.join(agentWebRoot, "src", "skills", "discord-notify.js");
    assert.ok(fs.existsSync(filePath), "discord-notify.js should exist");
    const mod = await import(toFileImport("src", "skills", "discord-notify.js"));
    assert.equal(typeof mod.isDiscordConfigured, "function");
    assert.equal(typeof mod.sendDiscordNotification, "function");
    assert.equal(typeof mod.notifyDigestComplete, "function");
    assert.equal(typeof mod.notifyPipelineComplete, "function");
  });

  it("isDiscordConfigured returns boolean", async () => {
    const mod = await import(toFileImport("src", "skills", "discord-notify.js"));
    const result = mod.isDiscordConfigured();
    assert.equal(typeof result, "boolean");
  });

  it("sendDiscordNotification returns not_configured when URL is missing", async () => {
    const mod = await import(toFileImport("src", "skills", "discord-notify.js"));
    if (mod.isDiscordConfigured()) {
      return;
    }

    const result = await mod.sendDiscordNotification({
      title: "Test",
      description: "Test",
    });
    assert.equal(result.sent, false);
    assert.equal(result.reason, "not_configured");
  });

  it("notifications route file exists", () => {
    const filePath = path.join(agentWebRoot, "src", "routes", "notifications.js");
    assert.ok(fs.existsSync(filePath));
  });
});

describe("Notifications API", () => {
  let app;
  let server;
  let baseUrl;

  before(async () => {
    const mod = await import(toFileImport("src", "server.js"));
    app = mod.app || mod.default;
    if (!app) {
      return;
    }

    await new Promise((resolve) => {
      server = createServer(app);
      server.listen(0, () => {
        baseUrl = `http://localhost:${server.address().port}`;
        resolve();
      });
    });
  });

  after(async () => {
    if (server) {
      await new Promise((resolve) => server.close(resolve));
    }
  });

  it("GET /api/notifications/status returns discord config status", async () => {
    if (!baseUrl) {
      return;
    }

    const res = await fetch(`${baseUrl}/api/notifications/status`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(typeof data.discord.configured, "boolean");
  });
});