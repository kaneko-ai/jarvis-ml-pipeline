> Authority: RECORD (Level 4, Binding for change history)
> Canonical: YES
> Purpose: 重要決定の履歴を残し、後から“なぜそうしたか”を再現できるようにする

# DECISIONS（決定記録）

## 書式（必ず守る）
各決定は以下のテンプレで追記する（上書き禁止）。

---
### DEC-YYYYMMDD-XX: タイトル（短く）
- Date: YYYY-MM-DD
- Status: Proposed / Accepted / Rejected / Superseded
- Context（背景）:
- Decision（決定）:
- Rationale（理由）:
- Consequences（影響）:
- Alternatives（代替案）:
- Risks（リスク）:
- Mitigations（対策）:
- References（参照）: （関連SPEC/PR/Issue/Runなど）
---

## 初期エントリ
---
### DEC-20260216-01: Markdown仕様の正本を確立し、リンク切れゼロを必須化
- Date: 2026-02-16
- Status: Accepted
- Context（背景）:
  - docs/DEVELOPMENT_PLAN.md と skills/README.md が、存在しない md を参照していた。
  - これは監査可能性と再現性を目的とするJARVISにとって致命的。
- Decision（決定）:
  - docs/SPEC_AUTHORITY.md, docs/BUNDLE_CONTRACT.md, docs/DoD.md, docs/DECISIONS.md を正本として新規作成し、参照を統一する。
  - docs/tasks/PHASE1_TASKS.md 等を新規作成し、計画書の参照を成立させる。
- Rationale（理由）:
  - “参照先が存在しない”状態は、仕様を無効化し、AI開発の誤解と暴走を誘発するため。
- Consequences（影響）:
  - 既存の計画書やREADMEのリンクが正規化される。
- Alternatives（代替案）:
  - DEVELOPMENT_PLANから参照を削除する案（Rejected：計画書の一次資料が消え、運用が曖昧になる）
- Risks（リスク）:
  - 仕様文書が増え、更新漏れが起きる可能性。
- Mitigations（対策）:
  - SPEC_AUTHORITYに従い、正本を明示し、他文書は参照で済ませる。
- References（参照）:
  - docs/MASTER_SPEC.md
  - policies/API_CONTRACT.md
---
