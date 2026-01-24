# JARVIS Runbook

> Authority: REFERENCE (Level 2, Non-binding)


運用手順書 - 失敗パターン別対処とメンテナンス

---

## 1. 失敗パターン別対処

### 1.1 PubMed API エラー

**症状**: `HTTPError 429 Too Many Requests` または `503 Service Unavailable`

**原因**: レート制限超過またはNCBIサーバー過負荷

**対処**:
1. `NCBI_API_KEY` が設定されているか確認
2. 設定されていない場合は取得して環境変数に設定
3. それでも発生する場合は 10分待機して再実行
4. 継続する場合はNCBIのステータスページを確認

```bash
# API keyの確認
echo $NCBI_API_KEY

# 再実行（チェックポイントから再開）
python -m jarvis_core.cli run --resume --run-id <run_id>
```

### 1.2 PMC フルテキスト取得失敗

**症状**: `No fulltext available` または `PMCID not found`

**原因**: OAでない論文、PMCに収録されていない

**対処**:
1. 論文がOAかどうか確認
2. OAでない場合は `degraded` モードで継続（abstractのみ）
3. Fail-Closed設定の場合はスキップして次の論文へ

```yaml
# degradedモード許可
fail_policy:
  default: "open"
```

### 1.3 パイプライン途中失敗

**症状**: ステージ途中でエラー終了

**対処**:
1. チェックポイントを確認
2. 再開コマンドを実行

```bash
# チェックポイント確認
cat artifacts/<run_id>/checkpoint.json

# 再開
python -m jarvis_core.cli run --resume --run-id <run_id>
```

### 1.4 品質ゲート不通過

**症状**: `QualityGateError: provenance_rate below threshold`

**原因**: 根拠なしfactが多い、抽出品質が低い

**対処**:
1. 監査ログで問題のClaimを特定
2. 元論文を確認して根拠を再抽出
3. 閾値を一時的に下げて実行（監査には記録）

```python
# 閾値を下げて実行（推奨避ける）
quality_gates:
  provenance_rate: 0.90  # 95% → 90%
```

---

## 2. 定期メンテナンス

### 2.1 アーティファクトクリーンアップ

古いアーティファクトを削除:

```bash
# 30日以上前のアーティファクトを削除
find artifacts/ -type d -mtime +30 -exec rm -rf {} +
```

### 2.2 メトリクス集計

週次でメトリクスを集計:

```bash
python scripts/aggregate_metrics.py --period weekly
```

### 2.3 キャッシュ無効化

モデル更新時:

```bash
# キャッシュクリア
rm -rf .cache/llm/*

# スナップショットのmodel_ioを無効化
python scripts/invalidate_model_cache.py --model-version old_version
```

---

## 3. モデル更新手順

### 3.1 事前準備

1. 現在のベンチマーク結果を保存
2. テストデータセット（Golden 10）を準備

### 3.2 更新実行

```bash
# 1. 新モデルでGolden testを実行
python -m jarvis_core.cli run --pipeline golden_test --model new_model

# 2. 結果を比較
python scripts/compare_golden.py --old old_results.json --new new_results.json

# 3. 差異が許容範囲なら本番適用
# configs/policies/reproducibility.yml を更新
```

### 3.3 ロールバック

問題が発生した場合:

```bash
# 前バージョンに戻す
git checkout HEAD~1 -- configs/policies/reproducibility.yml
```

---

## 4. スナップショット破損時の復旧

### 4.1 症状

- `JSONDecodeError` または `gzip.BadGzipFile`
- 再実行時に不整合

### 4.2 対処

```bash
# 1. 破損ファイルを特定
python scripts/verify_snapshots.py --run-id <run_id>

# 2. 破損ファイルを削除
rm artifacts/<run_id>/snapshot/snapshot.json.gz

# 3. 再実行（ライブ取得）
python -m jarvis_core.cli run --no-snapshot --run-id <run_id>
```

---

## 5. 緊急時連絡先

| 状況 | 対処 |
|-----|------|
| NCBI API全面停止 | NCBIステータスページ確認、待機 |
| CI全面失敗 | GitHub Actionsステータス確認 |
| データ不整合 | 監査ログから原因特定 |

---

## 6. 監査ログの確認方法

```bash
# 最新ランの監査ログ
cat artifacts/<run_id>/audit.json | jq .

# 失敗したステージを抽出
cat artifacts/<run_id>/audit.json | jq '.entries[] | select(.event == "failed")'

# provenance統計
cat artifacts/<run_id>/audit.json | jq '.summary'
```
