import { execFile } from 'node:child_process';
import { access } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.join(__dirname, '..', '..', '..');
const pythonPath = path.join(projectRoot, '.venv', 'Scripts', 'python.exe');

async function exists(filePath) {
  try {
    await access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function runPython(args) {
  if (!(await exists(pythonPath))) {
    return {
      ok: false,
      reason: `Python virtual environment is missing: ${pythonPath}`,
      stdout: '',
      stderr: ''
    };
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30_000);

  try {
    const { stdout, stderr } = await execFileAsync(pythonPath, args, {
      cwd: projectRoot,
      signal: controller.signal,
      windowsHide: true,
      maxBuffer: 10 * 1024 * 1024
    });

    return {
      ok: true,
      reason: '',
      stdout: String(stdout ?? ''),
      stderr: String(stderr ?? '')
    };
  } catch (error) {
    const timedOut = error && error.name === 'AbortError';
    const stderr = String(error?.stderr ?? '').trim();
    const reason = timedOut
      ? 'Python subprocess timed out after 30 seconds'
      : stderr || String(error?.message ?? 'Python subprocess failed');

    return {
      ok: false,
      reason,
      stdout: String(error?.stdout ?? ''),
      stderr
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

function toNumber(value, fallback = 0) {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}

function parseMaybeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function normalizeResult(item) {
  if (typeof item === 'string') {
    return {
      title: item,
      score: 0,
      source: ''
    };
  }

  if (!item || typeof item !== 'object') {
    return null;
  }

  const title =
    item.title ??
    item.paper_title ??
    item.name ??
    item.metadata?.title ??
    item.document?.title ??
    item.text ??
    item.content ??
    '';

  const source =
    item.source ??
    item.path ??
    item.file ??
    item.metadata?.source ??
    item.metadata?.path ??
    item.metadata?.file ??
    '';

  const score = toNumber(
    item.score ?? item.similarity ?? item.relevance ?? item.distance,
    0
  );

  return {
    title: String(title ?? ''),
    score,
    source: String(source ?? '')
  };
}

function collectResultItems(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (!data || typeof data !== 'object') {
    return [];
  }

  const candidateKeys = [
    'results',
    'hits',
    'items',
    'data',
    'matches',
    'documents'
  ];

  for (const key of candidateKeys) {
    if (Array.isArray(data[key])) {
      return data[key];
    }
  }

  return [data];
}

function parseSearchOutput(stdout) {
  const text = String(stdout ?? '').trim();
  if (!text) {
    return [];
  }

  const json = parseMaybeJson(text);
  if (json !== null) {
    const items = collectResultItems(json);
    return items.map(normalizeResult).filter(Boolean);
  }

  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => ({
      title: line,
      score: 0,
      source: ''
    }));
}

function parseIndexedCount(stdout) {
  const text = String(stdout ?? '').trim();
  if (!text) {
    return 0;
  }

  const json = parseMaybeJson(text);
  if (json !== null) {
    if (Array.isArray(json)) {
      return json.length;
    }

    if (typeof json === 'object') {
      const keys = ['indexed', 'indexed_count', 'count', 'total'];
      for (const key of keys) {
        if (key in json) {
          return Math.max(0, Math.floor(toNumber(json[key], 0)));
        }
      }
    }
  }

  const indexedMatch = text.match(/indexed\D+(\d+)/i);
  if (indexedMatch) {
    return Math.max(0, parseInt(indexedMatch[1], 10));
  }

  const numberMatch = text.match(/(\d+)/);
  if (numberMatch) {
    return Math.max(0, parseInt(numberMatch[1], 10));
  }

  return 0;
}

export async function searchChromaDB(query, topK = 5) {
  try {
    const normalizedQuery = typeof query === 'string' ? query.trim() : '';
    if (!normalizedQuery) {
      return [];
    }

    const normalizedTopK = Math.max(1, Math.floor(toNumber(topK, 5)));
    const result = await runPython([
      '-m',
      'jarvis_cli',
      'semantic-search',
      normalizedQuery,
      '--top',
      String(normalizedTopK),
      '--db',
      ''
    ]);

    if (!result.ok) {
      return [];
    }

    return parseSearchOutput(result.stdout).slice(0, normalizedTopK);
  } catch {
    return [];
  }
}

export async function indexPapersToChroma(papersJsonPath) {
  try {
    const dbPath = typeof papersJsonPath === 'string' ? papersJsonPath.trim() : '';
    if (!dbPath) {
      return { success: false, reason: 'papersJsonPath is required' };
    }

    const result = await runPython([
      '-m',
      'jarvis_cli',
      'semantic-search',
      '--db',
      dbPath,
      '--index-only'
    ]);

    if (!result.ok) {
      return { success: false, reason: result.reason || 'indexing failed' };
    }

    return { success: true, indexed: parseIndexedCount(result.stdout) };
  } catch (error) {
    return {
      success: false,
      reason: String(error?.message ?? 'indexing failed')
    };
  }
}

export async function getChromaCount() {
  try {
    const script =
      'from jarvis_core.embeddings.paper_store import PaperStore; s=PaperStore(); print(s.count())';

    const result = await runPython(['-c', script]);
    if (!result.ok) {
      return 0;
    }

    const match = String(result.stdout ?? '').match(/-?\d+/);
    return match ? parseInt(match[0], 10) : 0;
  } catch {
    return 0;
  }
}
