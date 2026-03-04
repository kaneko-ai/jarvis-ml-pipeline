\# JARVIS Agent Web



Browser-based chat interface for JARVIS Research OS.

Connects to GitHub Copilot (via copilot-api) for multi-model LLM access,

with LiteLLM/Gemini fallback.



\## Quick Start



```powershell

\# Terminal 1: Start Copilot proxy (first time requires GitHub OAuth)

cd agent-web

npx copilot-api@latest start --port 4141



\# Terminal 2: Start Express server

cd agent-web

npm run dev

\# → http://localhost:3000

Architecture

Browser (localhost:3000)

&nbsp;   ↓ HTTP/SSE

Express v5 (src/server.js)

&nbsp;   ├── /api/chat/stream  → copilot-bridge.js → copilot-api (:4141) → GitHub Copilot

&nbsp;   │                     → python-bridge.js  → llm\_caller.py → LiteLLM → Gemini

&nbsp;   ├── /api/sessions     → better-sqlite3 (chat-history.db)

&nbsp;   ├── /api/models       → copilot-api /v1/models + static fallback

&nbsp;   ├── /api/usage        → copilot-api /usage endpoint

&nbsp;   ├── /api/skills       → skill-registry.js (8 skills)

&nbsp;   ├── /api/mcp/servers  → mcp-status.js (5 servers, 15 tools)

&nbsp;   └── /api/health       → {"status":"ok","version":"1.0.0"}

API Endpoints

Method	Path	Description

POST	/api/chat/stream	SSE streaming chat (main endpoint)

GET	/api/sessions	List all sessions

POST	/api/sessions	Create new session

GET	/api/sessions/:id/messages	Get session messages

DELETE	/api/sessions/:id	Delete session

GET	/api/models	Available LLM models with tier info

GET	/api/usage	Copilot premium request usage

GET	/api/skills	List 8 built-in skills

GET	/api/mcp/servers	List 5 MCP servers, 15 tools

GET	/api/health	Health check

Chat Features

URL Detection: Any message containing a URL triggers jarvis browse automatically, prepending page content to the LLM prompt

Research Mode: Messages with research keywords (論文, PD-1, immunotherapy, etc.) trigger ChromaDB semantic search, prepending related papers to the prompt

Model Selection: Dropdown groups models by tier (Available / Restricted / Local Fallback)

Streaming: Real-time SSE streaming from Copilot or character-by-character from LiteLLM

Activity Timeline: Shows each processing step with elapsed time

Model Availability (Education Pro)

Tier	Models

Available (Pro)	claude-sonnet-4.6, claude-sonnet-4.5, gpt-4.1, gpt-4.1-mini, gpt-4o, o4-mini, gemini-2.0-flash, gemini-2.5-pro

Restricted (Pro+)	claude-opus-4.6, gpt-5.1, gpt-5.2-codex, gemini-3-pro-preview

Local Fallback	gemini/gemini-2.0-flash (via LiteLLM, requires GEMINI\_API\_KEY)

Default: claude-sonnet-4.6



File Structure

agent-web/

├── package.json

├── start.ps1              # Starts copilot-api + Express

├── README.md              # This file

├── src/

│   ├── server.js          # Express entry point

│   ├── routes/

│   │   ├── chat.js        # SSE streaming + research mode + URL detection

│   │   ├── sessions.js    # Session CRUD

│   │   ├── models.js      # Model list with tiers

│   │   ├── skills.js      # Skills endpoint

│   │   ├── mcp.js         # MCP servers endpoint

│   │   └── usage.js       # Copilot usage stats

│   ├── db/database.js     # SQLite CRUD

│   ├── llm/

│   │   ├── copilot-bridge.js   # Copilot API client (60s timeout)

│   │   ├── python-bridge.js    # LiteLLM fallback via Python

│   │   ├── llm\_caller.py       # Python LiteLLM caller

│   │   └── jarvis-tools.js     # JARVIS CLI wrapper (search, browse, evidence)

│   ├── skills/skill-registry.js

│   └── mcp-bridge/mcp-status.js

├── public/

│   ├── index.html

│   ├── css/styles.css

│   └── js/app.js

├── chat-history.db        # SQLite (gitignored)

└── node\_modules/          # (gitignored)

Requirements

Node.js v24+

Python 3.11+ with JARVIS venv (for CLI tools and LiteLLM fallback)

GitHub account with Copilot Pro/Education Pro (for copilot-api)

GEMINI\_API\_KEY in project root .env (for LiteLLM fallback)

Ports

Port	Service

3000	Agent-Web (Express)

4141	copilot-api (Copilot proxy)

8501	Streamlit Dashboard (separate)

