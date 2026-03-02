---
name: active-learning
description: "能動学習によりスクリーニング効率を向上させる。少量のラベル付けで関連論文を優先表示する。"
triggers:
  - screen
  - screening
  - active learning
  - label
dependencies:
  - paper-scoring
---
# Active Learning Screening

このスキルは、能動学習（Active Learning）を用いて文献スクリーニングの効率を向上させます。

## ワークフロー

1. 初期バッチの論文を提示し、include/exclude をラベル付け
2. TF-IDF + ロジスティック回帰で関連度を予測
3. 不確実性の高い論文を次のバッチとして提示
4. ラベル付けを繰り返し、モデルを更新
5. 予算（全体の50%）に達したら自動停止

## 使用方法

    jarvis screen <input.json> --auto --batch-size 5 --budget 0.5

--auto フラグを使うと、キーワードベースの自動ラベリングで動作します。
