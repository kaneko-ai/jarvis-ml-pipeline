import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('Dashboard Charts', () => {
  it('index.html includes Chart.js CDN', () => {
    const html = readFileSync(path.join(__dirname, '..', 'public', 'index.html'), 'utf-8');
    assert.ok(html.includes('chart.umd.min.js') || html.includes('Chart.js'));
  });

  it('index.html has chart canvas elements', () => {
    const html = readFileSync(path.join(__dirname, '..', 'public', 'index.html'), 'utf-8');
    assert.ok(html.includes('chart-by-year'));
    assert.ok(html.includes('chart-by-source'));
    assert.ok(html.includes('chart-by-keyword'));
    assert.ok(html.includes('chart-by-journal'));
  });

  it('dashboard.js exists and references Chart', () => {
    const filePath = path.join(__dirname, '..', 'public', 'js', 'modules', 'dashboard.js');
    assert.ok(existsSync(filePath));
    const content = readFileSync(filePath, 'utf-8');
    assert.ok(content.includes('Chart') || content.includes('chart'));
  });

  it('styles.css has chart-grid styles', () => {
    const css = readFileSync(path.join(__dirname, '..', 'public', 'css', 'styles.css'), 'utf-8');
    assert.ok(css.includes('chart-grid') || css.includes('chart-card'));
  });
});
