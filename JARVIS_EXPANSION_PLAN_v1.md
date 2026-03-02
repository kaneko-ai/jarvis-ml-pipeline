\# JARVIS\_EXPANSION\_PLAN\_v1.md — JARVIS Research OS 拡張計画書



\*\*作成日\*\*: 2026-03-02

\*\*前版\*\*: HANDOVER\_v5.md（2026-03-02、コミット 9220dd5a 時点）

\*\*対象リポジトリ\*\*: https://github.com/kaneko-ai/jarvis-ml-pipeline

\*\*ブランチ\*\*: `main`（直接コミット方式を継続）

\*\*現行バージョン\*\*: v1.0.0

\*\*目標バージョン\*\*: v2.0.0（全 Phase 完了後）

\*\*中間バージョン\*\*: v1.1.0（Day 1-2）→ v1.2.0（Day 3）→ v1.3.0（Day 4-5）→ v2.0.0（Day 6-7）



\*\*本書の目的\*\*: この文書を読んだ AI（Codex CLI / GitHub Copilot CLI / Claude）が、

追加の質問なしに全タスクを実装できることを保証する。

ユーザー（金子）の作業は「コマンド貼り付け → Enter → 結果確認」のみ。



---



\## 0. 実行環境ステータス（2026-03-02 確定）



| 項目 | 値 |

|------|-----|

| OS | Windows 11 |

| シェル | PowerShell 5.1 |

| Python | 3.12.3 |

| Node.js | v24.13.1 |

| プロジェクトパス | `C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline` |

| venv | `.venv`（プロジェクトルート直下） |

| venv 有効化 | `.\\.venv\\Scripts\\Activate.ps1` |

| C: 空き | 45.1 GB（460 GB 中） |

| H: | Google Drive 2TB（個人用 kanekiti1125@gmail.com） |

| G: | Google Drive 100GB（学生用 kaneko.yu3@dc.tohoku.ac.jp） |

| GPU | なし（Intel Iris Plus Graphics） |

| RAM | 16 GB LPDDR4x |

| CPU | Intel i7-1065G7（4C/8T） |



\### 0.1 利用可能な AI ツール



| ツール | プラン | モデル | 用途 |

|--------|--------|--------|------|

| Gemini API | Google AI Pro（2TB Drive 込み） | gemini-2.0-flash | JARVIS 内蔵 LLM（要約・分類） |

| OpenAI Codex CLI | ChatGPT Plus（$20/月） | GPT-5.3-Codex | コード生成・実装の自動化 |

| GitHub Copilot CLI | Education Pro（無料） | Claude Sonnet 4.6, GPT-5.3-Codex, Gemini 3 Pro 等 | コード生成・レビュー・計画 |

| Claude（本チャット） | — | Claude Opus 4.6 | 設計・計画・依頼書作成 |



\### 0.2 AI ツールのインストール状態（要確認）



