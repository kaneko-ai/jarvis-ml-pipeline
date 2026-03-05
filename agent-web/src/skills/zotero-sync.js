import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import dotenv from 'dotenv';
import yaml from 'js-yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.join(__dirname, '..', '..', '..');

dotenv.config({ path: path.join(projectRoot, '.env') });

const ZOTERO_API_BASE = 'https://api.zotero.org';

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseAuthors(authors) {
  if (!authors) {
    return [];
  }

  const list = Array.isArray(authors)
    ? authors
    : String(authors)
        .split(',')
        .map((name) => name.trim())
        .filter(Boolean);

  return list
    .map((author) => {
      if (!author) {
        return null;
      }

      if (typeof author === 'object') {
        const firstName = String(author.firstName ?? author.given ?? '').trim();
        const lastName = String(author.lastName ?? author.family ?? '').trim();

        if (!firstName && !lastName) {
          return null;
        }

        return {
          creatorType: 'author',
          firstName,
          lastName: lastName || firstName || 'Unknown',
        };
      }

      const raw = String(author).trim();
      if (!raw) {
        return null;
      }

      const parts = raw.split(/\s+/).filter(Boolean);
      if (parts.length === 1) {
        return {
          creatorType: 'author',
          firstName: '',
          lastName: parts[0],
        };
      }

      return {
        creatorType: 'author',
        firstName: parts.slice(0, -1).join(' '),
        lastName: parts[parts.length - 1],
      };
    })
    .filter(Boolean);
}

async function loadCollectionName() {
  const configPath = path.join(projectRoot, 'config.yaml');

  try {
    const configRaw = await fs.readFile(configPath, 'utf8');
    const config = yaml.load(configRaw);
    return String(config?.zotero?.collection ?? 'JARVIS');
  } catch {
    return 'JARVIS';
  }
}

function buildJournalArticle(paper, collectionName) {
  const title = String(paper?.title ?? '').trim() || 'Untitled';
  const creators = parseAuthors(paper?.authors);

  const item = {
    itemType: 'journalArticle',
    title,
    libraryCatalog: collectionName,
  };

  if (creators.length > 0) {
    item.creators = creators;
  }

  if (paper?.journal) {
    item.publicationTitle = String(paper.journal);
  }

  if (paper?.year) {
    item.date = String(paper.year);
  }

  if (paper?.doi) {
    item.DOI = String(paper.doi);
  }

  if (paper?.abstract) {
    item.abstractNote = String(paper.abstract);
  }

  if (paper?.url) {
    item.url = String(paper.url);
  }

  return item;
}

function makeStatusError(status, response) {
  if (status === 401) {
    return 'Zotero API authentication failed (401). Check ZOTERO_API_KEY.';
  }

  if (status === 403) {
    return 'Zotero API access forbidden (403). Check API key permissions and ZOTERO_USER_ID.';
  }

  if (status === 429) {
    const retryAfter = response.headers.get('retry-after');
    if (retryAfter) {
      return `Zotero API rate limit exceeded (429). Retry after ${retryAfter} seconds.`;
    }
    return 'Zotero API rate limit exceeded (429).';
  }

  return `Zotero API request failed with status ${status}.`;
}

export async function syncToZotero(papers) {
  const apiKey = String(process.env.ZOTERO_API_KEY ?? '').trim();
  const userId = String(process.env.ZOTERO_USER_ID ?? '').trim();

  if (!apiKey) {
    return {
      synced: 0,
      failed: 0,
      reason: 'ZOTERO_API_KEY not configured',
      errors: [],
    };
  }

  const paperList = Array.isArray(papers) ? papers : [];
  const collectionName = await loadCollectionName();
  const endpoint = `${ZOTERO_API_BASE}/users/${encodeURIComponent(userId)}/items`;

  let synced = 0;
  let failed = 0;
  const errors = [];

  if (!userId) {
    return {
      synced: 0,
      failed: paperList.length,
      errors: ['ZOTERO_USER_ID not configured.'],
    };
  }

  for (let index = 0; index < paperList.length; index += 1) {
    if (index > 0) {
      await sleep(1000);
    }

    const paper = paperList[index];
    const item = buildJournalArticle(paper, collectionName);

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Zotero-API-Key': apiKey,
        },
        body: JSON.stringify([item]),
      });

      if (!response.ok) {
        failed += 1;
        errors.push(`paper[${index}] ${makeStatusError(response.status, response)}`);
        continue;
      }

      let result;
      try {
        result = await response.json();
      } catch {
        result = null;
      }

      if (result?.successful && Object.keys(result.successful).length > 0) {
        synced += 1;
      } else if (result?.failed && Object.keys(result.failed).length > 0) {
        failed += 1;
        const failedMessage = result.failed?.['0'];
        if (typeof failedMessage === 'string') {
          errors.push(`paper[${index}] ${failedMessage}`);
        } else {
          errors.push(`paper[${index}] Zotero API rejected item.`);
        }
      } else {
        synced += 1;
      }
    } catch (error) {
      failed += 1;
      const message = error instanceof Error ? error.message : String(error);
      errors.push(`paper[${index}] Network/API error: ${message}`);
    }
  }

  return { synced, failed, errors };
}

export async function syncLatestDigest() {
  const digestsDir = path.join(projectRoot, 'agent-web', 'data', 'digests');

  try {
    const entries = await fs.readdir(digestsDir, { withFileTypes: true });
    const jsonFiles = entries.filter((entry) => entry.isFile() && entry.name.endsWith('.json'));

    if (jsonFiles.length === 0) {
      return {
        synced: 0,
        failed: 0,
        errors: ['No digest JSON files found in agent-web/data/digests/.'],
      };
    }

    let latestFile = null;
    let latestMtime = -1;

    for (const file of jsonFiles) {
      const filePath = path.join(digestsDir, file.name);
      const stat = await fs.stat(filePath);
      if (stat.mtimeMs > latestMtime) {
        latestMtime = stat.mtimeMs;
        latestFile = filePath;
      }
    }

    if (!latestFile) {
      return {
        synced: 0,
        failed: 0,
        errors: ['Unable to resolve latest digest file.'],
      };
    }

    const raw = await fs.readFile(latestFile, 'utf8');
    const digest = JSON.parse(raw);
    const topPapers = Array.isArray(digest?.topPapers) ? digest.topPapers : [];

    if (topPapers.length === 0) {
      return {
        synced: 0,
        failed: 0,
        errors: ['topPapers not found in latest digest.'],
      };
    }

    return await syncToZotero(topPapers);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      synced: 0,
      failed: 0,
      errors: [`Failed to sync latest digest: ${message}`],
    };
  }
}
