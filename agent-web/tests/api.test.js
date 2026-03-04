import { describe, it } from "node:test";
import assert from "node:assert/strict";

const BASE_URL = "http://localhost:3000";

async function fetchJSON(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  assert.equal(res.ok, true, `GET ${path} returned ${res.status}`);
  return res.json();
}

describe("API Endpoints (requires running server)", () => {
  it("GET /api/health returns ok", async () => {
    const data = await fetchJSON("/api/health");
    assert.equal(data.status, "ok");
    assert.ok(data.version, "version should exist");
  });

  it("GET /api/skills returns array of skills", async () => {
    const data = await fetchJSON("/api/skills");
    assert.ok(Array.isArray(data), "should be an array");
    assert.ok(data.length >= 1, "should have at least 1 skill");
    const first = data[0];
    assert.ok(first.name, "skill should have name");
  });

  it("GET /api/mcp/servers returns servers array", async () => {
    const data = await fetchJSON("/api/mcp/servers");
    assert.ok(Array.isArray(data), "should be an array");
    assert.ok(data.length >= 1, "should have at least 1 server");
    const first = data[0];
    assert.ok(first.name, "server should have name");
  });

  it("GET /api/models returns array with model objects", async () => {
    const data = await fetchJSON("/api/models");
    assert.ok(Array.isArray(data), "should be an array");
    assert.ok(data.length >= 1, "should have at least 1 model");
    const first = data[0];
    assert.ok(first.id || first.name, "model should have id or name");
  });

  it("GET /api/sessions returns array", async () => {
    const data = await fetchJSON("/api/sessions");
    assert.ok(Array.isArray(data), "should be an array");
  });
});
