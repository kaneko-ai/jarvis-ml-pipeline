# JARVIS Definition of Done (DoD)

## Phase 1: Foundation
- [ ] CIがinstall前提（pip install -e .）
- [ ] legacy握りつぶし撤廃（LEGACY_MUST_PASS）
- [ ] coreが落ちたらCIが落ちる

## Phase 2: MVP E2E
- [ ] e2e_oa10で必須8ファイル生成
- [ ] 根拠なし断言がwarningsへ

## Phase 3: Evaluation
- [ ] goldset 3ケースでPR回帰検知
- [ ] evidence_coverage_rate >= 0.8

## Phase 4: Ranking
- [ ] scores.jsonにfeatures
- [ ] report.mdに順位理由

## Phase 5: Cost Control
- [ ] budget制御がbundleに記録

## Phase 6: Ops
- [ ] DoD/Runbook/RepairPolicy整備

## Phase 7: Dashboard
- [ ] read-only runs閲覧UI

## Phase 8: Knowledge
- [ ] claim/evidence蓄積検索

## Phase 9: Scale
- [ ] 監査ログ付きzotero/screenpipe統合
