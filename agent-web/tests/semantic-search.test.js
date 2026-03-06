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

describe("Semantic Search", () => {
  it("semantic-search.js route file exists", () => {
    assert.ok(fs.existsSync(path.join(agentWebRoot, "src", "routes", "semantic-search.js")));
  });

  it("index.html contains semantic search radio button", () => {
    const html = fs.readFileSync(path.join(agentWebRoot, "public", "index.html"), "utf8");
    assert.ok(html.includes('name="searchType"'));
    assert.ok(html.includes('value="semantic"'));
  });

  it("search.js references semantic search API", () => {
    const js = fs.readFileSync(
      path.join(agentWebRoot, "public", "js", "modules", "search.js"),
      "utf8"
    );
    assert.ok(js.includes("semantic"));
    assert.ok(js.includes("/api/semantic-search"));
  });
});

describe("Semantic Search API", () => {
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

  it("GET /api/semantic-search without query returns 400", async () => {
    if (!baseUrl) {
      return;
    }

    const res = await fetch(`${baseUrl}/api/semantic-search`);
    assert.equal(res.status, 400);
  });

  it("GET /api/semantic-search with query returns results structure", async () => {
    if (!baseUrl) {
      return;
    }

    const res = await fetch(`${baseUrl}/api/semantic-search?query=CRISPR`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.searchType, "semantic");
    assert.ok(Array.isArray(data.results));
    assert.equal(typeof data.total, "number");
  });
});