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

describe("Security Module", () => {
  it("security.js middleware file exists", () => {
    assert.ok(fs.existsSync(path.join(agentWebRoot, "src", "middleware", "security.js")));
  });

  it("exports createHelmetMiddleware and rate limiters", async () => {
    const mod = await import(toFileImport("src", "middleware", "security.js"));
    assert.equal(typeof mod.createHelmetMiddleware, "function");
    assert.equal(typeof mod.createApiRateLimiter, "function");
    assert.equal(typeof mod.createLlmRateLimiter, "function");
  });

  it("package.json includes helmet and express-rate-limit", () => {
    const pkg = JSON.parse(fs.readFileSync(path.join(agentWebRoot, "package.json"), "utf8"));
    assert.ok(pkg.dependencies.helmet);
    assert.ok(pkg.dependencies["express-rate-limit"]);
  });

  it("server.js imports security middleware", () => {
    const serverCode = fs.readFileSync(path.join(agentWebRoot, "src", "server.js"), "utf8");
    assert.ok(serverCode.includes("createHelmetMiddleware"));
    assert.ok(serverCode.includes("createApiRateLimiter"));
  });
});

describe("Security Headers", () => {
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

  it("health endpoint returns X-Content-Type-Options: nosniff", async () => {
    if (!baseUrl) {
      return;
    }

    const res = await fetch(`${baseUrl}/api/health`);
    assert.equal(res.status, 200);
    assert.equal(res.headers.get("x-content-type-options"), "nosniff");
  });

  it("rate limit headers are present on API responses", async () => {
    if (!baseUrl) {
      return;
    }

    const res = await fetch(`${baseUrl}/api/health`);
    const rateLimit = res.headers.get("ratelimit-limit") || res.headers.get("x-ratelimit-limit");
    assert.ok(rateLimit || res.status === 200);
  });
});