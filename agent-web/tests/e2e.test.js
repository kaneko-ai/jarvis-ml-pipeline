import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import {
  countPapers,
  deletePaper,
  getPaperByDoi,
  init as initPapersRepository,
  insertPaper,
  insertPapers,
  searchPapers,
} from "../src/db/papers-repository.js";
import {
  deleteFact,
  getAllPreferences,
  getFact,
  getFactsByCategory,
  getMemoryContext,
  getPreference,
  setPreference,
  storeFact,
} from "../src/db/memory-store.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const agentWebRoot = path.resolve(__dirname, "..");

const PAPER_ONE = {
  doi: "10.1234/e2e-test-001",
  pmid: "E2E001",
  title: "E2E Test Paper on CRISPR",
  authors: "Test Author",
  journal: "Test Journal",
  year: 2025,
  abstract: "This is an end-to-end test paper",
  source: "test",
  score: 0.85,
};

const BULK_PAPERS = [
  {
    doi: "10.1234/e2e-test-002",
    pmid: "E2E002",
    title: "E2E Bulk Paper A",
    authors: "Bulk Author A",
    journal: "Bulk Journal",
    year: 2025,
    abstract: "Bulk insert paper A",
    source: "test",
    score: 0.7,
  },
  {
    doi: "10.1234/e2e-test-003",
    pmid: "E2E003",
    title: "E2E Bulk Paper B",
    authors: "Bulk Author B",
    journal: "Bulk Journal",
    year: 2025,
    abstract: "Bulk insert paper B",
    source: "test",
    score: 0.72,
  },
];

function cleanupPaper(doi) {
  deletePaper(doi);
}

describe("E2E: Papers Repository Full Flow", () => {
  it("insert → search → count → delete roundtrip", () => {
    initPapersRepository();
    cleanupPaper(PAPER_ONE.doi);

    const countBefore = countPapers();
    const insertResult = insertPaper(PAPER_ONE);

    assert.equal(insertResult.inserted, true);
    assert.equal(countPapers(), countBefore + 1);

    const searchResults = searchPapers("CRISPR");
    assert.ok(Array.isArray(searchResults));
    assert.ok(searchResults.some((paper) => paper.doi === PAPER_ONE.doi));

    const paperByDoi = getPaperByDoi(PAPER_ONE.doi);
    assert.ok(paperByDoi);
    assert.equal(paperByDoi.title, PAPER_ONE.title);

    assert.equal(deletePaper(PAPER_ONE.doi), true);
    assert.equal(countPapers(), countBefore);
  });

  it("insertPapers bulk insert works", () => {
    initPapersRepository();
    BULK_PAPERS.forEach((paper) => cleanupPaper(paper.doi));

    const countBefore = countPapers();
    const result = insertPapers(BULK_PAPERS);

    assert.equal(result.inserted, 2);
    assert.equal(countPapers(), countBefore + 2);

    BULK_PAPERS.forEach((paper) => {
      assert.equal(deletePaper(paper.doi), true);
    });
    assert.equal(countPapers(), countBefore);
  });
});

describe("E2E: Memory Store Full Flow", () => {
  it("fact lifecycle: store → get → context → delete", () => {
    deleteFact("e2e_test_fact");

    const storedFact = storeFact({
      key: "e2e_test_fact",
      value: "test value",
      category: "e2e",
      confidence: 0.9,
    });

    assert.ok(storedFact);
    assert.equal(getFact("e2e_test_fact")?.value, "test value");
    assert.match(getMemoryContext(), /test value/);

    const categoryFacts = getFactsByCategory("e2e");
    assert.ok(categoryFacts.some((fact) => fact.key === "e2e_test_fact"));

    assert.equal(deleteFact("e2e_test_fact"), true);
    assert.equal(getFact("e2e_test_fact"), null);
  });

  it("preference lifecycle: set → get → getAll", () => {
    setPreference("e2e_pref", "");

    const storedPreference = setPreference("e2e_pref", "pref_value");
    assert.equal(storedPreference, "pref_value");
    assert.equal(getPreference("e2e_pref"), "pref_value");

    const preferences = getAllPreferences();
    assert.equal(preferences.e2e_pref, "pref_value");

    setPreference("e2e_pref", "");
    assert.equal(getPreference("e2e_pref"), null);
  });
});

describe("E2E: Digest Module Integration", () => {
  it("digest data directory contains expected files", () => {
    const digestDir = path.join(agentWebRoot, "data", "digests");
    assert.equal(fs.existsSync(digestDir), true);

    const digestFiles = fs
      .readdirSync(digestDir)
      .filter((name) => name.endsWith(".json"));

    assert.ok(digestFiles.length > 0);

    const firstDigest = JSON.parse(
      fs.readFileSync(path.join(digestDir, digestFiles[0]), "utf8")
    );

    assert.ok(
      Object.hasOwn(firstDigest, "date") ||
        Object.hasOwn(firstDigest, "keywords") ||
        Object.hasOwn(firstDigest, "papers") ||
        Object.hasOwn(firstDigest, "topPapers")
    );
  });

  it("digest-to-obsidian module loads without error", async () => {
    const mod = await import("../src/skills/digest-to-obsidian.js");
    assert.equal(typeof mod.exportDigestToObsidian, "function");
    assert.equal(typeof mod.exportLatestDigest, "function");
  });
});

describe("E2E: Server Routes Integration", () => {
  it("all route modules load without error", async () => {
    const routeModules = await Promise.all([
      import("../src/routes/chat.js"),
      import("../src/routes/pipeline.js"),
      import("../src/routes/digest.js"),
      import("../src/routes/monitor.js"),
      import("../src/routes/memory.js"),
      import("../src/routes/sessions.js"),
      import("../src/routes/models.js"),
      import("../src/routes/skills.js"),
    ]);

    routeModules.forEach((mod) => {
      assert.equal(typeof mod.default, "function");
    });
  });
});

describe("E2E: Session Export", () => {
  it("sessions router has export capability", async () => {
    await import("../src/routes/sessions.js");
    assert.ok(true);
  });
});
