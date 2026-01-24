# JARVIS Decision Log

> Authority: REFERENCE (Level 2, Non-binding)


## 2024-12-27: Foundation to Scale 9フェーズ実装

### 決定事項

1. **公式MVP = e2e_oa10**
   - fullstackは実験用に格下げ
   - PR必要CIはe2e_oa10のみ

2. **bundle必要8ファイル**
   - input.json, papers.jsonl, claims.jsonl, evidence.jsonl
   - scores.json, report.md, warnings.jsonl, summaries.jsonl

3. **legacy握りつぶし撤廃**
   - LEGACY_MUST_PASS環境変数で制御
   - main push時はtrue（fail化）

4. **外部API依存分離**
   - PR必要CI: fixture使用
   - Nightly: 実データ

### 背景
- CIの偶然import依存を排除
- 品質回帰を検知可能に
- 成果物駆動で検収

### 次回レビュー
- 2025-01-15: legacy完全撤廃評価
