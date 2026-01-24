# JARVIS Research OS リリースチェックリスト

> Authority: REFERENCE (Level 2, Non-binding)


## リリース前チェック

### コード品質
- [ ] 全テスト通過: `uv run python -m pytest tests/ -v`
- [ ] 型チェック: `mypy jarvis_core/`
- [ ] リント: `ruff check .`
- [ ] フォーマット: `black --check .`

### ドキュメント
- [ ] README.md 更新
- [ ] CHANGELOG.md 更新
- [ ] API リファレンス最新化
- [ ] バージョン番号統一

### セキュリティ
- [ ] 依存関係の脆弱性チェック: `pip-audit`
- [ ] シークレットのハードコーディングなし
- [ ] SECURITY.md 確認

### パッケージング
- [ ] pyproject.toml バージョン更新
- [ ] 依存関係の互換性確認
- [ ] ビルドテスト: `python -m build`

---

## リリースプロセス

### 1. バージョンタグ作成
```bash
git tag -a v5.1.0 -m "Release v5.1.0"
git push origin v5.1.0
```

### 2. PyPI 公開
```bash
python -m build
twine upload dist/*
```

### 3. Docker イメージ公開
```bash
docker build -t kaneko-ai/jarvis-research-os:5.1.0 .
docker push kaneko-ai/jarvis-research-os:5.1.0
docker tag kaneko-ai/jarvis-research-os:5.1.0 kaneko-ai/jarvis-research-os:latest
docker push kaneko-ai/jarvis-research-os:latest
```

### 4. GitHub Release 作成
- タイトル: `v5.1.0`
- リリースノート: RELEASE_NOTES_v5.1.md からコピー
- アセット: wheel ファイルを添付

---

## リリース後確認

- [ ] PyPI インストール確認: `pip install jarvis-research-os==5.1.0`
- [ ] Docker 動作確認: `docker run kaneko-ai/jarvis-research-os:5.1.0 --help`
- [ ] CLI 動作確認: `jarvis run --goal "test"`
- [ ] 依存関係解決確認

---

## ロールバック手順

問題発生時:
```bash
# PyPI から削除 (24時間以内のみ)
pip index versions jarvis-research-os
# PyPI サポートに連絡

# Docker タグ更新
docker tag kaneko-ai/jarvis-research-os:5.0.0 kaneko-ai/jarvis-research-os:latest
docker push kaneko-ai/jarvis-research-os:latest
```
