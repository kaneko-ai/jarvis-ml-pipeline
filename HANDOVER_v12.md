# HANDOVER_v12.md
# JARVIS Research OS - Agent-Web Handover Document
# Date: 2026-03-04
# Author: Claude (AI assistant) + kaneko yu
# Previous: HANDOVER_v11.md (2026-03-05 timestamp in file, created 2026-03-03)

---

## 0. Quick Resume (next chat starter)

Paste this at the start of your next AI chat session:

```
You are continuing development of JARVIS Research OS + Agent-Web.
Read the handover document in full:
https://github.com/kaneko-ai/jarvis-ml-pipeline/blob/main/HANDOVER_v12.md

After reading, list:
1. All completed items (with commit hashes)
2. Current in-progress task and its exact status
3. Next steps in priority order
4. All absolute rules and known bugs

Then wait for my instruction.

Context:
- Windows 11, PowerShell 5.1, Python 3.11.9, Node v24.13.1
- Project path: C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline
- agent-web/ is the only folder to modify
- Express v5 (port 3000), Copilot API (port 4141, Education Pro)
- Default model: claude-sonnet-4.6
- Free tier only, copy-paste workflow only
```

---

## 1. Project Overview

**JARVIS Research OS** is a local-first research assistant combining:
- **Python CLI backend** (v2.0.0): 22 commands for paper search, semantic search, evidence grading, Zotero sync, Obsidian export, LangGraph pipeline
- **Agent-Web** (v1.1.0): Node/Express SPA chat interface with SSE streaming, multi-model LLM support, tool integration

**Repository**: https://github.com/kaneko-ai/jarvis-ml-pipeline
**Branch**: main
**Latest commit**: 3938883a (feat: session memory [H-2])
**Related repo**: https://github.com/kaneko-ai/zotero-doi-importer

---

## 2. Environment (EXACT - do not guess)

| Item | Value |
|------|-------|
| OS | Windows 11 |
| Shell | PowerShell 5.1 |
| Python | 3.11.9 (venv at .venv/) |
| Node.js | v24.13.1 |
| Project path | C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline |
| Agent-Web path | ...\agent-web |
| Data drive | H:\ (Google Drive mount) |
| Port: Agent-Web | 3000 |
| Port: Copilot API | 4141 (GitHub Copilot Education Pro) |
| Port: Streamlit | 8501 (not active) |
| Default model | claude-sonnet-4.6 |
| Working models | claude-sonnet-4.6, gpt-4.1, o4-mini, gemini-2.0-flash |
| BLOCKED models | claude-opus-4.6, gpt-5.1 (400 errors) |
| .env keys | ZOTERO_API_KEY (set), DATALAB_API_KEY (set), OPENAI_API_KEY (empty), DEEPSEEK_API_KEY (empty) |
| SEMANTIC_SCHOLAR_API_KEY | NOT SET (uses keyless mode, 100 req/5 min limit) |

---

## 3. File Structure (agent-web/)

```
agent-web/
  public/
    css/styles.css          (~350 lines, dark/gold theme)
    js/app.js               (652 lines, SSE handler, formatMarkdown, particles)
    index.html              (~85 lines)
  src/
    server.js               (Express v5 entry point)
    db/
      database.js           (SQLite: sessions + messages tables)
    llm/
      copilot-bridge.js     (Copilot API SSE streaming, system prompt)
      jarvis-tools.js       (Python CLI bridge: searchPapers, semanticSearch, browsePage, evidenceGrade)
      paper-search.js       (NEW: PubMed + Semantic Scholar live API) <-- H-1
      llm_caller.py
      python-bridge.js
    routes/
      chat.js               (main chat endpoint with session memory + live paper search)
      sessions.js
      models.js
      skills.js
      mcp.js
      usage.js
    middleware/.gitkeep
    mcp-bridge/
      mcp-status.js
    skills/
      skill-registry.js
  tests/
  package.json
```

---

## 4. Completed Work (commit history)

### 4.1 Python CLI Backend (v2.0.0) - ALL DONE
- D1-D7 complete, 22 commands, 50 pytest passing
- ChromaDB with 36 indexed papers
- LangGraph pipeline, Zotero sync, Obsidian export
- Tag: v2.0.0 (commit edd4d0cf)

### 4.2 Agent-Web Categories 1-10 - ALL DONE
- SSE streaming chat with Copilot API
- Multi-model support (model selector)
- Session management (create/list/delete)
- Tool integration (JARVIS CLI bridge)
- Commit: 38587e79

### 4.3 Phase 1 UI Enhancements - ALL DONE
- Dark/gold theme with CSS variables
- Particle background animation
- Frosted-glass sidebar
- Inline activity timeline (SSE events displayed)
- Code block syntax highlighting
- formatMarkdown bug fixes
- resetActivity DOM cleanup
- Commit: 643c7d74

### 4.4 README.md Update [I-3] - DONE
- Added Agent-Web section before Quick Start
- Updated HANDOVER link v8 -> v11
- Updated version v1.3.0 -> v2.0.0
- Commit: 37051d0d

