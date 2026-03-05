import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRootPath = path.join(__dirname, '..', '..', '..');
const configPath = path.join(projectRootPath, 'config.yaml');
const digestDirectoryPath = path.join(projectRootPath, 'agent-web', 'data', 'digests');
const digestFileNamePattern = /^digest-(\d{4}-\d{2}-\d{2})\.md$/;

function getObsidianConfig() {
  if (!fs.existsSync(configPath)) {
    throw new Error(`config.yaml not found: ${configPath}`);
  }

  let config;
  try {
    const configText = fs.readFileSync(configPath, 'utf8');
    config = yaml.load(configText) || {};
  } catch (error) {
    throw new Error(`Failed to parse config.yaml: ${error?.message || String(error)}`);
  }

  const vaultPath = String(config?.obsidian?.vault_path || '').trim();
  const notesFolder = String(config?.obsidian?.notes_folder || '').trim();

  if (!vaultPath) {
    throw new Error('obsidian.vault_path is missing in config.yaml');
  }
  if (!notesFolder) {
    throw new Error('obsidian.notes_folder is missing in config.yaml');
  }

  if (!fs.existsSync(vaultPath)) {
    console.warn(`Obsidian vault path does not exist: ${vaultPath}`);
    throw new Error(`Obsidian vault not found: ${vaultPath}`);
  }

  return { vaultPath, notesFolder };
}

function extractDigestDateFromFileName(digestFileName) {
  const matches = digestFileName.match(digestFileNamePattern);
  if (!matches) {
    throw new Error(`Invalid digest filename: ${digestFileName}. Expected digest-YYYY-MM-DD.md`);
  }
  return matches[1];
}

function createDigestFrontmatter(digestDate) {
  return `---\ntitle: "Daily Digest ${digestDate}"\ndate: ${digestDate}\ntags:\n  - daily-digest\n  - JARVIS\ntype: digest\n---\n\n`;
}

export function exportDigestToObsidian(digestMarkdownPath) {
  try {
    if (!digestMarkdownPath || typeof digestMarkdownPath !== 'string') {
      throw new Error('digestMarkdownPath must be a non-empty string');
    }

    const { vaultPath, notesFolder } = getObsidianConfig();
    const sourcePath = path.isAbsolute(digestMarkdownPath)
      ? digestMarkdownPath
      : path.join(projectRootPath, digestMarkdownPath);

    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Digest markdown file not found: ${sourcePath}`);
    }

    const digestFileName = path.basename(sourcePath);
    const digestDate = extractDigestDateFromFileName(digestFileName);
    const sourceMarkdown = fs.readFileSync(sourcePath, 'utf8');

    const digestsOutputDirectory = path.join(vaultPath, notesFolder, 'Digests');
    fs.mkdirSync(digestsOutputDirectory, { recursive: true });

    const outputPath = path.join(digestsOutputDirectory, `digest-${digestDate}.md`);
    const outputContent = `${createDigestFrontmatter(digestDate)}${sourceMarkdown}`;
    fs.writeFileSync(outputPath, outputContent, 'utf8');

    return { success: true, outputPath };
  } catch (error) {
    const message = error?.message || String(error);
    if (message.startsWith('Obsidian vault not found: ')) {
      throw error;
    }
    throw new Error(`Failed to export digest to Obsidian: ${message}`);
  }
}

export function exportLatestDigest() {
  if (!fs.existsSync(digestDirectoryPath)) {
    throw new Error(`Digest directory not found: ${digestDirectoryPath}`);
  }

  const digestFiles = fs
    .readdirSync(digestDirectoryPath, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith('.md'))
    .map((entry) => entry.name)
    .sort((first, second) => second.localeCompare(first));

  if (digestFiles.length === 0) {
    throw new Error(`No digest markdown files found in: ${digestDirectoryPath}`);
  }

  const latestDigestPath = path.join(digestDirectoryPath, digestFiles[0]);
  return exportDigestToObsidian(latestDigestPath);
}
