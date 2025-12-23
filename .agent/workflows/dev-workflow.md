---
description: JARVIS開発ワークフロー - 自動実行モード
---

// turbo-all

# 開発作業

1. コード変更を実施
2. テスト実行: `pytest -m core --tb=short -q`
3. Git追加: `git add .`
4. コミット: `git commit -m "message"`
5. プッシュ: `git push origin main`

# パイプライン実行

1. 設定確認: `cat pipeline_config.yaml`
2. Dry-run: `python run_pipeline.py --dry-run`
3. 本番実行: `python run_pipeline.py`

# デプロイ

1. Dockerビルド: `docker build -t jarvis:latest .`
2. テスト: `docker run --rm jarvis:latest python -c "import jarvis_core; print('OK')"`
3. プッシュ: `docker push`
