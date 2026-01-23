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

### DEC-004: 成果物契約（4ファイル必須）
- **Date**: 2024-12-27
- **Context**: Phase Loop 1実装において、成果物契約を簡素化・明確化する必要があった。
- **Decision**: 
  - 必須成果物を4ファイルに統一
  - run_config.json, result.json, eval_summary.json, events.jsonl
  - 成功/失敗に関わらず必ず生成
- **Consequences**: 
  - RunStoreが唯一のパス決定責務を持つ
  - 欠損があればContractViolationError
- **Migration Plan**: 既存の8ファイル契約と並行運用、段階的に統合
- **Links**: MASTER_SPEC v1.1, Phase Loop 1

### DEC-005: success条件（gate_passed必須）
- **Date**: 2024-12-27
- **Context**: 品質ゲートを通過せずにsuccessになるケースがあり、信頼性が損なわれていた。
- **Decision**: 
  - status == "success" ⇔ gate_passed == true
  - Verify未実行のrunはsuccessにならない
  - gate_passed == false → status は "failed" または "needs_retry"
- **Consequences**: 
  - citation無しでsuccessが構造的に不可能
  - QualityGateVerifierが必ず実行される
- **Migration Plan**: 新規runのみ適用
- **Links**: MASTER_SPEC v1.1, Phase Loop 1

### DEC-006: 成果物契約の統一（10ファイル）
- **Date**: 2024-12-27
- **Context**: 
  - MASTER_SPEC v1.1 では4ファイル必須（run_config.json, result.json, eval_summary.json, events.jsonl）
  - BUNDLE_CONTRACT.md では10ファイル必須（上記4つ + input.json, papers.jsonl, claims.jsonl, evidence.jsonl, scores.json, warnings.jsonl, report.md）
  - DEC-003では8ファイル、DEC-004では4ファイルと複数の契約が並存
  - この矛盾がプロジェクト進捗を65%で停滞させている根本原因
- **Decision**: 
  - **BUNDLE_CONTRACT.md の10ファイル契約を唯一の成果物契約とする**
  - 4ファイル契約（DEC-004）は廃止
  - 8ファイル契約（DEC-003）は10ファイルに統合
  - MASTER_SPEC.md を v1.2 に更新し、10ファイル契約を記載
- **Consequences**: 
  - run完了時に10ファイルが揃わなければFAIL
  - 失敗時でも result.json, eval_summary.json, warnings.jsonl, report.md は必ず生成
  - show-run がfail理由と欠損ファイルを表示
- **Migration Plan**: 
  - 即時適用（後方互換は維持しない）
  - 既存runは非互換として扱う
- **Links**: BUNDLE_CONTRACT.md, MASTER_SPEC v1.2

### DEC-007: 2段階カバレッジゲート
- **Date**: 2026-01-23
- **Context**: 
  - CIが `--cov-fail-under=95` を要求しているが、総合カバレッジは約65%
  - `tests/fixtures/sample.pdf` がGit LFSポインタで、PDF系テストが不安定
  - カバレッジ目標が現実と乖離しており、CIが常に失敗する状態
- **Decision**: 
  - **Phase 1（当面のブロッキング）**: カバレッジ85%、branch評価無効
  - **Phase 2（最終ゲート）**: カバレッジ95%、branch評価有効
  - CIのカバレッジ設定は `scripts/ci_coverage.sh` で一元管理
  - `.coveragerc.phase1` と `.coveragerc.phase2` で設定を分離
- **Consequences**: 
  - ci.yml から `--cov-fail-under` を削除
  - カバレッジ条件変更は `scripts/ci_coverage.sh` のみで行う
  - Phase2切替は専用PRで行い、カバレッジ改善変更と混在禁止
- **Migration Plan**: 
  - 即時適用
  - Phase1達成後、mainで連続10回CI成功でPhase2に移行
- **Links**: docs/COVERAGE_POLICY.md

