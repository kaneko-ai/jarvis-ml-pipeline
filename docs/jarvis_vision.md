# docs/jarvis_vision.md
Last Updated: 2025-12-20

## 0. この文書の役割（概要のみ）
このファイルは Jarvis（javis）の **全体像を短く把握するための概要**である。  
仕様・設計判断・ロードマップ・I/O契約の正本は `docs/JARVIS_MASTER.md` に一本化する。

- 正本：`docs/JARVIS_MASTER.md`

---

## 1. Jarvisとは何か（1文）
Jarvisは、研究・執筆・就活のタスクを「計画→実行→検証→記録」の手順に落とし、再現可能に回す **個人向けオーケストレーター**である。

---

## 2. 何を最優先にするか（運用が壊れないための原則）
- 実行経路（Plan→Act→Verify→Store）を強制する
- 根拠が不足する出力は言い切らない（根拠不足・不明を明示）
- 出力形式を固定し、後から検証できる形にする
- ログ（JSONL）を必須にして観測可能にする
- 内部思考（thought）を保存しない（運用上の害が大きい）

---

## 3. 今回「作らない」もの（明示的に凍結）
- Web UI（`/run` と `/status`）
- PDF→スライド自動生成、Podcast生成、PDF→動画
- GitHub Actions強化（通知/差分要約/Slack等）
- LoRAでの専用モデル化
- セキュリティ自動監査（BugTrace系）

理由：中核の配線と品質ゲートが未固定な段階で拡張すると、全機能が負債化するため。

---

## 4. 最小アーキテクチャ（概念図）
```text
[CLI/呼び出し口]
      |
      v
[Jarvis Core]
  Plan -> Act -> Verify -> Store
      |
      v
[Tools]
  - 文献索引検索（ローカル）
  - 文献取得/チャンク化（必要時）
      |
      v
[Data/Artifacts]
  - chunks / index / reports / logs
5. 次に見るべき文書
仕様・ロードマップ：docs/JARVIS_MASTER.md

進捗管理：docs/codex_progress.md

設定運用（agents.yaml）：docs/agent_registry.md

yaml
コードをコピーする

```markdown
# docs/codex_progress.md
Last Updated: 2025-12-20

## 0. このファイルの目的（進捗だけ）
このファイルは **進捗（状態）だけ** を管理する。  
仕様（Done条件・設計・改修順序）は正本 `docs/JARVIS_MASTER.md` に集約する。

- 正本：`docs/JARVIS_MASTER.md`

---

## 1. 現在のステータス（短く）
- M1：実行経路の統一（Plan→Act→Verify→Store の強制） — Status: Planned
- M2：文献パイプラインのツール化（paper_survey E2E） — Status: Planned
- M3：品質ゲート（根拠不足の言い切り禁止） — Status: Planned
- M4：拡張可能な構造へ整形（docs一本化＋tools中心） — Status: Planned

---

## 2. M1（DoDは正本に準拠）
- [ ] CLI / `run_jarvis()` が必ず ExecutionEngine を通る
- [ ] JSONLログ（run_id/task_id/subtask_id）が残る
- [ ] 出力が `answer/citations/meta` に固定される（thought保存なし）

## 3. M2
- [ ] `paper_survey` が「索引検索→根拠→要約」で一気通貫
- [ ] PaperFetcherAgent がスタブを脱し、citations を必ず返す
- [ ] 検索結果が `chunk_id/source/locator/text` で取り回せる

## 4. M3
- [ ] `paper_survey` と `thesis` で citations が無ければ fail/partial を返す
- [ ] 失敗理由（missing_citations 等）がログに残る
- [ ] validator関連のテストが追加される

## 5. M4
- [ ] `jarvis_core/tools/` が拡張点として固定される
- [ ] docsが一本化され、重複・破損が解消される
- [ ] 最短導線の examples が存在する（任意）

---

## 6. 次の更新ルール
- 設計を変えたら、まず `docs/JARVIS_MASTER.md` を更新する
- ここはチェックボックスとStatusだけを更新する
