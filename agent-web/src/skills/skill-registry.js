import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");
const SKILLS_DIR = path.join(PROJECT_ROOT, ".github", "skills");

const BUILTIN_SKILLS = [
  {
    name: "search_papers",
    description: "Search academic papers across PubMed, Semantic Scholar, OpenAlex",
    category: "research",
    command: "search",
    args_template: '"{query}" --max {max} --sources pubmed,s2,openalex'
  },
  {
    name: "semantic_search",
    description: "Search indexed papers using ChromaDB vector similarity",
    category: "research",
    command: "semantic-search",
    args_template: '"{query}" --top {top}'
  },
  {
    name: "evidence_grade",
    description: "Grade evidence level of papers (CEBM 1a-5)",
    category: "analysis",
    command: "evidence",
    args_template: "{file}"
  },
  {
    name: "citation_network",
    description: "Build citation network graph for papers",
    category: "analysis",
    command: "citation-graph",
    args_template: "{file}"
  },
  {
    name: "meta_analysis_prep",
    description: "Prepare data for meta-analysis: search, grade, score, summarize",
    category: "research",
    command: "pipeline",
    args_template: '"{query}" --max {max} --obsidian --prisma --no-summary'
  },
  {
    name: "browse_url",
    description: "Fetch and extract content from a URL",
    category: "utility",
    command: "browse",
    args_template: "{url} --json"
  },
  {
    name: "deep_research",
    description: "Autonomous multi-query deep research mode",
    category: "research",
    command: "deep-research",
    args_template: '"{query}" --max-sources {max}'
  },
  {
    name: "pdf_extract",
    description: "Extract text from PDF to Markdown",
    category: "utility",
    command: "pdf-extract",
    args_template: "{file}"
  }
];

export function listSkills() {
  const skills = [...BUILTIN_SKILLS];

  try {
    if (fs.existsSync(SKILLS_DIR)) {
      const dirs = fs.readdirSync(SKILLS_DIR, { withFileTypes: true })
        .filter((d) => d.isDirectory());
      for (const dir of dirs) {
        const skillMd = path.join(SKILLS_DIR, dir.name, "SKILL.md");
        if (fs.existsSync(skillMd)) {
          const content = fs.readFileSync(skillMd, "utf-8");
          const descMatch = content.match(/description:\s*(.+)/i) || content.match(/^>\s*(.+)/m);
          skills.push({
            name: dir.name,
            description: descMatch ? descMatch[1].trim() : dir.name,
            category: "custom",
            command: null,
            source: "file"
          });
        }
      }
    }
  } catch {
    // ignore skill discovery failures
  }

  return skills;
}

export function getSkill(name) {
  return listSkills().find((s) => s.name === name) || null;
}