### 4.5 Session Memory [H-2] - DONE
- Added getMessages import to chat.js
- MAX_HISTORY_MESSAGES = 20 (last 20 user/assistant messages sent as context)
- buildHistory(sessionId) function retrieves from SQLite
- Tested: LLM correctly recalls user name from earlier in conversation
- Commit: 3938883a

### 4.6 Live Paper Search [H-1] - CODE COMPLETE, NEEDS TESTING
- paper-search.js created with searchLivePapers() and formatPapersForLLM()
- Exports verified: searchLivePapers, formatPapersForLLM
- chat.js integration done (import, isResearchQuery trigger, SSE activity events, context injection)
- **STATUS**: Code is deployed but runtime behavior not yet confirmed
- **NEXT ACTION**: Run the API test command below, then test in browser
- **Test command**:
  ```
  node -e "import('./agent-web/src/llm/paper-search.js').then(async m=>{const r=await m.searchLivePapers('PD-1 immunotherapy',2);console.log('PubMed:',r.pubmed.length,'S2:',r.semanticScholar.length);if(r.pubmed[0])console.log('Sample:',r.pubmed[0].title)}).catch(e=>console.log('ERR:',e.message))"
  ```
- If test passes: commit and push, then move to H-3
- If test fails: check error message, likely network/API issue

---

## 5. Remaining Tasks (Priority Order)

### 5.1 [H-1] Live Paper Search - VERIFY & COMMIT
- Code is in place (paper-search.js + chat.js changes)
- Need to confirm API calls work (PubMed ESearch/ESummary + Semantic Scholar Graph API)
- If working: git add + commit + push
- If failing: debug the specific API call

### 5.2 [H-3] Persistent Cross-Session Memory (2-3 sessions)
- Add SQLite tables: facts, user_preferences
- At conversation end, extract key facts via LLM
- On new session start, inject stored facts into system prompt
- Reference: Derrick Choi's 5-file structure (prompt.md, plans.md, architecture.md, implement.md, documentation.md)
- Reference: pkm_tk111's Obsidian-as-memory approach
- Reference: CoPaw/ReMe memory compaction (summarize when >70% context used)

### 5.3 [M-1] UI Animations (lower priority)
- Text appearance animation
- Reasoning accordion
- Message transition effects

### 5.4 Long-term: Research Compiler
- Input: topic string
- Auto-search latest papers (PubMed, Semantic Scholar, OpenAlex)
- Summarize and structure into textbook-style chapters
- Export to Obsidian vault
- Requires H-1, H-2, H-3 to be complete first

---

## 6. Absolute Rules (MUST FOLLOW)

1. **Files**: Only modify files inside agent-web/ directory
2. **APIs**: Free tier only (no paid API keys)
3. **PowerShell + JS escaping**:
   - PowerShell here-string (`@" ... "@`) destroys JS `$1` capture groups -> use String.fromCharCode(36) or .js temp file
   - NEVER use backtick template literals inside PowerShell here-strings
   - For complex code: write to a .js temp file, run with node, then delete
4. **formatMarkdown**: Extract code blocks FIRST, then run escapeHtml on remaining text
5. **resetActivity**: Call .remove() on DOM elements BEFORE setting references to null
6. **python -c**: Do NOT use for complex code (encoding issues on Windows)
7. **jarvis_cli/__init__.py**: Can be fully overwritten if needed
8. **User workflow**: Copy-paste -> Enter -> confirm result (no complex multi-step shell commands)
9. **Commit messages**: Follow conventional commits (feat/fix/docs prefix)

---

## 7. Known Issues & Gotchas

| Issue | Detail | Workaround |
|-------|--------|------------|
| PowerShell $ in JS | `$1` becomes empty string | Use String.fromCharCode(36)+"1" or temp .js file |
| scrapling css_first | Import error in some jarvis_cli commands | Skip scrapling-dependent features |
| Gemini rate limit | 15 RPM for gemini-2.0-flash | Add delay between calls |
| Semantic Scholar limit | 100 req/5 min without API key | Batch queries, add S2_API_KEY to .env if available |
| Drive path | H:\ mount may disconnect | Check before accessing |
| git-credential-manager | Rename warning on every push | Cosmetic only, ignore |
| LF/CRLF | Warning on git add | Cosmetic only, ignore |
| claude-opus-4.6 | Returns 400 error | Use claude-sonnet-4.6 instead |
| gpt-5.1 | Returns 400 error | Use gpt-4.1 instead |

---

## 8. Architecture & Data Flow

