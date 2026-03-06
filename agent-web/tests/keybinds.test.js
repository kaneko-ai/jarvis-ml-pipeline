import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('Keyboard Shortcuts', () => {
  it('keybinds.js module exists', () => {
    assert.ok(existsSync(path.join(__dirname, '..', 'public', 'js', 'modules', 'keybinds.js')));
  });

  it('exports init function', () => {
    const content = readFileSync(
      path.join(__dirname, '..', 'public', 'js', 'modules', 'keybinds.js'), 'utf-8');
    assert.ok(content.includes('export function init'));
  });

  it('defines at least 10 shortcuts', () => {
    const content = readFileSync(
      path.join(__dirname, '..', 'public', 'js', 'modules', 'keybinds.js'), 'utf-8');
    const matches = content.match(/key:\s*'/g);
    assert.ok(matches && matches.length >= 10, `Expected >=10 shortcuts, found ${matches?.length}`);
  });

  it('app.js imports keybinds', () => {
    const content = readFileSync(
      path.join(__dirname, '..', 'public', 'js', 'app.js'), 'utf-8');
    assert.ok(content.includes('keybinds'));
  });
});
