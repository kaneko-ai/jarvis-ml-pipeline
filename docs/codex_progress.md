# Codex Progress（進捗トラッキング）

> Authority: REFERENCE (Level 2, Non-binding)


このファイルは **進捗（状態）だけ** を管理する。  
仕様（Done条件・設計）は正本 `docs/JARVIS_MASTER.md` に集約する。

- 正本：[`docs/JARVIS_MASTER.md`](./JARVIS_MASTER.md)
  - マイルストーン定義：正本「9. マイルストーン（M1–M4）」
  - 直近優先順位：正本「10. 直近の実装優先順位」

---

## 現在のステータス（短く）
- M1: Minimal Core — Status: （未設定）
- M2: Tool統合（文献） — Status: （未設定）
- M3: 自己評価と再試行 — Status: （未設定）
- M4: UI/API接続 — Status: （未設定）

---

## M1: Minimal Core（Done条件は正本に準拠）
- [ ] CLI/APIが必ず Planner→Executor→Router の正規ルートを通る
- [ ] Task→SubTask→AgentResult が一貫I/Oで流れる
- [ ] JSONLログ（run_id/task_id/subtask_id）が残る

## M2: Tool統合（文献）
- [ ] Paper系Agentが paper_pipeline を呼び、索引更新→検索→要約まで一気通貫で通る
- [ ] 成果物（index/chunks/meta/report）が AgentResult の artifacts に載る
- [ ] ローカル索引優先→外部取得（全文）という段階制御ができる

## M3: 自己評価と再試行
- [ ] Judgeが最低2種類（形式＋引用/整合）で動く
- [ ] Judge失敗時に、リトライ方針（何を変えて再試行するか）がログに残る
- [ ] リトライ回数・理由・結果が集計できる

## M4: UI/API接続
- [ ] `/run` と `/status/{run_id}` が存在し、外部UIから進捗参照できる
- [ ] 結果を“最終報告フォーマット”で返す（Summarizer相当の整形）

---

## 次にやること（更新用メモ）
- 進捗更新はこのファイルで良いが、設計変更は必ず `JARVIS_MASTER.md` を更新すること。
