# JARVIS Quality Bar - Phase 2 (Intelligence)

> Authority: REFERENCE (Level 2, Non-binding)


> Authority: DEC-006, MASTER_SPEC v1.2  
> Date: 2024-12-28

---

## Phase 2 品質基準

Phase 2（賢さ強化）では、Phase 1の基盤（10ファイル契約、Quality Gate）に加え、以下の**知的品質**を満たす必要がある。

---

## 1. Evidence Support (根拠支持率)

| 指標 | 閾値 | 説明 | 失敗時の挙動 |
|------|------|------|-------------|
| **Support Rate** | ≥ 0.90 | 全Claimに対する根拠付き率 | `FAIL` (UnsupportedClaim) |
| **Unsupported Claims** | = 0 | 根拠が全くないClaim | `FAIL` (HallucinationRisk) |
| **Weakly Supported** | ≤ 10% | 根拠が弱いClaim（Medium未満） | `WARNING` |

### 評価方法
```python
# Evidence Grading Stage が自動計算
# logs/runs/{run_id}/evidence.jsonl に strength 付与
# eval_summary.json に support_rate を記録
```

---

## 2. Evidence Strength Grading

各Evidenceは以下の4段階で評価される：

| Grade | 条件 |
|-------|------|
| **Strong** | Direct evidence, same paper, quote > 100 chars |
| **Medium** | Direct evidence OR quote > 50 chars |
| **Weak** | Indirect/Prior, quote > 20 chars |
| **None** | No valid evidence |

Claimは最低でも以下のいずれかを満たす必要がある：
- Strong evidence が1つ以上
- Medium evidence が2つ以上

---

## 3. Provenance Precision (引用精度)

| 指標 | 閾値 | 説明 |
|------|------|------|
| **Locator Precision** | 100% | すべてのEvidenceに有効なlocator（section + paragraph） |
| **Quote Span Validity** | 100% | quote_span が実際の論文テキストと一致 |

---

## 4. Report Quality (レポート品質)

report.md には以下が**必要**：

- [ ] 各結論段落に **Evidence ID列** が明記される
- [ ] 根拠不足の主張は「不明」「推測」とラベル付け
- [ ] 推測が必要な場合は `> [!WARNING]` アラート使用

### 悪い例（Phase 1）
```markdown
CD73は腫瘍微小環境で重要である。
```

### 良い例（Phase 2）
```markdown
CD73は腫瘍微小環境で重要である [^ev_1a2b3c, ^ev_4d5e6f]。

> [!NOTE]
> Evidence: PMID:36991446 (Section: Introduction, P2)
```

---

## 5. Contradiction Detection (矛盾検出)

| 指標 | 閾値 | 説明 |
|------|------|------|
| **Contradiction Rate** | ≤ 5% | Evidence間で矛盾するClaim |
| **Contradiction Handling** | 100% | 矛盾が検出されたら明示的に報告 |

---

## DoD (Phase 2 Step 2)

- [x] Evidence Grading Stage 実装
- [x] Support Rate 計算ロジック
- [x] QUALITY_BAR_PHASE2.md 作成
- [ ] Report生成規約の更新（Evidence ID表示）
- [ ] Contradiction検出ロジック（Step 6で実装）

---

*Phase 2 Quality Bar - 「それっぽい」ではなく「測れる」賢さ*
