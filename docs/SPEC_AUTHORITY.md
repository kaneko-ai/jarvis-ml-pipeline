> Authority: SPEC (Level 0, Binding)

# JARVIS Specification Authority

このドキュメントはリポジトリ内のすべての仕様文書の**権威順位（Authority Order）**を定義する。
仕様の衝突・二重管理・蒸し返しを構造的に止めるための最上位文書である。

## Purpose

- 仕様文書の乱立による矛盾を排除し、**唯一の真実源（Single Source of Truth）**を確立する
- 同じ議論を繰り返さない（決定は DECISIONS.md に記録）
- CIで強制語彙の誤用を検出し、自動で止める

---

## Authority Order（権威順位）

| Level | 分類 | 拘束力 | 代表文書 |
|-------|------|--------|---------|
| 0 | AUTHORITY | 最高 | SPEC_AUTHORITY.md |
| 1 | SPEC | Binding | MASTER_SPEC.md |
| 2 | REQUIREMENT | Binding | MATURITY_M*.md, CRITICAL_ENFORCEMENT_LAYER.md |
| 3 | GATE | Binding | DoD.md, QUALITY_BAR.md |
| 4 | REFERENCE | Non-binding | JARVIS_MASTER.md, JARVIS_ARCHITECTURE.md |
| 5 | ROADMAP | Non-binding | *ROADMAP*.md, *STATUS*.md |

---

## 矛盾時の裁定ルール

1. **上位が常に優先**：Level番号が小さいほど権威が高い
2. **下位は修正対象**：矛盾が発見されたら下位文書を修正する
3. **決定は記録必須**：矛盾修正時は DECISIONS.md に記録する

---

## Document Classification（分類定義）

| 分類 | 説明 | 強制語彙 |
|------|------|----------|
| SPEC | 最上位仕様。全実装はこれに従う | ✅ 使用可 |
| REQUIREMENT | 段階要件・成熟度要件 | ✅ 使用可 |
| GATE | 合否判定・品質ゲート | ✅ 使用可 |
| REFERENCE | 設計まとめ・説明 | ❌ 禁止 |
| ROADMAP | 計画・予定 | ❌ 禁止 |

---

## Language Policy（強制語彙の使用規約）

以下の語彙は **SPEC/REQUIREMENT/GATE** レベルでのみ使用可能：

### 英語
- MUST, SHALL, REQUIRED, NEVER, ALWAYS

### 日本語
- 必須, 厳守, 〜しなければならない, 〜してはいけない, 禁止, 常に, 絶対に

**REFERENCE/ROADMAP** でこれらが出現した場合、CIで自動的にfailする。

---

## Change Policy（変更手順）

1. 仕様を変更する場合、対象文書のLevelを確認
2. 上位文書との整合性を確認
3. 変更後、DECISIONS.md に以下を記録：
   - Context（何が問題だったか）
   - Decision（何を決めたか）
   - Consequences（影響）
   - Migration Plan（移行方針）

---

## CI Enforcement

```bash
python tools/spec_lint.py
```

- REFERENCE/ROADMAP文書で強制語彙を検出したらfail
- 違反箇所（ファイル、行番号、語彙）を出力

---

## 文書一覧と割り当て

| 文書 | Level | 分類 |
|------|-------|------|
| SPEC_AUTHORITY.md | 0 | AUTHORITY |
| MASTER_SPEC.md | 1 | SPEC |
| MATURITY_M1.md〜M7.md | 2 | REQUIREMENT |
| CRITICAL_ENFORCEMENT_LAYER.md | 2 | REQUIREMENT |
| DoD.md | 3 | GATE |
| QUALITY_BAR.md | 3 | GATE |
| RepairPolicy.md | 3 | GATE |
| JARVIS_MASTER.md | 4 | REFERENCE |
| JARVIS_ARCHITECTURE.md | 4 | REFERENCE |
| JARVIS_GUIDE_SIMPLE.md | 4 | REFERENCE |
| JARVIS_V44_ROADMAP.md | 5 | ROADMAP |
| codex_progress.md | 5 | ROADMAP |
| DecisionLog.md | 5 | ROADMAP |