```
Browser (localhost:3000)
  |
  | POST /api/chat  (SSE stream)
  v
Express v5 (server.js)
  |
  +-> routes/chat.js
  |     |
  |     +-> db/database.js (SQLite: sessions, messages)
  |     |     - getMessages(sessionId) -> buildHistory() [H-2]
  |     |     - addMessage() after response
  |     |
  |     +-> llm/copilot-bridge.js
  |     |     - callCopilotLLMStream({message, model, history})
  |     |     - SSE to Copilot API (localhost:4141)
  |     |     - System prompt (Japanese, research-focused)
  |     |
  |     +-> llm/jarvis-tools.js
  |     |     - searchPapers() -> Python CLI (jarvis_cli search)
  |     |     - semanticSearch() -> Python CLI (jarvis_cli semantic-search)
  |     |     - browsePage(), evidenceGrade()
  |     |
  |     +-> llm/paper-search.js [H-1 NEW]
  |           - searchPubMed() -> PubMed E-utilities API
  |           - searchSemanticScholar() -> S2 Graph API
  |           - searchLivePapers() -> both in parallel
  |           - formatPapersForLLM() -> text block for context
  |
  +-> routes/sessions.js, models.js, skills.js, usage.js, mcp.js
```

**SSE Event Flow**: session -> activity -> tool_call -> delta (streamed tokens) -> done

**Frontend (app.js) Event Handling** (lines ~560-593):
- `session`: set sessionId
- `activity`: update inline activity timeline
- `tool_call`: show tool execution in activity
- `delta`: append to response, run formatMarkdown
- `done`: finalize, save to DOM

---

## 9. Key Config Files

### .env (project root)
```
ZOTERO_API_KEY=wc3GxeCPThtkWJnvVJQsLtLb
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
DATALAB_API_KEY=ng2yRJcuRfpvc0mCRwENWwGucyfLq5eTOXMTBB7eeyY
# SEMANTIC_SCHOLAR_API_KEY= (not set)
```

### config.yaml (project root)
- Obsidian vault path, storage locations, LLM defaults
- See HANDOVER_v11.md section for full details

### agent-web/package.json
- Express v5, better-sqlite3, node-fetch, etc.

---

## 10. Smoke Test Procedures

### Python CLI
```powershell
cd "C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline"
.venv\Scripts\activate
python -m pytest tests/ -q
python -m jarvis_cli search "PD-1" --max 3
```

### Agent-Web
```powershell
cd "C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline\agent-web"
npm run dev
# Open http://localhost:3000
# Test 1: Send "hello" -> should get response
# Test 2: Send "my name is kaneko" then "what is my name?" -> should recall (session memory)
# Test 3: Send "PD-1 immunotherapy latest papers" -> should show live_paper_search activity + paper results
```

### Paper Search API (standalone test)
```powershell
cd "C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline"
node -e "import('./agent-web/src/llm/paper-search.js').then(async m=>{const r=await m.searchLivePapers('PD-1 immunotherapy',2);console.log('PubMed:',r.pubmed.length,'S2:',r.semanticScholar.length);if(r.pubmed[0])console.log('Sample:',r.pubmed[0].title)}).catch(e=>console.log('ERR:',e.message))"
```

---

## 11. Git Commit History (recent)

```
3938883a feat(agent-web): session memory - send conversation history as LLM context [H-2]
37051d0d docs: add Agent-Web section to README, update to v2.0.0 [I-3]
643c7d74 feat(agent-web): Phase 1 UI - dark/gold theme, particles, inline activity, code highlight + HANDOVER_v11
903b68aa docs: HANDOVER_v10.md
38587e79 feat: Agent-Web v1.0.0
43342c25 docs: HANDOVER_v9.md
edd4d0cf (tag: v2.0.0) D7: v2.0.0 release
```

---

## 12. External References (from research session)

These were investigated during the session for integration ideas:

| Source | Key Idea | Applied To |
|--------|----------|------------|
| @derrickcchoi | 5-file persistent project memory (prompt.md, plans.md, architecture.md, implement.md, documentation.md) | H-3 design |
| @pkm_tk111 | Obsidian as AI agent memory/constitution | H-3 design |
| @talk_like_staw | XML tag structured prompts for Claude | System prompt improvement |
| @mgechev (skills-best-practices) | Skill files <500 lines, flat structure, third-person imperative | Future skills enhancement |
| @ctatedev (agent-browser) | Vercel agent-browser for AI browser control | Future scraping |
| @hAru_mAki_ch (Star Office UI) | Pixel art office UI concept | UI inspiration only |
| CoPaw/ReMe | Memory compaction at 70% context, hybrid search (vector 0.7 + BM25 0.3) | H-3 design |
| @LLMJunky | 70 parallel sub-agents for app building | Long-term multi-agent |

---

## 13. Session Timeline (this chat)

1. Read HANDOVER_v11.md, confirmed understanding
2. Investigated 8+ Twitter/X URLs (most blocked by robots.txt, used search fallback)
3. Synthesized external research into integration plan
4. [I-3] README.md updated - commit 37051d0d - DONE
5. [H-2] Session memory implemented - commit 3938883a - DONE (tested, LLM recalls user name)
6. [H-1] Live paper search - paper-search.js created, chat.js updated - CODE COMPLETE, RUNTIME UNVERIFIED
7. Created HANDOVER_v12.md (this document)

---

## 14. What the Next AI Must Do First

1. Read this entire document
2. Run the paper search API test (Section 10, standalone test)
3. If H-1 works: commit and push, move to H-3
4. If H-1 fails: examine error, fix the specific API call issue
5. Then implement H-3 (persistent cross-session memory)

---

*End of HANDOVER_v12.md*
