> Authority: ROADMAP (Level 5, Non-binding)

# Human Tasks Playbook (2026-02-12)

## 前提
- このドキュメントは「Codex が実行できない操作」を人手で完了するための手順書です。
- 現在日時の実測基準: 2026-02-12 JST（= 2026-02-11 UTC）。

## 現在地と目標の差分

| 項目 | 現在地（実測） | 目標 | 差分 |
|---|---:|---:|---:|
| jarvis_core カバレッジ | 75.99% | 85% | -9.01pt |
| CI連続グリーン（workflow `CI`） | 10回（最新 run: `21946264034`） | 10回 | 0回 |
| CI連続グリーン（workflow `CI Matrix`） | 100回以上（直近100件成功, 最新 run: `21946264057`） | 10回 | 達成 |
| Docker 検証 | 完了（2026-02-12, 別チャット実施） | 完了 | 達成 |
| PyPI公開 | 完了（2026-02-12, 別チャット実施） | 本番公開完了 | 達成 |
| `.env`履歴パージ | 履歴除去済み（2026-02-12） | 履歴完全除去 | 達成 |

---

## 1. SEC-001 `.env` 履歴パージ（最優先）

### 状態
- ✅ 完了（2026-02-12）
- 実施内容:
  - `.env` 履歴削除
  - LFS欠損参照 `tests/fixtures/sample.pdf` も履歴から削除
  - `main` / tags force-push 反映
  - `origin/main` で `.env` と `tests/fixtures/sample.pdf` の履歴が空であることを確認

### Codexが実行できない理由（実施時）
- `main` への force push は本番運用影響があり、最終承認が必要だった。

### あなたの作業（PowerShell）
1. **新規クリーンクローンを作る**（既存作業ツリーを壊さないため）
```powershell
cd $HOME\Documents
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git jarvis-ml-pipeline-secfix
cd jarvis-ml-pipeline-secfix
```
2. **履歴から `.env` を除去**
```powershell
# 未導入なら: pip install git-filter-repo
git filter-repo --path .env --invert-paths --force
```
3. **残存確認**
```powershell
git log --all --full-history -- .env
# 何も出なければOK
```
4. **remote再設定（filter-repo後に消えるため）**
```powershell
git remote add origin https://github.com/kaneko-ai/jarvis-ml-pipeline.git
```
5. **force push（main + tags）**
```powershell
git push origin main --force
git push origin --tags --force
```
6. **秘密情報ローテーション**
- 実キーを一度でも `.env` に置いた場合は、全キー再発行。

---

## 2. TD-020 Docker検証

### 状態
- ✅ 完了（2026-02-12、別チャットで実施済み）
- 実施内容: Docker build / コンテナ内テストまで完了

### 参考（再実施が必要な場合）
1. Docker Desktop をインストール
2. 動作確認
```powershell
docker --version
docker run hello-world
```
3. リポジトリでビルド
```powershell
cd C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline
docker build -t jarvis-test .
```
4. コンテナ内テスト
```powershell
docker run --rm jarvis-test python -m pytest tests/ --ignore=tests/e2e --ignore=tests/integration -q -x
```

---

## 3. TD-022 PyPI公開

### 状態
- ✅ 完了（2026-02-12、別チャットで実施済み）
- 実施内容: Secrets / Environments 設定、および `Publish to PyPI` 実行まで完了

### Codex側で完了済み
- `uv run python -m build` 成功
- `uv run --with twine twine check dist/*.whl dist/*.tar.gz` 成功

### 参考（再実施が必要な場合）
1. PyPIでAPIトークン発行
2. GitHub Secrets登録
  - `PYPI_API_TOKEN`
  - `TEST_PYPI_API_TOKEN`（任意だが推奨）
3. GitHub Environments作成
  - `pypi`
  - `test-pypi`
4. `Publish to PyPI` workflow 実行

---

## 4. TD-010 CI 10回連続グリーン

### 現在値（実測: 2026-02-12 JST）
- ✅ `CI` workflow: 10回連続成功（最新 run: `21946264034`）
- ✅ `CI Matrix` workflow: 100回以上連続成功（直近100件、最新 run: `21946264057`）

### あなたの作業
1. ✅ GitHub Actions で `main` の `CI` 実行履歴を確認
2. ✅ 赤が出たらログ原因修正
3. ✅ 10回連続成功まで観測（達成）

---

## 5. 補足（品質指標）

- `scripts/run_regression.py` は現状プレースホルダ実装（固定値ベース）です。
- 2026-02-12 実行値:
  - `success_rate`: 1.0
  - `claim_precision`: 0.7
  - `citation_precision`: 0.8
- `check_quality_bar.py` は `entity_hit_rate` 未供給のため現状Fail。

### Windows 文字コード注意
- 一部スクリプトは記号文字出力で `cp932` エラーになる場合があります。
- その場合は UTF-8 モードで実行してください。
```powershell
$env:PYTHONUTF8='1'
uv run python scripts/check_quality_bar.py --metrics reports/eval/latest/metrics.json
uv run python scripts/scan_secrets.py
```

---

## 6. Update (2026-02-12)
- TD-020 Docker validation: COMPLETED (done in another chat)
- TD-022 PyPI publish setup: COMPLETED (done in another chat)
- Verification executed in this session:
  - `uv run pytest -q` -> `6392 passed, 468 skipped`
  - `uv build` -> success (`sdist` and `wheel` created)
- Remaining human tasks in this playbook: none


---

## 2026-02-13 Update (Landing Page API)
- ランディングページのデモをバックエンドAPI呼び出し対応へ拡張
- API到達不可時は既存ブラウザロジックへ自動フォールバック
- 実装詳細は `docs/README.md` の `Landing Page & Demo API` セクションに統合
