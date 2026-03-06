import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pubDir = path.join(__dirname, '..', 'public');

describe('PWA Support', () => {
  it('manifest.json exists and is valid JSON', () => {
    const manifestPath = path.join(pubDir, 'manifest.json');
    assert.ok(existsSync(manifestPath));
    const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
    assert.equal(manifest.short_name, 'JARVIS');
    assert.ok(manifest.icons.length > 0);
    assert.equal(manifest.display, 'standalone');
  });

  it('sw.js (service worker) exists', () => {
    assert.ok(existsSync(path.join(pubDir, 'sw.js')));
  });

  it('icon file exists', () => {
    assert.ok(existsSync(path.join(pubDir, 'icons', 'icon.svg')));
  });

  it('index.html references manifest', () => {
    const html = readFileSync(path.join(pubDir, 'index.html'), 'utf-8');
    assert.ok(html.includes('manifest.json'));
    assert.ok(html.includes('theme-color'));
  });

  it('sw.js contains cache strategy', () => {
    const sw = readFileSync(path.join(pubDir, 'sw.js'), 'utf-8');
    assert.ok(sw.includes('CACHE_NAME') || sw.includes('caches'));
    assert.ok(sw.includes('install'));
    assert.ok(sw.includes('fetch'));
  });
});
