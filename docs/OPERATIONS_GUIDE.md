# JARVIS 運用ワークフロー

> Authority: REFERENCE (Level 2, Non-binding)


本ドキュメントでは日常運用タスクを説明します。

---

## 日次タスク

### 1. ヘルスチェック確認

```bash
# 全サービスの状態
kubectl get pods -n jarvis

# ヘルスエンドポイント
curl https://jarvis.example.com/health
curl https://jarvis.example.com/ready
```

### 2. メトリクス確認

- Grafana で JARVIS System Health ダッシュボードを確認
- エラー率が 1% 以下であることを確認
- P99 レイテンシが 2 秒以下であることを確認

### 3. アラート確認

- Slack `#jarvis-alerts` チャンネルを確認
- 未解決のアラートがないことを確認

---

## 週次タスク

### 1. リソース使用量レビュー

```bash
# CPU/メモリ使用量
kubectl top pods -n jarvis

# ストレージ使用量
kubectl exec jarvis-postgresql-0 -n jarvis -- df -h
```

### 2. ログレビュー

```bash
# エラーログの確認
kubectl logs -l app=jarvis-api -n jarvis | grep -i error

# 遅いクエリの確認
kubectl logs jarvis-postgresql-0 -n jarvis | grep "duration:"
```

### 3. 依存関係更新

```bash
# セキュリティアップデートを確認
dependabot alerts を確認

# 更新を適用
pip install --upgrade -r requirements.lock
```

---

## リリースプロセス

### 1. リリース準備

```bash
# テストを実行
pytest -m core

# バージョンを更新
# pyproject.toml のバージョンを更新

# タグを作成
git tag v4.4.1
git push origin v4.4.1
```

### 2. 自動リリース

GitHub Actions が自動的に:
1. テストを実行
2. Docker イメージをビルド
3. GHCR にプッシュ
4. GitHub Release を作成

### 3. デプロイ

ArgoCD が自動的にデプロイ、または手動で:

```bash
# Helm でアップグレード
helm upgrade jarvis helm/jarvis \
  --namespace jarvis \
  --set api.image.tag=v4.4.1
```

---

## インシデント対応

### Severity 1 (Critical)

**症状**: サービス完全停止

**対応**:
1. `#jarvis-critical` でインシデント宣言
2. 直近のデプロイをロールバック
   ```bash
   helm rollback jarvis -n jarvis
   ```
3. ログを収集
4. ポストモーテム実施

### Severity 2 (High)

**症状**: エラー率 > 5%、レイテンシ > 5s

**対応**:
1. Pod をリスタート
   ```bash
   kubectl rollout restart deployment jarvis-api -n jarvis
   ```
2. スケールアップ
   ```bash
   kubectl scale deployment jarvis-api --replicas=10 -n jarvis
   ```
3. 原因調査

### Severity 3 (Medium)

**症状**: 部分的な機能低下

**対応**:
1. ログを確認
2. 次のリリースで修正

---

## バックアップ

### 自動バックアップ (CronJob)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: jarvis-backup
spec:
  schedule: "0 2 * * *"  # 毎日 2:00
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - pg_dump
            - -h
            - jarvis-postgresql
            - -U
            - jarvis
            - -d
            - jarvis
            - -f
            - /backup/jarvis-$(date +%Y%m%d).sql
```

### 手動バックアップ

```bash
# PostgreSQL
kubectl exec jarvis-postgresql-0 -n jarvis -- \
  pg_dump -U jarvis jarvis | gzip > backup-$(date +%Y%m%d).sql.gz

# Qdrant
curl -X POST http://qdrant:6333/collections/jarvis/snapshots
```

---

## スケーリングガイドライン

| 負荷レベル | API Pods | Worker Pods | Redis Memory |
|-----------|----------|-------------|--------------|
| Low (< 10 rps) | 2 | 1 | 256Mi |
| Medium (10-50 rps) | 3-5 | 2-3 | 512Mi |
| High (50-200 rps) | 5-10 | 3-5 | 1Gi |
| Peak (> 200 rps) | 10-20 | 5-10 | 2Gi |

---

## コンタクト

- **オンコール**: PagerDuty jarvis-oncall
- **Slack**: `#jarvis-support`
- **Wiki**: https://wiki.example.com/jarvis