```powershell

\# セッション開始時に以下を実行して状態を確認

node --version                        # v24.13.1 であること

npm --version                         # npm が使えること

codex --version 2>$null               # Codex CLI インストール済みか

copilot --version 2>$null             # Copilot CLI インストール済みか

Copy

0.3 AI ツール未インストール時のセットアップ

Copy# --- Codex CLI インストール（ChatGPT Plus で認証）---

npm install -g @openai/codex

codex  # 初回実行で「Sign in with ChatGPT」を選択



\# --- GitHub Copilot CLI インストール（Education Pro で認証）---

\# 方法1: WinGet（推奨）

winget install GitHub.Copilot

\# 方法2: npm

npm install -g @github/copilot

copilot  # 初回実行で GitHub アカウントで認証

注意: Codex CLI の Windows サポートは experimental。PowerShell で動作するが、 一部コマンド実行に問題がある場合は WSL 経由を検討。 GitHub Copilot CLI は 2026-02-25 に GA リリース済み、Windows 完全対応。



1\. ストレージ配置（確定）

C: ドライブ（460 GB / 空き 45 GB）

├── Windows, Program Files

├── Users\\kaneko yu\\

│   ├── Documents\\jarvis-work\\jarvis-ml-pipeline\\  ← プロジェクト本体

│   │   ├── .venv\\（1.35 GB）

│   │   ├── jarvis\_cli\\

│   │   ├── jarvis\_core\\

│   │   ├── config.yaml

│   │   └── .env

│   ├── .cache\\huggingface\\（0.48 GB — MiniLM-L6-v2）

│   └── Zotero\\（0.47 GB）



H: ドライブ（Google Drive 2TB / 使用 57 GB）

├── マイドライブ\\jarvis-data\\

│   ├── logs\\orchestrate\\

│   ├── logs\\pipeline\\

│   ├── pdf-archive\\        ← PDF全文保管

│   ├── exports\\json\\

│   ├── exports\\bibtex\\

│   ├── exports\\prisma\\

│   └── backup\\

├── マイドライブ\\obsidian-vault\\

│   └── papers\\

└── マイドライブ\\jarvis-ml-pipeline\\  ← 既存（参照のみ）



G: ドライブ（学生用 100GB — JARVIS では使わない）

2\. 統合対象リポジトリ 全50件マスターリスト

凡例

導入方式: pip = Python パッケージ / api = API 経由 / ref = アーキテクチャ参考 / npm = Node パッケージ

優先度: P0 = Day 1-2 / P1 = Day 3-4 / P2 = Day 5-6 / P3 = Day 7（仕上げ）

\#	リポジトリ	★	導入方式	優先度	JARVIS 統合先

1	BerriAI/litellm	25K	pip	P0	LLM 基盤統一

2	pydantic/pydantic-ai	18K	pip	P0	LLM 出力構造化

3	567-labs/instructor	11K	pip	P0	LLM 出力バリデーション

4	D4Vinci/Scrapling	10.6K	pip	P0	browse.py 更新

5	jina-ai/reader	20K	api	P0	browse フォールバック

6	VectifyAI/PageIndex	15K	pip	P1	ベクトル不要 RAG

7	chroma-core/chroma	19K	pip	P1	永続ベクトル DB

8	HKUDS/LightRAG	28K	pip	P1	グラフ RAG

9	tobi/qmd	9.9K	ref	P1	ローカル検索参考

10	opendatalab/MinerU	35K	api	P1	PDF→Markdown

11	microsoft/graphrag	28K	pip	P1	ナレッジグラフ RAG

12	unclecode/crawl4ai	60K	pip	P1	高度ウェブクロール

13	firecrawl/firecrawl	30K	api	P2	クロール API

14	langchain-ai/langgraph	25K	pip	P2	オーケストレータ改善

15	bytedance/deer-flow	15K	ref	P2	Deep Research 参考

16	assafelovic/gpt-researcher	25K	pip	P2	自律型リサーチ

17	stanford-oval/storm	20K	ref	P2	レポート自動生成

18	huggingface/smolagents	25K	pip	P2	軽量エージェント

19	crewAIInc/crewAI	30K	ref	P2	マルチエージェント参考

20	agno-agi/agno	25K	ref	P2	マルチモーダル参考

21	run-llama/llama\_index	48K	pip	P2	データコネクタ

22	infiniflow/ragflow	55K	ref	P2	RAG エンジン参考

23	logancyang/obsidian-copilot	15K	ref	P1	Obsidian 連携参考

24	khoj-ai/khoj	25K	api	P2	セカンドブレイン

25	kortix-ai/suna	17K	ref	P3	汎用エージェント参考

26	modelcontextprotocol/servers	20K	ref	P1	MCP サーバー拡張

27	anthropics/skills	73K	ref	P1	Skills 仕様準拠

28	openclaw/openclaw	217K	ref	P3	AI アシスタント参考

29	obra/superpowers	57K	ref	P3	ワークフロー参考

30	thedotmack/claude-mem	30K	ref	P2	永続メモリ参考

31	gsd-build/get-shit-done	17K	ref	P0	開発フロー管理

32	badlogic/pi-mono	14K	ref	P3	ツールキット参考

33	KeygraphHQ/shannon	24K	ref	P3	セキュリティ参考

34	openai/skills	9.3K	ref	P1	Skills カタログ参考

35	ollama/ollama	162K	ref	P3	将来のローカル LLM

36	open-webui/open-webui	124K	ref	P3	Web UI 参考

37	qdrant/qdrant	24K	ref	P3	ベクトル DB 参考

38	mastra-ai/mastra	21K	ref	P3	TS エージェント参考

39	SamuelSchmidgall/AgentLaboratory	5K	ref	P2	研究自動化参考

40	stepfun-ai/StepDeepResearch	5K	ref	P2	Deep Research 参考

41	openai/openai-agents-python	15K	pip	P2	エージェント SDK

42	langchain-ai/langchain	123K	ref	P3	エコシステム参考

43	Significant-Gravitas/AutoGPT	175K	ref	P3	プラグイン参考

44	geekan/MetaGPT	62K	ref	P3	SOP 参考

45	huggingface/text-embeddings-inference	15K	ref	P3	埋め込み高速化参考

46	deepseek-ai/DeepSeek-R1	80K	api	P1	LiteLLM 経由で利用

47	microsoft/autogen	53K	ref	P3	HITL 参考

48	allenai/olmocr	15K	ref	P3	OCR 参考

49	openai/codex	30K+	npm	P0	実装自動化ツール

50	github/copilot-cli	GA	npm	P0	実装自動化ツール

3\. Phase 構成とスケジュール

Day 1（6h）: Phase D1 — AI ツール環境構築 + LLM 基盤統一

タスク	内容	所要時間	依存

D1-1	Codex CLI + Copilot CLI インストール・認証	30min	なし

D1-2	LiteLLM 導入 + config.yaml 拡張	2h	D1-1

D1-3	PydanticAI + Instructor 導入（構造化出力）	2h	D1-2

D1-4	テスト: 全 LLM プロバイダ疎通確認	1h	D1-3

D1-5	コミット + プッシュ → v1.0.1	30min	D1-4

Day 2（6h）: Phase D2 — スクレイピング・ブラウズ強化

タスク	内容	所要時間	依存

D2-1	Scrapling v0.4 更新 + browse.py 修正	1.5h	なし

D2-2	Jina Reader API 統合（フォールバック）	1.5h	なし

D2-3	Crawl4AI 導入 + 高度クロール機能	2h	D2-1

D2-4	MCP openalex/s2 ローカルハンドラ実装	1h	なし

D2-5	コミット + プッシュ → v1.1.0	—	D2-4

Day 3（6h）: Phase D3 — RAG・ベクトル DB・PDF 解析

タスク	内容	所要時間	依存

D3-1	ChromaDB 導入 + semantic-search 永続化	2h	なし

D3-2	LightRAG 導入 + グラフ構築	2h	D3-1

D3-3	MinerU API 連携（PDF→Markdown）	1.5h	なし

D3-4	コミット + プッシュ → v1.2.0	30min	D3-3

Day 4（6h）: Phase D4 — エージェント・オーケストレータ強化

タスク	内容	所要時間	依存

D4-1	orchestrate.py を LangGraph ベースに再構築	3h	D1-2

D4-2	GPT-Researcher 統合（Deep Research モード）	2h	D4-1

D4-3	Skills execute アクション実装	1h	なし

D4-4	コミット + プッシュ	—	D4-3

Day 5（6h）: Phase D5 — 知識管理・エクスポート・Obsidian

タスク	内容	所要時間	依存

D5-1	Obsidian Vault を H: に移行 + config.yaml 更新	1h	なし

D5-2	GraphRAG 引用ネットワーク可視化	2h	D3-2

D5-3	ログ出力先を H:\\jarvis-data に変更	1h	なし

D5-4	openai-agents-python 統合（エージェント SDK）	1.5h	D4-1

D5-5	コミット + プッシュ → v1.3.0	30min	D5-4

Day 6（6h）: Phase D6 — テスト・品質保証・ドキュメント

タスク	内容	所要時間	依存

D6-1	pytest テストスイート一括作成	3h	全 Phase

D6-2	Streamlit Dashboard 更新	1.5h	D3-1, D4-1

D6-3	HANDOVER\_v6.md 作成	1h	D6-2

D6-4	README.md 更新	30min	D6-3

Day 7（6h）: Phase D7 — 仕上げ・スモークテスト・v2.0.0 リリース

タスク	内容	所要時間	依存

D7-1	全 CLI コマンド スモークテスト	2h	D6-1

D7-2	E2E パイプラインテスト（2 クエリ）	1.5h	D7-1

D7-3	バグ修正バッファ	1.5h	D7-2

D7-4	pyproject.toml version 更新 → v2.0.0	30min	D7-3

D7-5	最終コミット + プッシュ + Git タグ v2.0.0	30min	D7-4

4\. 各タスク 詳細仕様

D1-1: Codex CLI + Copilot CLI インストール・認証

目的: 2 つの AI コーディングツールを使えるようにし、以降のタスクで実装を自動化する。



手順:



Copy# 1. Codex CLI インストール

npm install -g @openai/codex



\# 2. Codex CLI 認証（ChatGPT Plus）

codex

\# → 「Sign in with ChatGPT」を選択 → ブラウザで認証



\# 3. GitHub Copilot CLI インストール

winget install GitHub.Copilot



\# 4. Copilot CLI 認証（Education Pro）

copilot

\# → GitHub アカウントで認証



\# 5. 動作確認

codex --version

copilot --version

Codex CLI の利用可能モデル（ChatGPT Plus）:



GPT-5.3-Codex（デフォルト、最高性能）

GPT-5-mini（プレミアムリクエスト消費なし）

GPT-4.1（プレミアムリクエスト消費なし）

GitHub Copilot CLI の利用可能モデル（Education Pro）:



Claude Sonnet 4.6, Claude Sonnet 4.5

GPT-5.3-Codex, GPT-5-Codex

Gemini 3 Pro, Gemini 2.5 Pro

GPT-5-mini, GPT-4.1（プレミアムリクエスト消費なし）

Copilot CLI の操作モード:



Plan mode: Shift+Tab で切替。計画立案→承認→実行

Autopilot mode: 完全自律実行（信頼できるタスク向け）

\& プレフィックス: バックグラウンドでクラウドエージェントに委任

Windows での注意:



Codex CLI は Windows experimental。PowerShell で基本動作するが問題が出たら WSL 使用

Copilot CLI は Windows GA（2026-02-25）。問題なく動作

D1-2: LiteLLM 導入 + config.yaml 拡張

目的: 全 LLM 呼び出しを LiteLLM 経由に統一し、Gemini / OpenAI / DeepSeek をシームレスに切り替え可能にする。



インストール:



Copypython -m pip install litellm

新規ファイル: jarvis\_core/llm/litellm\_client.py



Copy"""LiteLLM unified client for JARVIS."""

from \_\_future\_\_ import annotations

import os

from typing import Optional

from dotenv import load\_dotenv



load\_dotenv()





def completion(

&nbsp;   prompt: str,

&nbsp;   model: Optional\[str] = None,

&nbsp;   system: str = "You are a research assistant.",

&nbsp;   temperature: float = 0.3,

&nbsp;   max\_tokens: int = 2000,

) -> str:

&nbsp;   """Unified LLM completion via LiteLLM."""

&nbsp;   import litellm



&nbsp;   if model is None:

&nbsp;       model = os.getenv("LLM\_MODEL", "gemini/gemini-2.0-flash")



&nbsp;   messages = \[

&nbsp;       {"role": "system", "content": system},

&nbsp;       {"role": "user", "content": prompt},

&nbsp;   ]



&nbsp;   response = litellm.completion(

&nbsp;       model=model,

&nbsp;       messages=messages,

&nbsp;       temperature=temperature,

&nbsp;       max\_tokens=max\_tokens,

&nbsp;   )

&nbsp;   return response.choices\[0].message.content





def completion\_structured(

&nbsp;   prompt: str,

&nbsp;   response\_model,

&nbsp;   model: Optional\[str] = None,

&nbsp;   system: str = "You are a research assistant.",

) -> object:

&nbsp;   """Structured output via Instructor + LiteLLM."""

&nbsp;   import instructor

&nbsp;   import litellm



&nbsp;   if model is None:

&nbsp;       model = os.getenv("LLM\_MODEL", "gemini/gemini-2.0-flash")



&nbsp;   client = instructor.from\_litellm(litellm.completion)

&nbsp;   return client.chat.completions.create(

&nbsp;       model=model,

&nbsp;       messages=\[

&nbsp;           {"role": "system", "content": system},

&nbsp;           {"role": "user", "content": prompt},

&nbsp;       ],

&nbsp;       response\_model=response\_model,

&nbsp;   )

Copy

config.yaml 追加セクション:



Copyllm:

&nbsp; default\_provider: gemini

&nbsp; default\_model: "gemini/gemini-2.0-flash"

&nbsp; fallback\_model: "openai/gpt-4.1"

&nbsp; models:

&nbsp;   gemini: "gemini/gemini-2.0-flash"

&nbsp;   openai: "openai/gpt-5-mini"

&nbsp;   deepseek: "deepseek/deepseek-reasoner"

&nbsp; cache\_enabled: true

&nbsp; max\_retries: 3

&nbsp; temperature: 0.3

.env 追加:



\# 既存

GEMINI\_API\_KEY=<既存キー>

\# 新規（取得次第追加）

OPENAI\_API\_KEY=<ChatGPT Plus の API キーまたは空欄>

DEEPSEEK\_API\_KEY=<取得次第>

pipeline.py の変更点: LLMClient の呼び出しを litellm\_client.completion() に置換。



D1-3: PydanticAI + Instructor 導入

目的: LLM 出力を Pydantic モデルで型安全にバリデーションする。



インストール:



Copypython -m pip install pydantic-ai instructor

新規ファイル: jarvis\_core/llm/structured\_models.py



Copy"""Pydantic models for structured LLM outputs."""

from pydantic import BaseModel, Field

from typing import Optional

from enum import Enum





class EvidenceLevelLLM(str, Enum):

&nbsp;   LEVEL\_1A = "1a"

&nbsp;   LEVEL\_1B = "1b"

&nbsp;   LEVEL\_2A = "2a"

&nbsp;   LEVEL\_2B = "2b"

&nbsp;   LEVEL\_3 = "3"

&nbsp;   LEVEL\_4 = "4"

&nbsp;   LEVEL\_5 = "5"





class EvidenceGradeLLM(BaseModel):

&nbsp;   level: EvidenceLevelLLM

&nbsp;   confidence: float = Field(ge=0.0, le=1.0)

&nbsp;   reasoning: str

&nbsp;   study\_type: str





class PaperSummaryLLM(BaseModel):

&nbsp;   title\_ja: str = Field(description="論文タイトルの日本語訳")

&nbsp;   summary\_ja: str = Field(description="300字以内の日本語要約")

&nbsp;   key\_findings: list\[str] = Field(description="主要な発見（3-5項目）")

&nbsp;   limitations: Optional\[str] = Field(default=None, description="限界点")

&nbsp;   relevance\_score: float = Field(ge=0.0, le=1.0, description="研究テーマとの関連度")





class ContradictionResultLLM(BaseModel):

&nbsp;   is\_contradictory: bool

&nbsp;   confidence: float = Field(ge=0.0, le=1.0)

&nbsp;   explanation: str

&nbsp;   contradiction\_type: Optional\[str] = None

Copy

D1-4: テスト — 全 LLM プロバイダ疎通確認

テストスクリプト: scripts/test\_llm\_providers.py



Copy"""Test all LLM providers via LiteLLM."""

import sys

sys.path.insert(0, ".")



from jarvis\_core.llm.litellm\_client import completion, completion\_structured

from jarvis\_core.llm.structured\_models import PaperSummaryLLM



def test\_gemini():

&nbsp;   result = completion("What is PD-1 immunotherapy? Reply in 50 words.", model="gemini/gemini-2.0-flash")

&nbsp;   print(f"\[Gemini] OK: {result\[:80]}...")

&nbsp;   return True



def test\_structured():

&nbsp;   result = completion\_structured(

&nbsp;       prompt="Summarize: PD-1 is an immune checkpoint receptor.",

&nbsp;       response\_model=PaperSummaryLLM,

&nbsp;       model="gemini/gemini-2.0-flash",

&nbsp;   )

&nbsp;   print(f"\[Structured] OK: {result.title\_ja}")

&nbsp;   return True



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   passed = 0

&nbsp;   for name, fn in \[("Gemini", test\_gemini), ("Structured", test\_structured)]:

&nbsp;       try:

&nbsp;           fn()

&nbsp;           passed += 1

&nbsp;       except Exception as e:

&nbsp;           print(f"\[{name}] FAIL: {e}")

&nbsp;   print(f"\\n{passed}/2 providers OK")

Copy

D2-1: Scrapling v0.4 更新 + browse.py 修正

インストール:



Copypython -m pip install --upgrade scrapling

browse.py の変更点:



\_first(page, selector) ヘルパーを更新

PubMed abstract セレクタを div.abstract-content に修正

authors 重複問題を set() で除去

D2-2: Jina Reader API 統合

新規ファイル: jarvis\_core/browse/jina\_reader.py



Copy"""Jina Reader API for URL-to-Markdown conversion."""

import requests





def read\_url(url: str, timeout: int = 30) -> dict:

&nbsp;   """Convert URL to Markdown via Jina Reader API."""

&nbsp;   jina\_url = f"https://r.jina.ai/{url}"

&nbsp;   headers = {"Accept": "application/json"}

&nbsp;   resp = requests.get(jina\_url, headers=headers, timeout=timeout)

&nbsp;   resp.raise\_for\_status()

&nbsp;   data = resp.json()

&nbsp;   return {

&nbsp;       "title": data.get("title", ""),

&nbsp;       "content": data.get("content", ""),

&nbsp;       "url": url,

&nbsp;       "source": "jina\_reader",

&nbsp;   }

browse.py への統合: Scrapling 失敗時のフォールバックとして jina\_reader.read\_url() を呼ぶ。



D2-3: Crawl4AI 導入

インストール:



Copypython -m pip install crawl4ai

新規ファイル: jarvis\_core/browse/crawl4ai\_client.py



Copy"""Crawl4AI integration for advanced web crawling."""

from crawl4ai import WebCrawler





def crawl\_url(url: str) -> dict:

&nbsp;   """Crawl URL and extract structured content."""

&nbsp;   crawler = WebCrawler()

&nbsp;   result = crawler.run(url=url)

&nbsp;   return {

&nbsp;       "title": result.metadata.get("title", ""),

&nbsp;       "content": result.markdown,

&nbsp;       "links": result.links\[:20],

&nbsp;       "url": url,

&nbsp;       "source": "crawl4ai",

&nbsp;   }

D2-4: MCP openalex/s2 ローカルハンドラ実装

変更ファイル: jarvis\_core/mcp/hub.py



OpenAlex と Semantic Scholar の \_local\_\* ハンドラを追加:



\_local\_openalex\_search(params) → requests.get("https://api.openalex.org/works", ...)

\_local\_s2\_search(params) → requests.get("https://api.semanticscholar.org/graph/v1/paper/search", ...)

\_local\_s2\_paper(params) → 単一論文メタデータ取得

\_local\_s2\_citations(params) → 被引用論文リスト取得

D3-1: ChromaDB 導入 + semantic-search 永続化

インストール:



Copypython -m pip install chromadb

新規ファイル: jarvis\_core/embeddings/chroma\_store.py



Copy"""ChromaDB persistent vector store for JARVIS."""

import chromadb

from pathlib import Path





class JarvisChromaStore:

&nbsp;   def \_\_init\_\_(self, persist\_dir: str = None):

&nbsp;       if persist\_dir is None:

&nbsp;           persist\_dir = str(Path.home() / "Documents" / "jarvis-work" /

&nbsp;                           "jarvis-ml-pipeline" / ".chroma")

&nbsp;       self.client = chromadb.PersistentClient(path=persist\_dir)

&nbsp;       self.collection = self.client.get\_or\_create\_collection(

&nbsp;           name="jarvis\_papers",

&nbsp;           metadata={"hnsw:space": "cosine"},

&nbsp;       )



&nbsp;   def add\_papers(self, papers: list\[dict]) -> int:

&nbsp;       ids, docs, metas = \[], \[], \[]

&nbsp;       for p in papers:

&nbsp;           pid = p.get("doi") or p.get("pmid") or p.get("title", "")\[:50]

&nbsp;           if not pid:

&nbsp;               continue

&nbsp;           ids.append(str(pid))

&nbsp;           docs.append(f"{p.get('title', '')} {p.get('abstract', '')}")

&nbsp;           metas.append({

&nbsp;               "title": p.get("title", ""),

&nbsp;               "year": str(p.get("year", "")),

&nbsp;               "source": p.get("source", ""),

&nbsp;           })

&nbsp;       if ids:

&nbsp;           self.collection.upsert(ids=ids, documents=docs, metadatas=metas)

&nbsp;       return len(ids)



&nbsp;   def search(self, query: str, top\_k: int = 10) -> list\[dict]:

&nbsp;       results = self.collection.query(query\_texts=\[query], n\_results=top\_k)

&nbsp;       output = \[]

&nbsp;       for i, doc\_id in enumerate(results\["ids"]\[0]):

&nbsp;           output.append({

&nbsp;               "id": doc\_id,

&nbsp;               "score": 1 - results\["distances"]\[0]\[i] if results\["distances"] else 0,

&nbsp;               "metadata": results\["metadatas"]\[0]\[i] if results\["metadatas"] else {},

&nbsp;           })

&nbsp;       return output



&nbsp;   def count(self) -> int:

&nbsp;       return self.collection.count()

Copy

semantic\_search.py の変更: ChromaDB を使用し、過去の検索結果を永続化して横断検索可能に。



D3-2: LightRAG 導入 + グラフ構築

インストール:



Copypython -m pip install lightrag-hku

新規ファイル: jarvis\_core/rag/lightrag\_engine.py



LightRAG を使い、論文テキストからエンティティ・関係を自動抽出してグラフを構築。 naive / local / global / hybrid の 4 モードで検索。



D3-3: MinerU API 連携（PDF→Markdown）

新規ファイル: jarvis\_core/pdf/mineru\_client.py



Datalab.to API を使って PDF を Markdown/JSON に変換。 API キーは .env に MINERU\_API\_KEY として保存。



D4-1: orchestrate.py を LangGraph ベースに再構築

インストール:



Copypython -m pip install langgraph

変更ファイル: jarvis\_cli/orchestrate.py



現在の線形 5 エージェントパイプラインを、LangGraph のグラフベース構造に変更:



条件分岐: Evidence Unknown → 追加検索ループ

並列実行: SearchAgent と PDFAgent を並行

HITL: 不確実な論文のみ人間確認を要求

D4-2: GPT-Researcher 統合

インストール:



Copypython -m pip install gpt-researcher

新規 CLI コマンド: jarvis deep-research



jarvis deep-research "PD-1 resistance mechanisms" --max-sources 20 --output report.md

GPT-Researcher を JARVIS のソースクライアント（PubMed, OpenAlex 等）と組み合わせて、 自律的に検索→分析→レポート生成を行う Deep Research モードを追加。



D4-3: Skills execute アクション実装

変更ファイル: jarvis\_cli/skills.py



現在の list/match/show/context に加えて execute を実装:



jarvis skills execute --name systematic-review --query "spermidine autophagy"

SKILL.md の steps: セクションに従って、pipeline コマンドを順次実行。



D5-1: Obsidian Vault を H: に移行

手順:



Copy# 1. 既存の Vault を H: にコピー

$src = "C:\\Users\\kaneko yu\\Documents\\ObsidianVault"

$dst = "H:\\マイドライブ\\obsidian-vault"

if (Test-Path $src) {

&nbsp;   Copy-Item "$src\\\*" -Destination $dst -Recurse -Force

&nbsp;   Write-Host "Vault copied to H:" -ForegroundColor Green

}

config.yaml 更新:



Copyobsidian:

&nbsp; vault\_path: "H:\\\\マイドライブ\\\\obsidian-vault"

&nbsp; papers\_folder: "JARVIS/Papers"

&nbsp; notes\_folder: "JARVIS/Notes"

D5-2: GraphRAG 引用ネットワーク可視化

新規ファイル: jarvis\_core/rag/citation\_graph.py



GraphRAG のコミュニティ検出を利用して、論文間の引用ネットワークを構築・可視化。 出力形式: Mermaid .mmd + Obsidian 互換 .md



D5-3: ログ出力先を H: に変更

変更ファイル: config.yaml + jarvis\_cli/pipeline.py + jarvis\_cli/orchestrate.py



Copystorage:

&nbsp; logs\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\logs"

&nbsp; exports\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\exports"

&nbsp; pdf\_archive\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\pdf-archive"

&nbsp; local\_fallback: "logs"  # H: が利用不可の場合

D6-1: pytest テストスイート一括作成

テストファイル構成:



tests/

├── test\_litellm\_client.py      # LLM 統合テスト

├── test\_structured\_models.py   # Pydantic モデルテスト

├── test\_chroma\_store.py        # ChromaDB CRUD テスト

├── test\_jina\_reader.py         # Jina Reader API テスト

├── test\_browse\_updated.py      # Scrapling v0.4 テスト

├── test\_mcp\_handlers.py        # MCP openalex/s2 テスト

├── test\_pipeline\_e2e.py        # E2E パイプラインテスト

├── test\_orchestrate.py         # オーケストレータテスト

├── test\_deep\_research.py       # Deep Research テスト

└── test\_skills\_execute.py      # Skills execute テスト

各テストは pytest.mark.skipif でネットワーク/API キー不在時にスキップ。



5\. Codex CLI / Copilot CLI 用 依頼書テンプレート

以降のタスクで Codex CLI や Copilot CLI に作業を依頼する際、 以下のテンプレートに沿って依頼書（プロンプト）を渡す。



5.1 Codex CLI 用依頼書テンプレート

codex

を起動後、以下を貼り付ける:



\## Task: \[タスク ID（例: D1-2）]

\## Goal: \[目的を1文で]



\### Context

\- Project: JARVIS Research OS (jarvis-ml-pipeline)

\- Current dir: C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline

\- Python: 3.12.3, venv at .venv

\- MUST use `python -m pip install` for packages

\- MUST overwrite jarvis\_cli/\_\_init\_\_.py entirely (no partial edits)

\- DO NOT use `python -c "..."` — always create .py files



\### Files to create/modify

1\. \[ファイルパス] — \[変更内容]

2\. \[ファイルパス] — \[変更内容]



\### Requirements

\- \[要件1]

\- \[要件2]



\### Test

Run: `python scripts/test\_\[name].py`

Expected: \[期待される出力]



\### Constraints

\- No GPU available (CPU only, 16GB RAM)

\- Windows 11, PowerShell 5.1

\- Scrapling: no css\_first(), use css("sel")\[0]

\- jarvis\_core.agents.orchestrator: DO NOT import (file/dir conflict)

5.2 GitHub Copilot CLI 用依頼書テンプレート

copilot

を起動後、/plan で Plan mode に切り替えてから以下を貼り付ける:



Plan and implement task \[D1-2]: LiteLLM integration for JARVIS Research OS.



Context: This is a Python 3.12 CLI project for systematic literature reviews.

Current LLM: Gemini only. Goal: Add LiteLLM for multi-provider support.



Create these files:

1\. jarvis\_core/llm/litellm\_client.py — unified completion + structured output

2\. Update config.yaml — add llm.models section

3\. scripts/test\_llm\_providers.py — smoke test



Rules:

\- Use `python -m pip install` for packages

\- Overwrite jarvis\_cli/\_\_init\_\_.py entirely if changes needed

\- No `python -c` commands

\- Test with: python scripts/test\_llm\_providers.py

5.3 自動化スクリプト: AI 依頼書生成器

新規ファイル: scripts/generate\_task\_prompt.py



Copy"""Generate AI task prompts for Codex CLI / Copilot CLI."""

import json

import sys

from pathlib import Path



CONTEXT = """## Context

\- Project: JARVIS Research OS (jarvis-ml-pipeline)

\- Dir: C:\\\\Users\\\\kaneko yu\\\\Documents\\\\jarvis-work\\\\jarvis-ml-pipeline

\- Python: 3.12.3, venv at .venv

\- MUST use `python -m pip install` for packages

\- MUST overwrite jarvis\_cli/\_\_init\_\_.py entirely (no partial edits)

\- DO NOT use `python -c "..."` — always create .py files

\- No GPU (CPU only, 16GB RAM)

\- Windows 11, PowerShell 5.1

\- Scrapling: no css\_first(), use css("sel")\[0]

\- jarvis\_core.agents.orchestrator: DO NOT import



"""



TASKS = {

&nbsp;   "D1-2": {

&nbsp;       "goal": "Integrate LiteLLM for multi-provider LLM support",

&nbsp;       "files": \[

&nbsp;           "jarvis\_core/llm/litellm\_client.py — unified completion function",

&nbsp;           "config.yaml — add llm.models section",

&nbsp;           "scripts/test\_llm\_providers.py — smoke test",

&nbsp;       ],

&nbsp;       "packages": \["litellm"],

&nbsp;       "test": "python scripts/test\_llm\_providers.py",

&nbsp;   },

&nbsp;   "D1-3": {

&nbsp;       "goal": "Add PydanticAI + Instructor for structured LLM outputs",

&nbsp;       "files": \[

&nbsp;           "jarvis\_core/llm/structured\_models.py — Pydantic response models",

&nbsp;           "jarvis\_core/llm/litellm\_client.py — add completion\_structured()",

&nbsp;       ],

&nbsp;       "packages": \["pydantic-ai", "instructor"],

&nbsp;       "test": "python scripts/test\_structured.py",

&nbsp;   },

&nbsp;   # ... 全タスクを定義 ...

}





def generate(task\_id: str, tool: str = "codex") -> str:

&nbsp;   task = TASKS.get(task\_id)

&nbsp;   if not task:

&nbsp;       return f"Unknown task: {task\_id}"



&nbsp;   prompt = f"## Task: {task\_id}\\n## Goal: {task\['goal']}\\n\\n"

&nbsp;   prompt += CONTEXT

&nbsp;   prompt += "### Files to create/modify\\n"

&nbsp;   for i, f in enumerate(task\["files"], 1):

&nbsp;       prompt += f"{i}. {f}\\n"

&nbsp;   if task.get("packages"):

&nbsp;       prompt += f"\\n### Install first\\n"

&nbsp;       for pkg in task\["packages"]:

&nbsp;           prompt += f"python -m pip install {pkg}\\n"

&nbsp;   prompt += f"\\n### Test\\nRun: `{task\['test']}`\\n"

&nbsp;   return prompt





if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   task\_id = sys.argv\[1] if len(sys.argv) > 1 else "D1-2"

&nbsp;   tool = sys.argv\[2] if len(sys.argv) > 2 else "codex"

&nbsp;   print(generate(task\_id, tool))

Copy

使い方:



Copy# Codex CLI 用の依頼書を生成

python scripts/generate\_task\_prompt.py D1-2 codex



\# Copilot CLI 用の依頼書を生成

python scripts/generate\_task\_prompt.py D3-1 copilot



\# 生成された文をコピーして codex or copilot に貼り付け

6\. 新規 CLI コマンド一覧（v2.0.0 で追加）

コマンド	使用例	Phase

deep-research	jarvis deep-research "PD-1 resistance" --max-sources 20	D4-2

rag-index	jarvis rag-index input.json	D3-1

rag-search	jarvis rag-search "spermidine autophagy" --top 10	D3-1

graph-build	jarvis graph-build input.json --output graph.mmd	D5-2

pdf-extract	jarvis pdf-extract paper.pdf --output paper.md	D3-3

合計: 既存 20 + 新規 5 = 25 コマンド



7\. pyproject.toml 更新計画

Copy\[project]

version = "2.0.0"



dependencies = \[

&nbsp;   # 既存

&nbsp;   "requests>=2.28.0",

&nbsp;   "pyyaml>=6.0",

&nbsp;   "pydantic>=2.0.0",

&nbsp;   "jsonschema>=4.23.0",

&nbsp;   "rank-bm25>=0.2.2",

&nbsp;   "defusedxml>=0.7.1",

&nbsp;   # v2.0.0 新規

&nbsp;   "litellm>=1.50.0",

&nbsp;   "instructor>=1.5.0",

&nbsp;   "chromadb>=0.5.0",

&nbsp;   "crawl4ai>=0.4.0",

]



\[project.optional-dependencies]

rag = \[

&nbsp;   "lightrag-hku>=1.0.0",

&nbsp;   "langgraph>=0.2.0",

]

research = \[

&nbsp;   "gpt-researcher>=0.8.0",

]

pdf = \[

&nbsp;   "pymupdf>=1.22.0",

&nbsp;   # MinerU は API 経由のため pip 不要

]

Copy

注意: pandas は dependencies から削除（現在未使用、インストール失敗歴あり）。



8\. .env 最終形

\# === LLM ===

GEMINI\_API\_KEY=<既存の39文字キー>

LLM\_PROVIDER=gemini

LLM\_MODEL=gemini/gemini-2.0-flash

\# OPENAI\_API\_KEY=<取得次第>

\# DEEPSEEK\_API\_KEY=<取得次第>



\# === Zotero ===

ZOTERO\_API\_KEY=<既存キー>

ZOTERO\_USER\_ID=16956010



\# === MinerU ===

\# MINERU\_API\_KEY=<Datalab.to で取得>



\# === Jina ===

\# JINA\_API\_KEY=<任意。未設定でも無料枠あり>

9\. config.yaml 最終形（v2.0.0）

Copyobsidian:

&nbsp; vault\_path: "H:\\\\マイドライブ\\\\obsidian-vault"

&nbsp; papers\_folder: "JARVIS/Papers"

&nbsp; notes\_folder: "JARVIS/Notes"



zotero:

&nbsp; api\_key: ""

&nbsp; user\_id: ""

&nbsp; collection: "JARVIS"



search:

&nbsp; default\_sources: \[pubmed, semantic\_scholar, openalex, arxiv, crossref]

&nbsp; max\_results: 20



llm:

&nbsp; default\_provider: gemini

&nbsp; default\_model: "gemini/gemini-2.0-flash"

&nbsp; fallback\_model: "openai/gpt-4.1"

&nbsp; models:

&nbsp;   gemini: "gemini/gemini-2.0-flash"

&nbsp;   openai: "openai/gpt-5-mini"

&nbsp;   deepseek: "deepseek/deepseek-reasoner"

&nbsp; cache\_enabled: true

&nbsp; max\_retries: 3

&nbsp; temperature: 0.3



evidence:

&nbsp; use\_llm: false

&nbsp; strategy: weighted\_average



storage:

&nbsp; logs\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\logs"

&nbsp; exports\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\exports"

&nbsp; pdf\_archive\_dir: "H:\\\\マイドライブ\\\\jarvis-data\\\\pdf-archive"

&nbsp; local\_fallback: "logs"



rag:

&nbsp; chroma\_persist\_dir: ".chroma"

&nbsp; lightrag\_working\_dir: ".lightrag"

&nbsp; default\_top\_k: 10



deep\_research:

&nbsp; max\_sources: 20

&nbsp; report\_format: "markdown"

Copy

10\. スモークテスト手順（v2.0.0）

Copy# 0. 移動と仮想環境有効化

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1



\# 1. バージョン確認

python -c "import jarvis\_cli; print('CLI OK')"

codex --version

copilot --version



\# 2. AI ツール確認

python -c "from jarvis\_core.llm.litellm\_client import completion; print('LiteLLM OK')"



\# 3. ChromaDB 確認

python -c "from jarvis\_core.embeddings.chroma\_store import JarvisChromaStore; s=JarvisChromaStore(); print(f'Chroma OK, {s.count()} docs')"



\# 4. CLI ヘルプ（25 コマンド表示されること）

python -m jarvis\_cli --help



\# 5. 簡易パイプラインテスト

python -m jarvis\_cli pipeline "autophagy" --max 3 --no-summary



\# 6. RAG テスト

python -m jarvis\_cli rag-search "PD-1 immunotherapy" --top 5



\# 7. MCP テスト（openalex 含む）

python -m jarvis\_cli mcp invoke --tool openalex\_search --params-file test\_params.json



\# 8. Deep Research テスト

python -m jarvis\_cli deep-research "spermidine autophagy aging" --max-sources 5



\# 9. pytest

python -m pytest tests/ -v --tb=short



\# 10. H: ドライブのログ確認

Get-ChildItem "H:\\マイドライブ\\jarvis-data\\logs" -Recurse | Select-Object -First 5

Copy

11\. 日次作業フロー（ユーザー金子の行動）

毎日の開始手順

Copy# 1. プロジェクト移動 + venv 有効化

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1



\# 2. Git 状態確認

git status

git log --oneline -3



\# 3. 当日のタスク依頼書を生成

python scripts/generate\_task\_prompt.py D\[X]-\[Y] codex

\# → 出力をコピー



\# 4-A. Codex CLI で実装

codex

\# → 依頼書を貼り付け → 実装完了を待つ



\# 4-B. または Copilot CLI で実装

copilot

\# → /plan → 依頼書を貼り付け → 計画確認 → 承認



\# 5. テスト実行

python scripts/test\_\[task].py



\# 6. コミット + プッシュ

git add -A

git commit -m "D\[X]-\[Y]: \[内容]"

git push origin main

各日の作業量

日	Phase	タスク数	見積時間	成果物

Day 1	D1	5	6h	v1.0.1（LLM 基盤）

Day 2	D2	5	6h	v1.1.0（スクレイピング強化）

Day 3	D3	4	6h	v1.2.0（RAG + PDF）

Day 4	D4	4	6h	（エージェント強化）

Day 5	D5	5	6h	v1.3.0（知識管理）

Day 6	D6	4	6h	（テスト + ドキュメント）

Day 7	D7	5	6h	v2.0.0 リリース

12\. 実装時の絶対ルール（HANDOVER\_v5 から継承 + 追加）

PowerShell から python -c "..." で複雑なコードを実行しない。必ず .py ファイルを作成して python filename.py で実行。

jarvis\_cli/\_\_init\_\_.py は全文上書きのみ。write\_\*.py スクリプト方式を厳守。

パッケージインストールは python -m pip install。

logs/ ディレクトリは .gitignore で除外。

Gemini API: 1,500 req/日、15 RPM。

Semantic Scholar: 100 req/5min。

jarvis\_core.agents.orchestrator は import 不可。

Scrapling の css\_first() は存在しない。css("selector")\[0] を使用。

MCP invoke で JSON → --params-file 経由。

write\_\*.py で triple-quoted string 内に """ を含めない。

Codex CLI: Windows experimental。問題が出たら PowerShell → WSL 切り替え。

Copilot CLI: Plan mode で計画確認してから Autopilot に移行。

H: ドライブ（Google Drive）はオフラインで遅延あり。ログ書き込み失敗時は local\_fallback を使用。

Codex CLI の Plus 制限: 週あたりの Codex セッション数に上限あり。連続利用で制限に達した場合は Copilot CLI に切り替え。

ChromaDB: SQLite ベース。.chroma/ はプロジェクトルートに配置（C: の高速アクセス用）。

13\. 既知の問題と回避策（HANDOVER\_v5 継承 + 新規）

\#	問題	原因	回避策

1	agents.py / agents/ 衝突	ファイルとディレクトリ共存	import しない

2	Ollama 未インストール	GPU なし	LiteLLM 経由で API 利用

3	基礎研究が全て Level 5	ルールベースの限界	構造化出力で LLM 判定を追加

4	Orchestrate で Evidence unknown	abstract 空	OpenAlex 併用

5	S2 429	無料枠制限	指数バックオフ（実装済み）

6	PS 5.1 JSON	クォート壊れ	--params-file 使用

7	init.py 部分挿入失敗	文字列操作	全文上書き

8	pip venv 外インストール	修復済み	python -m pip

9	Scrapling css\_first()	API 非互換	css()\[0]

10	PubMed browse abstract 空	セレクタ不一致	D2-1 で修正

11	MCP openalex/s2 未テスト	ハンドラ未実装	D2-4 で実装

12	NEW Codex CLI Windows	experimental	問題時 WSL

13	NEW H: ドライブ遅延	Google Drive 同期	local\_fallback

14	NEW Codex Plus 制限	週間セッション上限	Copilot CLI に切替

15	NEW pandas 不要	インストール失敗歴	dependencies から削除

14\. 成功基準（v2.0.0 リリース判定）

\#	基準	検証方法

1	25 CLI コマンドが --help で表示	jarvis --help

2	jarvis pipeline が 7 ステップ完走	E2E テスト

3	LiteLLM 経由で Gemini 要約生成	--provider gemini

4	ChromaDB に論文が永続保存	jarvis rag-search

5	Jina Reader がフォールバック動作	Scrapling 失敗を模擬

6	MCP openalex/s2 が応答返却	jarvis mcp invoke

7	Deep Research がレポート生成	jarvis deep-research

8	ログが H: に保存	Get-ChildItem H:\\...\\logs

9	Obsidian ノートが H: に出力	jarvis pipeline --obsidian

10	pytest 全テスト PASS	python -m pytest tests/ -v

11	git tag v2.0.0 が push 済み	git tag -l

15\. Day 1 即時実行コマンド

以下をそのまま貼り付けて Day 1 を開始してください:



Copy# === Day 1 準備 ===

cd "C:\\Users\\kaneko yu\\Documents\\jarvis-work\\jarvis-ml-pipeline"

.\\.venv\\Scripts\\Activate.ps1

git status



\# === D1-1: AI ツールインストール ===

npm install -g @openai/codex

winget install GitHub.Copilot



\# インストール確認

codex --version

copilot --version



\# === D1-2 準備: LiteLLM インストール ===

python -m pip install litellm instructor pydantic-ai



\# インストール確認

python -c "import litellm; print(f'LiteLLM {litellm.\_\_version\_\_}')"

python -c "import instructor; print('Instructor OK')"

上記が全部成功したら、次は codex を起動して D1-2 の依頼書を貼り付けます。 その依頼書は私が生成します。



16\. 用語集（追加分）

用語	説明

LiteLLM	100+ LLM プロバイダを統一 API で呼び出すゲートウェイライブラリ

Instructor	LLM 出力を Pydantic モデルに構造化するライブラリ

PydanticAI	Pydantic 社の GenAI エージェントフレームワーク

ChromaDB	SQLite ベースの軽量永続ベクトルデータベース

LightRAG	グラフベースの軽量 RAG フレームワーク（HKU 開発）

GraphRAG	Microsoft のナレッジグラフ強化 RAG

Crawl4AI	LLM 対応ウェブクローラー

Jina Reader	URL→Markdown 変換 API

MinerU	PDF→Markdown 変換ツール（109言語 OCR 対応）

GPT-Researcher	自律型ウェブリサーチエージェント

LangGraph	LangChain のグラフベースオーケストレーション

Codex CLI	OpenAI のターミナル型コーディングエージェント

Copilot CLI	GitHub のターミナル型 AI 開発支援ツール

GPT-5.3-Codex	Codex CLI のデフォルトモデル（2026-02 最新）

Plan mode	Copilot CLI の計画モード（Shift+Tab で切替）

Autopilot mode	Copilot CLI の自律実行モード

End of JARVIS\_EXPANSION\_PLAN\_v1.md





---



