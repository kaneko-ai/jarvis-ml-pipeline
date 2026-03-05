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
