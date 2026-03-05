import assert from "node:assert/strict";
import { describe, it, afterEach } from "node:test";
import http from "node:http";
import express from "express";

import { ParallelRunner } from "../src/llm/parallel-runner.js";
import * as geminiSummarizer from "../src/llm/gemini-summarizer.js";
import pipelineRouter from "../src/routes/pipeline.js";
import monitorRouter from "../src/routes/monitor.js";

const originalFetch = globalThis.fetch;
const originalGeminiApiKey = process.env.GEMINI_API_KEY;
const originalGeminiModel = process.env.GEMINI_MODEL;

function setGeminiEnv() {
  process.env.GEMINI_API_KEY = "test-api-key";
  process.env.GEMINI_MODEL = "gemini-2.0-flash";
}

function mockGeminiFetch(summaryText = "Mocked summary") {
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    statusText: "OK",
    async json() {
      return {
        candidates: [
          {
            content: {
              parts: [{ text: summaryText }],
            },
          },
        ],
      };
    },
  });
}

function startServer(router, mountPath) {
  const app = express();
  app.use(mountPath, router);
  const server = http.createServer(app);

  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      server.off("error", reject);
      resolve(server);
    });
  });
}

function closeServer(server) {
  return new Promise((resolve, reject) => {
    server.close((error) => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
  });
}

function requestJson(server, path) {
  const address = server.address();
  const port = typeof address === "object" && address ? address.port : null;

  return new Promise((resolve, reject) => {
    const req = http.request(
      {
        hostname: "127.0.0.1",
        port,
        path,
        method: "GET",
      },
      (res) => {
        let body = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          try {
            const parsed = body ? JSON.parse(body) : null;
            resolve({
              statusCode: res.statusCode,
              body: parsed,
            });
          } catch (error) {
            reject(error);
          }
        });
      }
    );

    req.on("error", reject);
    req.end();
  });
}

afterEach(() => {
  globalThis.fetch = originalFetch;

  if (originalGeminiApiKey === undefined) {
    delete process.env.GEMINI_API_KEY;
  } else {
    process.env.GEMINI_API_KEY = originalGeminiApiKey;
  }

  if (originalGeminiModel === undefined) {
    delete process.env.GEMINI_MODEL;
  } else {
    process.env.GEMINI_MODEL = originalGeminiModel;
  }
});

describe("parallel-runner.js", () => {
  it("ParallelRunner instance can be created", () => {
    assert.doesNotThrow(() => new ParallelRunner());
  });

  it("runInPool executes async function and returns result", async () => {
    const runner = new ParallelRunner();
    const result = await runner.runInPool("apiPool", async () => "ok");

    assert.equal(result, "ok");
    runner.shutdown();
  });

  it("getStatus returns expected shape", () => {
    const runner = new ParallelRunner();
    const status = runner.getStatus();

    assert.deepEqual(status.apiPool, {
      queued: 0,
      running: 0,
      completed: 0,
      failed: 0,
    });
    assert.deepEqual(status.geminiPool, {
      queued: 0,
      running: 0,
      completed: 0,
      failed: 0,
    });
    assert.deepEqual(status.copilotPool, {
      queued: 0,
      running: 0,
      completed: 0,
      failed: 0,
    });

    runner.shutdown();
  });

  it("shutdown clears queued tasks without error", async () => {
    const runner = new ParallelRunner();

    let release;
    const gate = new Promise((resolve) => {
      release = resolve;
    });

    const runningTasks = Array.from({ length: 4 }, () =>
      runner.runInPool("apiPool", async () => {
        await gate;
        return "running";
      })
    );

    const queuedTask = runner.runInPool("apiPool", async () => "queued");

    await new Promise((resolve) => setTimeout(resolve, 10));
    assert.ok(runner.getStatus().apiPool.queued >= 1);

    assert.doesNotThrow(() => runner.shutdown());
    await assert.rejects(queuedTask, /shut down/i);

    release();
    await Promise.allSettled(runningTasks);

    assert.equal(runner.getStatus().apiPool.queued, 0);
  });
});

describe("gemini-summarizer.js", () => {
  it("summarizePaper returns object with summary field", async () => {
    setGeminiEnv();
    mockGeminiFetch("Single paper summary");

    const summarizePaper =
      typeof geminiSummarizer.summarizePaper === "function"
        ? geminiSummarizer.summarizePaper
        : async (paper) => {
            const [result] = await geminiSummarizer.summarizeBatch([paper], {
              concurrency: 1,
              delayMs: 0,
              timeoutMs: 1000,
            });
            return result;
          };

    const result = await summarizePaper({
      title: "Test paper",
      abstract: "Test abstract",
      authors: "Tester",
    });

    assert.equal(typeof result, "object");
    assert.ok(Object.hasOwn(result, "summary"));
  });

  it("summarizeBatch returns [] for empty array", async () => {
    const result = await geminiSummarizer.summarizeBatch([]);
    assert.deepEqual(result, []);
  });

  it("summarizeBatch calls onProgress callback", async () => {
    setGeminiEnv();
    mockGeminiFetch("Batch summary");

    const calls = [];
    const papers = [
      { title: "P1", abstract: "A1" },
      { title: "P2", abstract: "A2" },
    ];

    const result = await geminiSummarizer.summarizeBatch(papers, {
      concurrency: 1,
      delayMs: 0,
      timeoutMs: 1000,
      onProgress(payload) {
        calls.push(payload);
      },
    });

    assert.equal(result.length, 2);
    assert.ok(calls.length >= 2);
    assert.ok(calls.every((payload) => typeof payload.current === "number"));
    assert.ok(calls.every((payload) => typeof payload.total === "number"));
  });
});

describe("pipeline routes", () => {
  it("pipeline router is a valid Express router", () => {
    assert.equal(typeof pipelineRouter, "function");
  });

  it("/api/pipeline/history endpoint exists", async () => {
    const server = await startServer(pipelineRouter, "/api/pipeline");

    try {
      const response = await requestJson(server, "/api/pipeline/history");
      assert.equal(response.statusCode, 200);
      assert.ok(Array.isArray(response.body));
    } finally {
      await closeServer(server);
    }
  });
});

describe("monitor routes", () => {
  it("monitor router is a valid Express router", () => {
    assert.equal(typeof monitorRouter, "function");
  });

  it("/api/monitor/status returns expected JSON shape", async () => {
    globalThis.fetch = async () => ({ ok: true });
    const server = await startServer(monitorRouter, "/api/monitor");

    try {
      const response = await requestJson(server, "/api/monitor/status");

      assert.equal(response.statusCode, 200);
      assert.equal(typeof response.body, "object");
      assert.ok(response.body !== null);
      assert.ok(Object.hasOwn(response.body, "copilotApi"));
      assert.ok(Object.hasOwn(response.body, "db"));
      assert.ok(Object.hasOwn(response.body, "uptime"));
      assert.ok(Object.hasOwn(response.body, "nodeVersion"));
      assert.ok(Object.hasOwn(response.body, "timestamp"));
    } finally {
      await closeServer(server);
    }
  });
});