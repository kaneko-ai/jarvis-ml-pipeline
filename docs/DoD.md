> Authority: SPEC (Level 2, Binding)
> Canonical: YES
> Purpose: 「完了」を恣意的に宣言できないように、機械的に判定できる条件を固定する

# DoD（Definition of Done）

## 1. ドキュメントDoD（Markdown）
- 内部リンク切れが 0
- 参照先ファイルがすべて存在する
- “正本（canonical）” が明示され、重複仕様がある場合は片方に統合されている
- 仕様の衝突解決（SPEC_AUTHORITY）が存在し、参照されている

## 2. 機能DoD（Feature）
- 入力／出力／失敗時挙動／ログがSPECに明記
- 失敗時でも監査可能（最低限：run.json + audit.json が意味を持つ）
- 主要パラメータが固定（seed、モデル名、version 等）
- 再実行で同等の結果が得られる（許容範囲をSPECで定義）

## 3. 契約DoD（Contract）
- BUNDLE_CONTRACT の必須10ファイルが常に生成される
- 欠損はテストで検出される（例：e2e contract test）

## 4. 記録DoD（Decisions）
- 重大決定は docs/DECISIONS.md に記録
- “なぜ／何が変わる／影響範囲／後方互換／リスク” が書かれている

## 5. 禁止（DoD未満の完了宣言）
- 「動いたからOK」
- 「CIが通ったからOK」
- 「見た目ができたからOK」
（JARVISの目的は再現性・監査可能性。ここを外すなら別プロジェクトになる）
