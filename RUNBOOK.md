# JARVIS運用Runbook

Target release: `v1.0.0`

JARVIS Research OS (Phase 2-ΩΩ) の運用手順・障害対応ガイド

---

## 典型的な失敗パターン

### 1. UNSUPPORTED_CLAIM（根拠不足）

**原因**: Evidence不足またはEvidence強度が低い  
**確認ファイル**: `warnings.jsonl`  
**対処**:
1. `evidence.jsonl`でevidence_strengthを確認
2. Strong/Medium evidenceが不足している場合:
   - クエリを緩和して再検索
   - または結論を推測扱いに降格

```bash
# 警告確認
uv run python -c "import json; print([w for w in map(json.loads, open('logs/runs/XXX/warnings.jsonl')) if w['code']=='UNSUPPORTED_CLAIM'])"
```

---

### 2. BUDGET_EXCEEDED（予算超過）

**原因**: トークン使用量が閾値を超過  
**確認ファイル**: `cost_report.json`  
**対処**:
1. `cost_report.json`でトークン内訳を確認
2. fast profileで再実行

```bash
# コスト確認
cat logs/runs/XXX/cost_report.json | jq '.totals'

# fast profileで再実行
uv run python jarvis_cli.py run --goal "query" --profile fast
```

---

### 3. LANGUAGE_VIOLATION（言語違反）

**原因**: 禁止された因果表現（"causes", "proves"等）  
**確認**: report.mdの内容  
**対処**:
1. `docs/LANGUAGE_RULES.yaml`の禁止用語を確認
2. Report生成ロジック（`generate_report.py`）を修正
3. 再実行

---

### 4. INVALID_EVIDENCE_LOCATOR（根拠位置不正）

**原因**: Evidence locatorがPDF本文と不一致  
**確認**: locator verification結果  
**対処**:
1. PDF抽出設定（`pdf_extract_config.yaml`）を確認
2. 一致率< 0.8の場合は該当evidenceを無効化

---

## ログ確認順序

トラブル時は以下の順で確認：

1. **eval_summary.json** - gate_passed, 全体結果
2. **warnings.jsonl** - 警告一覧（1行1JSON）
3. **cost_report.json** - トークン/時間/API呼び出し
4. **evidence.jsonl** - 根拠の強度・ID
5. **report.md** - 最終出力

---

## 再実行手順

### 通常再実行

```bash
uv run python jarvis_cli.py run --goal "your query"
```

### Snapshot再実行（再現性確保）

```bash
uv run python jarvis_cli.py rerun --snapshot logs/runs/{run_id}/retrieval_snapshot.json
```

### Profile切り替え

```bash
# Strictモード（高品質・低速）
uv run python jarvis_cli.py run --goal "query" --profile strict

# Balancedモード（標準）
uv run python jarvis_cli.py run --goal "query" --profile balanced

# Fastモード（予算節約）
uv run python jarvis_cli.py run --goal "query" --profile fast
```

---

## Quality Gate失敗時の対応

### Provenance Rate < 0.90

**意味**: 根拠追跡率が低い  
**対処**: ステージ実装を確認し、provenance.add()呼び出しを追加

### Support Rate < 0.90

**意味**: 結論の支持率が低い  
**対処**:
- より強いevidenceを収集
- または推測扱いに降格

### Trick Setでの予期しない合格

**意味**: 落ちるべきケースで落ちていない（過剰一般化）  
**対処**: Language lintルールを強化、またはevidence判定を厳格化

---

## CI失敗時の対処

### uv.lock未更新

```bash
uv lock
git add uv.lock
git commit -m "build: Update lock"
```

### Testフ
ィルーチャ

```bash
# ローカルで再現
uv run pytest tests/test_xxx.py -v

# 詳細ログ
uv run pytest tests/ -vv --tb=short
```

---

## 承認フロー（Human-in-the-loop）

成果物を外部共有・論文化する前に必ず承認：

```bash
# 承認
uv run python jarvis_cli.py approve --run_id {run_id} --approver "name" --scope "publication"

# 取り消し
uv run python jarvis_cli.py revoke --run_id {run_id}
```

**未承認の成果物は外部共有禁止**

---

## 定期メンテナンス

### 月次ベンチマーク

```bash
# realistic_mixで回帰監視
uv run python jarvis_cli.py benchmark --dataset evals/benchmarks/realistic_mix_v1.jsonl
```

### Golden Set拡張

現在7論文 → 目標100論文/ドメイン

---

## 緊急連絡

システム障害・データ漏洩の疑いがある場合:
1. 実行停止
2. ログ保全（logs/runs/以下をバックアップ）
3. 管理者に報告
