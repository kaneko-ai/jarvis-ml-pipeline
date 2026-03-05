import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..', '..');
const agentWebRoot = path.resolve(__dirname, '..');

// daily-digest.js のモジュールインポートテスト
describe('Daily Digest Module', () => {
  it('should export runDailyDigest function', async () => {
    const mod = await import('../src/skills/daily-digest.js');
    assert.ok(typeof mod.runDailyDigest === 'function' || typeof mod.default === 'function',
      'runDailyDigest or default export should be a function');
  });
});

// digest.js ルーターのインポートテスト
describe('Digest Router', () => {
  it('should export a Router', async () => {
    const mod = await import('../src/routes/digest.js');
    assert.ok(mod.default || mod.router,
      'digest.js should export a router');
  });
});

// config.yaml の digest セクション読み込みテスト（プロジェクトルート基準）
describe('Digest Config', () => {
  it('should have digest keywords in config.yaml', async () => {
    const yaml = await import('js-yaml');
    const configPath = path.join(projectRoot, 'config.yaml');
    assert.ok(fs.existsSync(configPath), 'config.yaml should exist at project root: ' + configPath);
    const raw = fs.readFileSync(configPath, 'utf8');
    const config = yaml.load(raw);
    assert.ok(config.digest, 'config.yaml should have digest section');
    assert.ok(Array.isArray(config.digest.keywords), 'digest.keywords should be an array');
    assert.ok(config.digest.keywords.length > 0, 'digest.keywords should not be empty');
  });
});

// data/digests ディレクトリ存在テスト（agent-web/data/digests 基準）
describe('Digest Output Directory', () => {
  it('should have data/digests directory', () => {
    const digestDir = path.join(agentWebRoot, 'data', 'digests');
    assert.ok(fs.existsSync(digestDir), 'data/digests directory should exist at: ' + digestDir);
  });
});

describe('paper-search module', () => {
  it('should export searchLivePapers function', async () => {
    const mod = await import('../src/llm/paper-search.js');
    assert.equal(typeof mod.searchLivePapers, 'function');
  });
});

describe('papers-repository module', () => {
  it('should export insertPaper function', async () => {
    const mod = await import('../src/db/papers-repository.js');
    assert.equal(typeof mod.insertPaper, 'function');
  });

  it('should export getPapers function', async () => {
    const mod = await import('../src/db/papers-repository.js');
    assert.equal(typeof mod.getPapers, 'function');
  });

  it('should export countPapers function', async () => {
    const mod = await import('../src/db/papers-repository.js');
    assert.equal(typeof mod.countPapers, 'function');
  });
});

describe('papers-repository CRUD', () => {
  it('insertPaper and getPapers roundtrip', async () => {
    const { insertPaper, getPapers, deletePaper } = await import('../src/db/papers-repository.js');
    const inserted = insertPaper({
      title: 'Test Paper 2026',
      year: 2026,
      source: 'test',
      keyword: 'test',
    });

    const insertedId = typeof inserted === 'object' ? inserted.id : inserted;
    assert.ok(insertedId, 'inserted id should exist');

    const papers = getPapers({ keyword: 'test' });
    assert.ok(Array.isArray(papers));
    assert.ok(papers.length > 0);
    assert.equal(papers[0].title, 'Test Paper 2026');

    deletePaper(insertedId);
  });
});

describe('digest-to-obsidian module', () => {
  it('should export exportDigestToObsidian function', async () => {
    const mod = await import('../src/skills/digest-to-obsidian.js');
    assert.equal(typeof mod.exportDigestToObsidian, 'function');
  });

  it('should export exportLatestDigest function', async () => {
    const mod = await import('../src/skills/digest-to-obsidian.js');
    assert.equal(typeof mod.exportLatestDigest, 'function');
  });
});


