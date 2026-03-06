import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('I18N Module', () => {
  it('i18n.js file exists and is valid ESM', async () => {
    const filePath = path.join(__dirname, '..', 'public', 'js', 'modules', 'i18n.js');
    const content = readFileSync(filePath, 'utf-8');
    assert.ok(content.includes('export function t('));
    assert.ok(content.includes('export function setLang('));
    assert.ok(content.includes('export function toggleLang('));
  });

  it('translations include both en and ja', async () => {
    const filePath = path.join(__dirname, '..', 'public', 'js', 'modules', 'i18n.js');
    const content = readFileSync(filePath, 'utf-8');
    assert.ok(content.includes('en:'));
    assert.ok(content.includes('ja:'));
    assert.ok(content.includes("'nav.chat'"));
    assert.ok(content.includes('チャット'));
  });

  it('index.html contains data-i18n attributes', () => {
    const html = readFileSync(path.join(__dirname, '..', 'public', 'index.html'), 'utf-8');
    assert.ok(html.includes('data-i18n='));
    assert.ok(html.includes('langToggle'));
  });

  it('all en keys have ja equivalents', async () => {
    const filePath = path.join(__dirname, '..', 'public', 'js', 'modules', 'i18n.js');
    const content = readFileSync(filePath, 'utf-8');
    const enKeys = [...content.matchAll(/'([a-z]+\.[a-zA-Z]+)'/g)].map((match) => match[1]);
    assert.ok(enKeys.length >= 20, `Expected >= 20 i18n keys, got ${enKeys.length}`);
  });
});
