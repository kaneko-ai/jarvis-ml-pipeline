# 🔬 JARVIS Research OS

[![CI](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/core_tests.yml/badge.svg)](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions)
[![Spec Lint](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/spec-lint.yml/badge.svg)](https://github.com/kaneko-ai/jarvis-ml-pipeline/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI-powered scientific research assistant with reproducible pipelines.**

---

## 🚀 Quickstart (CLI only)

```bash
# 1. Clone & Setup
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline
cd jarvis-ml-pipeline
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install
pip install -r requirements.lock
pip install -e .

# 3. Configure
cp .env.example .env
# Edit .env with your API keys

# 4. Run (CLI is the ONLY entry point)
python jarvis_cli.py run --goal "CD73 immunotherapy survey"

# 5. View results
python jarvis_cli.py show-run --run-id <run_id>
```

> ⚠️ **Note**: `main.py` is for demo only. Use `jarvis_cli.py` for all operations.

---

## 📁 Project Structure

```
jarvis-ml-pipeline/
├── jarvis_cli.py          # 🔑 ONLY entry point
├── jarvis_core/           # Core modules
│   ├── pipelines/         # MVP pipelines
│   ├── api/               # PubMed/arXiv clients
│   ├── extraction/        # PDF/Semantic/Claim
│   ├── analysis/          # Contradiction/Graph/Review
│   └── knowledge/         # Claim/Evidence store
├── logs/runs/{run_id}/    # Run outputs (Bundle)
├── configs/pipelines/     # Pipeline definitions
├── docs/                  # Documentation (Spec Authority)
└── tests/                 # Test suite
```

---

## 📋 Run Bundle (Output Contract)

Every run produces these files in `logs/runs/{run_id}/`:

| File | Description |
|------|-------------|
| `input.json` | Execution config |
| `result.json` | Final answer + citations |
| `eval_summary.json` | Quality gate results |
| `papers.jsonl` | Paper metadata |
| `claims.jsonl` | Extracted claims |
| `evidence.jsonl` | Evidence with locators |
| `scores.json` | Ranking features |
| `report.md` | Human-readable report |
| `warnings.jsonl` | Warnings & issues |

See [docs/BUNDLE_CONTRACT.md](docs/BUNDLE_CONTRACT.md) for schema.

---

## 🛠 Commands

| Command | Description |
|---------|-------------|
| `python jarvis_cli.py run --goal "..."` | Execute research task |
| `python jarvis_cli.py show-run --run-id ID` | View run results |
| `python jarvis_cli.py build-index --path DIR` | Build document index |

---

## 📖 Documentation

| Document | Authority | Description |
|----------|-----------|-------------|
| [SPEC_AUTHORITY.md](docs/SPEC_AUTHORITY.md) | Level 0 | Specification hierarchy |
| [BUNDLE_CONTRACT.md](docs/BUNDLE_CONTRACT.md) | Level 3 | Output contract |
| [ROADMAP_100.md](docs/ROADMAP_100.md) | Level 5 | 100-step roadmap |
| [DoD.md](docs/DoD.md) | Level 3 | Definition of Done |
| [DECISIONS.md](docs/DECISIONS.md) | Level 5 | Decision log |

---

## 🔒 Quality Gates

- **Citation required**: No answer without evidence
- **Locator required**: Evidence must have source location
- **No assertions**: Uncertain claims go to warnings

---

## 🧪 Testing

```bash
# Core tests (blocking)
pytest -m core -v

# Spec lint (doc authority check)
python tools/spec_lint.py

# All tests
pytest -v
```

---

## 🌐 Dashboard (Static UI)

P11 Dashboardは `dashboard/` 配下に分割されています。GitHub Pagesなどの静的ホスティングで利用できます。

### 変更ファイル

- `dashboard/assets/app.js`
- `dashboard/assets/ui.js`
- `dashboard/assets/styles.css`
- `dashboard/index.html`
- `dashboard/runs.html`
- `dashboard/run.html`
- `dashboard/schedule.html`
- `dashboard/feedback.html`
- `dashboard/decision.html`
- `dashboard/finance.html`
- `dashboard/settings.html`

### 動作確認手順（主要画面）

1. `dashboard/settings.html` を開き、`API_BASE` と `API_TOKEN` を保存して接続テストを実行。
2. `dashboard/index.html` で Health/KPI/Latest Runs が表示されることを確認。
3. `dashboard/runs.html` で Run一覧のフィルタ・遷移が動作することを確認。
4. `dashboard/run.html?id=<run_id>` で Progress/Logs, Claims/Evidence, QA, Exports, Submission が表示されることを確認。
5. `dashboard/feedback.html` で Feedback Risk の取り込みと High一覧表示を確認。
6. `dashboard/decision.html` と `dashboard/finance.html` で入力→実行→結果表示を確認。
7. `dashboard/schedule.html` でスケジュール作成/一覧表示を確認。

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure all tests pass
4. Submit a pull request

See [docs/DoD.md](docs/DoD.md) for merge requirements.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🌐 完全無料アーキテクチャ（GitHub Pages + Cloudflare Workers + GitHub Actions）

JARVISは、**完全無料**で動作するアーキテクチャを採用しています：

```
[GitHub Pages] → [Cloudflare Workers] → [GitHub Actions]
    ↓ UI配信      ↓ 中継API             ↓ パイプライン実行
   static       Turnstile検証         public/生成
   files        run_id生成             ↓
                workflow_dispatch     gh-pagesデプロイ
```

### アーキテクチャの利点

- ✅ **完全無料**: すべて無料枠内で動作
- ✅ **サーバーレス**: uvicorn不要、ローカルサーバー不要
- ✅ **セキュア**: Turnstileによるボット対策、GitHub Token非公開
- ✅ **スケーラブル**: Cloudflareの無料枠（1日10万リクエスト）

### セットアップガイド

#### 1. GitHub Pages設定

```bash
# リポジトリSettings → Pages
# Source: gh-pages branch / (root)
```

初回デプロイ後、`https://<username>.github.io/<repo>/` でアクセス可能。

#### 2. Cloudflare Turnstile作成

1. [Cloudflare Dashboard](https://dash.cloudflare.com/) → Turnstile
2. 新規ウィジェット作成
3. **Site key** と **Secret key** を取得
4. Domainに `<username>.github.io` を追加

#### 3. Cloudflare Worker作成

1. Cloudflare Dashboard → Workers & Pages → Create
2. `cloudflare-worker.js` の内容をコピー
3. Deploy

**Secrets設定**（Workers → Settings → Variables）：
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx  # workflow実行権限を持つPAT
GITHUB_OWNER=kaneko-ai
GITHUB_REPO=jarvis-ml-pipeline
GITHUB_WORKFLOW_FILE=jarvis_dispatch.yml
TURNSTILE_SECRET_KEY=0x4AAAAAAA...  # Turnstile Secret Key
ALLOWED_ORIGIN=https://kaneko-ai.github.io
```

**GitHub PAT作成**:
1. GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Scopes: `repo`, `workflow`

#### 4. public/index.html設定

`public/index.html` の以下を編集：
```javascript
const WORKER_URL = 'https://YOUR_WORKER.YOUR_SUBDOMAIN.workers.dev/dispatch';
const TURNSTILE_SITE_KEY = 'YOUR_TURNSTILE_SITE_KEY';
```

また、Turnstile widgetの `data-sitekey` も更新：
```html
<div class="cf-turnstile" ... data-sitekey="YOUR_TURNSTILE_SITE_KEY"></div>
```

#### 5. GitHub Actions Secrets設定

リポジトリSettings → Secrets and variables → Actions:
```
NCBI_API_KEY=your_ncbi_api_key  # PubMed API用（任意）
```

#### 6. 動作確認

1. ブラウザで `https://<username>.github.io/<repo>/` にアクセス
2. 「新規クエリ」タブで検索クエリを入力
3. Turnstileチェックボックスにチェック
4. 「パイプライン実行」ボタンをクリック
5. GitHub Actionsが起動し、数分後に結果が `public/runs/` に生成される
6. ページ更新で結果を確認

### 運用ルール（無料枠を守る）

#### UIポーリング制限
- 基本は**手動更新**
- run開始直後のみ30秒間隔で最大10回（5分間）
- Workers 1日10万リクエスト上限に余裕

#### Pages容量管理（1GB制限）
- `public/runs/` は最大50件でローテーション
- PDFなど重いファイルは置かない
- 古いrunは `build_runs_index.py` が自動カット

#### Turnstileの重要性
⚠️ **Turnstileを設定しないと、第三者があなたのActions枠を乱用します**
- Cloudflare Turnstileは無料
- ボット対策として必須
- Worker側で検証（`siteverify`）

### トラブルシューティング

**Q: Actions が起動しない**
- Worker Secrets（特に `GITHUB_TOKEN`）を確認
- GitHub PATの権限（`repo`, `workflow`）を確認

**Q: Turnstile検証が失敗する**
- `TURNSTILE_SECRET_KEY` が正しいか確認
- `ALLOWED_ORIGIN` がPages URLと一致するか確認

**Q: runs一覧が表示されない**
- `public/runs/index.json` が存在するか確認
- GitHub Pagesがデプロイされているか確認（gh-pagesブランチ）
