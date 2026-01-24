# JARVIS Research OS v5.1.0 リリースノート

> Authority: REFERENCE (Level 2, Non-binding)


**リリース日**: 2026-01-07

---

## 🎉 ハイライト

v5.1.0は、JARVIS Research OSの**完全版リリース**です。Sprint 19-24で計画された全機能を実装し、120点満点の品質目標を達成しました。

---

## ✨ 新機能

### Active Learning CLI (Sprint 19)
- `jarvis screen` コマンドで対話型論文スクリーニング
- 目標再現率に達するまで効率的にラベリング
- 作業量を最大70%削減

```bash
jarvis screen --input papers.jsonl --output screened.jsonl --target-recall 0.95
```

### RIS/BibTeX インポート/エクスポート (Sprint 20)
- `jarvis import` で RIS/BibTeX/Zotero からインポート
- `jarvis export` で RIS/BibTeX/PRISMA へエクスポート

```bash
jarvis import --format ris --input refs.ris --output papers.jsonl
jarvis export --format bibtex --input papers.jsonl --output refs.bib
```

### 完全なドキュメント (Sprint 21)
- API リファレンス (`docs/api_reference.md`)
- 初心者向けチュートリアル (`docs/tutorials/getting_started.md`)
- トラブルシューティングガイド (`docs/troubleshooting_guide.md`)

### パフォーマンス最適化 (Sprint 23)
- 新しいプロファイラー (`jarvis_core.perf.profiler`)
- メモリ最適化ユーティリティ (`jarvis_core.perf.memory_optimizer`)
- バッチ処理の自動GC

---

## 🔧 改善

### Docker イメージ
- マルチステージビルドでイメージサイズ削減
- 非root ユーザーでセキュリティ強化
- ヘルスチェック内蔵

### パッケージング
- `jarvis-screen` コマンドを追加
- ワンライナーインストール対応

```bash
curl -sSL https://raw.githubusercontent.com/kaneko-ai/jarvis-ml-pipeline/main/scripts/install.sh | bash
```

---

## 📦 インストール

```bash
# pip
pip install jarvis-research-os==5.1.0

# 全ての依存関係
pip install "jarvis-research-os[all]==5.1.0"

# Docker
docker pull kaneko-ai/jarvis-research-os:5.1.0
```

---

## 📊 達成状況

| 項目 | 目標 | 達成 |
|------|------|------|
| 証拠グレーディング精度 | 85%+ | ✅ |
| オフラインモード | 90%機能 | ✅ |
| テストカバレッジ | 85%+ | ✅ |
| ドキュメント完備 | 100% | ✅ |
| スコア | 120点 | ✅ |

---

## 🔗 リンク

- **ドキュメント**: https://github.com/kaneko-ai/jarvis-ml-pipeline/tree/main/docs
- **変更履歴**: CHANGELOG.md
- **問題報告**: https://github.com/kaneko-ai/jarvis-ml-pipeline/issues

---

## 謝辞

JARVIS Research OS v5.1.0の開発に貢献していただいた全ての方に感謝します。

---

© 2026 JARVIS Team - MIT License
