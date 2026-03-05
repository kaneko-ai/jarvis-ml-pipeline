import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.join(__dirname, '..', '..', '..');
const CONFIG_PATH = path.join(PROJECT_ROOT, 'config.yaml');

let cachedArchiveDir = null;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function sanitizeFilename(title, year) {
  const baseTitle = typeof title === 'string' ? title : '';
  let normalized = baseTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  normalized = normalized.replace(/-+/g, '-').replace(/^-+|-+$/g, '');
  normalized = normalized.slice(0, 80);
  normalized = normalized.replace(/-+$/g, '');

  if (!normalized) {
    normalized = 'untitled';
  }

  const yearPart = year !== undefined && year !== null && String(year).trim() !== '' ? String(year).trim() : '';
  return yearPart ? `${normalized}-${yearPart}` : normalized;
}

function getArchiveDir() {
  if (cachedArchiveDir) {
    return cachedArchiveDir;
  }

  const raw = fs.readFileSync(path.join(CONFIG_PATH), 'utf8');
  const parsed = yaml.load(raw) || {};
  const configured = parsed?.storage?.pdf_archive_dir;

  if (!configured || typeof configured !== 'string') {
    throw new Error('storage.pdf_archive_dir is missing in config.yaml');
  }

  cachedArchiveDir = path.isAbsolute(configured)
    ? path.join(configured)
    : path.join(PROJECT_ROOT, configured);

  return cachedArchiveDir;
}

function getTargetPath({ title, year }) {
  const archiveDir = getArchiveDir();
  const filename = `${sanitizeFilename(title, year)}.pdf`;
  return path.join(archiveDir, filename);
}

async function fetchPdfBuffer(pdfUrl) {
  const response = await fetch(pdfUrl);
  if (!response.ok) {
    throw new Error(`PDF fetch failed: HTTP ${response.status}`);
  }
  const bytes = await response.arrayBuffer();
  return Buffer.from(bytes);
}

async function resolvePdfUrlFromDoi(doi) {
  const endpoint = `https://api.unpaywall.org/v2/${encodeURIComponent(doi)}?email=jarvis@example.com`;
  const response = await fetch(endpoint);
  if (!response.ok) {
    throw new Error(`Unpaywall request failed: HTTP ${response.status}`);
  }

  const body = await response.json();
  return body?.best_oa_location?.url_for_pdf || '';
}

export async function archivePdf({ doi, pmid, title, url, year }) {
  try {
    const archiveDir = getArchiveDir();
    fs.mkdirSync(path.join(archiveDir), { recursive: true });

    let pdfUrl = '';
    let source = '';

    if (typeof url === 'string' && url.trim() !== '') {
      pdfUrl = url.trim();
      source = 'direct';
    } else if (typeof doi === 'string' && doi.trim() !== '') {
      pdfUrl = await resolvePdfUrlFromDoi(doi.trim());
      source = 'unpaywall';
    } else {
      return { success: false, reason: 'missing-url-and-doi' };
    }

    if (!pdfUrl) {
      return { success: false, reason: 'pdf-url-not-found' };
    }

    const savedPath = getTargetPath({ title, year, doi, pmid });
    const pdfBuffer = await fetchPdfBuffer(pdfUrl);
    fs.writeFileSync(path.join(savedPath), pdfBuffer);

    return { success: true, path: savedPath, source };
  } catch (error) {
    return { success: false, reason: error?.message || 'archive-failed' };
  }
}

export async function archivePapers(papers) {
  try {
    if (!Array.isArray(papers)) {
      return [{ success: false, reason: 'invalid-papers-input' }];
    }

    const results = [];

    for (let i = 0; i < papers.length; i += 1) {
      const paper = papers[i] || {};

      let targetPath = '';
      try {
        targetPath = getTargetPath(paper);
      } catch (error) {
        results.push({ success: false, reason: error?.message || 'config-read-failed' });
        continue;
      }

      if (fs.existsSync(path.join(targetPath))) {
        results.push({ success: true, path: targetPath, source: 'existing', skipped: true });
        continue;
      }

      const result = await archivePdf(paper);
      results.push(result);

      if (i < papers.length - 1) {
        await sleep(2000);
      }
    }

    return results;
  } catch (error) {
    return [{ success: false, reason: error?.message || 'archive-papers-failed' }];
  }
}
