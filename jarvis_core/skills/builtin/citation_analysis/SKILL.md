---
name: citation-analysis
description: 引用文の文脈を分類し、支持・対立・言及の関係を整理する。
triggers:
  - citation
  - references
  - support
  - contrast
---
# Citation Analysis

このスキルは、引用文の文脈を以下の3分類で整理します。

## 分類ガイド

- **Support**: 引用が主張を支持・補強している
- **Contrast**: 引用が結果に反する、もしくは反論している
- **Mention**: 関連研究として言及されているが評価は中立

## 実施手順

1. 引用文の周辺文脈（前後2-3文）を抽出する
2. 引用文が主張に与える関係を分類する
3. 重要な引用には補足メモを追加する

詳細なパターン例は `resources/CITATION_PATTERNS.md` を参照してください。
