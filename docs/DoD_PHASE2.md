# Definition of Done: Phase 2 (Intelligence Upgrade)

> Authority: Phase 2 Completion Criteria  
> Date: 2024-12-28

---

## Phase 2 完了条件

Phase 2（賢さ強化）は、以下のすべてを満たした時点で「完了」とする。

---

## 1. Evidence-Based Output (根拠ベース出力)

- [x] **Claim Unit Schema**: 主張の最小単位が定義されている
- [x] **Evidence Unit Schema**: 根拠の最小単位が定義されている
- [x] **Evidence Grading**: 根拠の強さ（Strong/Medium/Weak/None）を自動評価
- [ ] **Report Generation**: すべての結論にEvidence IDが明記される

### 検証方法
```bash
# スキーマ検証
python tools/schema_lint.py logs/runs/{run_id}/

# 根拠支持率確認
cat logs/runs/{run_id}/eval_summary.json | jq '.metrics.support_rate'
# => 0.90以上であること
```

---

## 2. Domain-Specific Intelligence (ドメイン知能)

- [x] **Rubrics Definition**: 免疫・がん領域の評価軸（5軸）が定義されている
- [x] **Feature Extraction**: 論文からRubric特徴量を抽出できる
- [ ] **Subscores in Report**: レポートに軸別スコア（model_tier, evidence_type等）が表示される

### 検証方法
```bash
# features.jsonl が生成されることを確認
ls logs/runs/{run_id}/features.jsonl

# スコア内訳確認
cat logs/runs/{run_id}/scores.json | jq '.subscores'
```

---

## 3. Reproducible Ranking (再現可能なランキング)

- [x] **Golden Dataset**: 人間ラベル付きのランキングデータ（最低7論文）
- [x] **LightGBM Ranker**: Learning-to-Rankモデルの訓練・推論が可能
- [x] **CLI Command**: `jarvis_cli.py train-ranker` で訓練できる
- [ ] **Ranking Explanation**: レポートに「なぜこの順位か」の理由が表示される

### 検証方法
```bash
# ランカー訓練
python jarvis_cli.py train-ranker --dataset evals/golden_sets/cd73_set_v1.jsonl --output models/ranker_v1.txt

# 訓練成功を確認
ls models/ranker_v1.txt
```

---

## 4. Uncertainty & Cost Control (不確実性・コスト制御)

- [x] **Inference Policy**: トークン予算・エスカレーション規則が定義されている
- [x] **Escalation Logic**: 品質低下時に追加推論をトリガーできる
- [ ] **Cost Report**: run完了後にコスト内訳（cost_report.json）が出力される
- [ ] **Uncertainty Labels**: 低信頼度のClaimに明示的なラベルが付く

### 検証方法
```bash
# cost_report.json 確認
cat logs/runs/{run_id}/cost_report.json | jq '.total_tokens'

# 予算超過でfailすることを確認（テスト）
```

---

## 5. Robustness to Tricks (罠問題への耐性)

- [x] **Contradiction Set**: 相反する主張を含む論文ペア（3問以上）
- [x] **Overclaim Set**: 過大主張の検出問題（4問以上）
- [x] **No Evidence Set**: 根拠不足の検出問題（3問以上）
- [ ] **Trick Set Evaluation**: 上記すべてで適切に対応できることを確認

### 検証方法
```bash
# 罠セット評価（将来実装）
python -m pytest tests/test_trick_sets.py -v

# 期待される挙動:
# - Contradiction: 矛盾を検出し、両論を記載
# - Overclaim: 因果の飛躍を検出し、保守的に記述
# - No Evidence: 「不明」と明記
```

---

## 6. Documentation & CI (ドキュメント・CI)

- [x] **QUALITY_BAR_PHASE2.md**: Phase 2品質基準が文書化されている
- [x] **Rubrics YAML**: ドメイン評価軸が形式的に定義されている
- [x] **Golden Sets**: 評価データセットが `evals/` に配置されている
- [x] **Trick Sets**: 罠問題セットが `evals/trick_sets/` に配置されている
- [ ] **CI Integration**: GitHub Actionsでtrick set評価が自動実行される

---

## Phase 2 完了チェックリスト

### Core Implementation ✅
- [x] Claim/Evidence Schema
- [x] Evidence Grading
- [x] Domain Rubrics
- [x] LightGBM Ranker
- [x] Inference Policy
- [x] Escalation Logic

### Evaluation Sets ✅
- [x] Golden Ranking Dataset (7 papers)
- [x] Contradiction Set (3 cases)
- [x] Overclaim Set (4 cases)
- [x] No Evidence Set (3 cases)

### Integration (Remaining) 🔄
- [ ] Report with Evidence IDs
- [ ] Subscores in scores.json
- [ ] Ranking Explanation in report
- [ ] cost_report.json output
- [ ] Uncertainty Labels
- [ ] Trick Set Evaluation Tests
- [ ] CI Integration

---

## Phase 2 完了宣言の条件

以下が**すべて**満たされた時、Phase 2は完了とする：

1. ✅ **6つのCore実装**が完了
2. ✅ **4種類のEval Sets**が揃っている
3. [ ] **Integration項目**のうち最低4つが動作確認済み
4. [ ] **Trick Sets**で80%以上が期待通りの挙動を示す

---

*Phase 2 DoD - 「賢さ」を測れる形にした*