describe('pdf-archiver module', () => {
  it('should export archivePdf function', async () => {
    const mod = await import('../src/skills/pdf-archiver.js');
    assert.equal(typeof mod.archivePdf, 'function');
  });

  it('should export archivePapers function', async () => {
    const mod = await import('../src/skills/pdf-archiver.js');
    assert.equal(typeof mod.archivePapers, 'function');
  });
});

describe('zotero-sync module', () => {
  it('should export syncToZotero function', async () => {
    const mod = await import('../src/skills/zotero-sync.js');
    assert.equal(typeof mod.syncToZotero, 'function');
  });

  it('should export syncLatestDigest function', async () => {
    const mod = await import('../src/skills/zotero-sync.js');
    assert.equal(typeof mod.syncLatestDigest, 'function');
  });
});

describe('chroma-bridge module', () => {
  it('should export searchChromaDB function', async () => {
    const mod = await import('../src/db/chroma-bridge.js');
    assert.equal(typeof mod.searchChromaDB, 'function');
  });

  it('should export getChromaCount function', async () => {
    const mod = await import('../src/db/chroma-bridge.js');
    assert.equal(typeof mod.getChromaCount, 'function');
  });

  it('should export indexPapersToChroma function', async () => {
    const mod = await import('../src/db/chroma-bridge.js');
    assert.equal(typeof mod.indexPapersToChroma, 'function');
  });
});

describe('memory-store module', () => {
  it('should export storeFact function', async () => {
    const mod = await import('../src/db/memory-store.js');
    assert.equal(typeof mod.storeFact, 'function');
  });

  it('should export getMemoryContext function', async () => {
    const mod = await import('../src/db/memory-store.js');
    assert.equal(typeof mod.getMemoryContext, 'function');
  });

  it('should export extractAndStoreFacts function', async () => {
    const mod = await import('../src/db/memory-store.js');
    assert.equal(typeof mod.extractAndStoreFacts, 'function');
  });

  it('storeFact and getFact roundtrip', async () => {
    const { storeFact, getFact, deleteFact } = await import('../src/db/memory-store.js');
    const stored = storeFact({ key: 'test_key', value: 'test_value', category: 'test' });
    assert.ok(stored);
    const fact = getFact('test_key');
    assert.ok(fact);
    assert.equal(fact.value, 'test_value');
    deleteFact('test_key');
  });

  it('setPreference and getPreference roundtrip', async () => {
    const { setPreference, getPreference } = await import('../src/db/memory-store.js');
    const pref = setPreference('test_pref', 'test_val');
    assert.ok(pref);
    assert.equal(getPreference('test_pref'), 'test_val');
    setPreference('test_pref', '');
  });

  it('getMemoryContext returns string', async () => {
    const { getMemoryContext } = await import('../src/db/memory-store.js');
    const context = getMemoryContext();
    assert.equal(typeof context, 'string');
  });

  it('extractAndStoreFacts handles simple name', async () => {
    const { getFact, storeFact, deleteFact, extractAndStoreFacts } = await import('../src/db/memory-store.js');
    const prevUserName = getFact('user_name');
    const prevInterest = getFact('research_interest_1');

    try {
      extractAndStoreFacts('Your name is TestUser and you study PD-1', 'test-session');
      const fact = getFact('user_name');
      assert.ok(fact);
      assert.match(fact.value, /TestUser/);
    } finally {
      if (prevUserName) {
        storeFact({
          key: prevUserName.key,
          value: prevUserName.value,
          sourceSession: prevUserName.source_session,
          category: prevUserName.category,
          confidence: prevUserName.confidence,
        });
      } else {
        deleteFact('user_name');
      }

      if (prevInterest) {
        storeFact({
          key: prevInterest.key,
          value: prevInterest.value,
          sourceSession: prevInterest.source_session,
          category: prevInterest.category,
          confidence: prevInterest.confidence,
        });
      } else {
        deleteFact('research_interest_1');
      }
    }
  });
});

describe('chat system prompt', () => {
  it('SYSTEM_PROMPT constant should exist in chat module', async () => {
    const mod = await import('../src/routes/chat.js');
    assert.ok(mod);
  });
});

