---
name: paper-scoring
description: "論文の品質スコアを算出し、エビデンスレベル・引用数・掲載誌などを総合評価する。"
triggers:
  - score
  - scoring
  - paper quality
  - ranking
dependencies:
  - evidence-grading
---
# Paper Scoring

このスキルは、論文の総合品質スコア（A～F）を自動算出します。

## 評価基準

- エビデンスレベル (CEBM 1a～5): 高いほど加点
- 引用数: 分野平均との比較で加点
- 掲載誌: インパクトファクターに基づく加点
- 研究デザイン: RCT > コホート > 症例報告
- アブストラクトの質: 構造化されているか

## 使用方法

    jarvis score <input.json>

出力には各論文の total_score (0-100) と grade (A-F) が付与されます。
