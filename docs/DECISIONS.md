> Authority: ROADMAP (Level 5, Non-binding)

# JARVIS Decision Log

仕様変更・衝突修正・権威順位の変更など、将来「なぜこうなった」を掘り返せるようにする決定記録。

---

## Decision Template

```
## DEC-XXX: [Title]
- **Date**: YYYY-MM-DD
- **Context**: 何が問題だったか
- **Decision**: 何を決めたか
- **Consequences**: 影響
- **Migration Plan**: 既存との差分移行
- **Links**: 関連PR/Issue/Doc
```

---

## Decisions

### DEC-001: Authority Order導入
- **Date**: 2024-12-27
- **Context**: 仕様文書が複数存在し（JARVIS_MASTER.md, MASTER_SPEC.md, MATURITY_*.md等）、矛盾や重複が発生。同じ議論を何度も繰り返す状態。
- **Decision**: 
  - SPEC_AUTHORITY.md を最上位文書として作成
  - 権威順位（Level 0-5）を固定
  - CIで強制語彙の誤用を自動検出
- **Consequences**: 
  - REFERENCE/ROADMAP文書で強制語彙（MUST等）使用不可
  - 既存文書にAuthority Headerを追加
- **Migration Plan**: 
  - 全docs冒頭にAuthority Header追加
  - 強制語彙違反箇所は修正 or 例外登録
- **Links**: Foundation to Scale実装

### DEC-002: CLI単一入口化
- **Date**: 2024-12-27
- **Context**: main.py と jarvis_cli.py の両方が入口として存在し、ユーザー導線が割れていた。
- **Decision**: 
  - jarvis_cli.py を唯一の入口に
  - main.py はデモ専用に格下げ
- **Consequences**: 
  - READMEのQuickstartはCLIのみ
  - main.py はドキュメントから削除
- **Migration Plan**: README更新、main.pyにデモ明記
- **Links**: Step 1-2

### DEC-003: 成果物契約（Bundle規格）
- **Date**: 2024-12-27
- **Context**: run成果物が揺れ、後工程（評価・UI）が安定しない。
- **Decision**: 
  - logs/runs/{run_id}/ に必須8ファイル
  - input.json, papers.jsonl, claims.jsonl, evidence.jsonl, scores.json, report.md, warnings.jsonl, summaries.jsonl
- **Consequences**: 欠けたらrun FAIL
- **Migration Plan**: 既存runは非互換（新規のみ適用）
- **Links**: Step 14-20
