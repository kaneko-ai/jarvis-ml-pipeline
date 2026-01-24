# JARVIS Deployment Guide

> Authority: REFERENCE (Level 2, Non-binding)


## 概要

JARVISを開発環境および本番環境にデプロイするためのガイドです。

---

## 1. 開発環境 (Docker Compose)

### 前提条件

- Docker Desktop インストール
- Docker Compose v2

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-org/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# 環境変数ファイルを作成
cp .env.example .env
# .env を編集して API キーを設定

# コンテナを起動
docker-compose up -d

# 起動確認
docker-compose ps

# ログを確認
docker-compose logs -f jarvis-api
```

### サービス一覧

| サービス | ポート | 説明 |
|----------|--------|------|
| jarvis-api | 8000 | メインAPI |
| jarvis-worker | - | バックグラウンドワーカー |
| redis | 6379 | キャッシュ・キュー |
| postgres | 5432 | メインDB |
| qdrant | 6333 | ベクトルDB |
| prometheus | 9090 | メトリクス収集 |
| grafana | 3000 | ダッシュボード (admin/admin) |

### 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# API テスト
curl http://localhost:8000/api/v1/status

# Grafana
open http://localhost:3000
```

### 停止・クリーンアップ

```bash
# 停止
docker-compose down

# データも含めて削除
docker-compose down -v
```

---

## 2. 本番環境 (Kubernetes + Helm)

### 前提条件

- kubectl 設定済み
- Helm 3.x インストール
- Kubernetes クラスタ (1.25+)

### Helm デプロイ

```bash
# 名前空間を作成
kubectl create namespace jarvis

# 依存関係をインストール
cd helm/jarvis
helm dependency update

# values-production.yaml を作成
cat > values-production.yaml <<EOF
api:
  replicaCount: 3
  image:
    repository: ghcr.io/your-org/jarvis
    tag: "4.4.0"
  
  ingress:
    hosts:
      - host: jarvis.your-domain.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: jarvis-tls
        hosts:
          - jarvis.your-domain.com

secrets:
  JARVIS_WEB_TOKEN: "your-secure-token"
  GOOGLE_API_KEY: "your-api-key"
EOF

# デプロイ
helm install jarvis . \
  --namespace jarvis \
  -f values.yaml \
  -f values-production.yaml

# 確認
helm status jarvis -n jarvis
kubectl get pods -n jarvis
```

### アップグレード

```bash
helm upgrade jarvis . \
  --namespace jarvis \
  -f values.yaml \
  -f values-production.yaml
```

### ロールバック

```bash
# 履歴を確認
helm history jarvis -n jarvis

# ロールバック
helm rollback jarvis 1 -n jarvis
```

---

## 3. GitOps (ArgoCD)

### ArgoCD セットアップ

```bash
# ArgoCD をインストール
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# パスワードを取得
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# UI にアクセス
kubectl port-forward svc/argocd-server -n argocd 8080:443
open https://localhost:8080
```

### JARVIS アプリケーションを登録

```bash
# Application を作成
kubectl apply -f k8s/argocd/application.yaml

# Sync を確認
argocd app get jarvis
argocd app sync jarvis
```

### GitOps ワークフロー

1. コードを main ブランチにプッシュ
2. ArgoCD が変更を検知
3. 自動的に Sync を実行
4. 失敗時は Slack に通知

---

## 4. モニタリング (Grafana)

### ダッシュボードへのアクセス

```bash
# ポートフォワード (K8s)
kubectl port-forward svc/grafana 3000:80 -n monitoring

# または Ingress 経由
open https://grafana.your-domain.com
```

### 初期設定

1. **データソース追加**
   - Configuration → Data Sources → Add data source
   - Prometheus を選択
   - URL: `http://prometheus:9090`

2. **ダッシュボードインポート**
   - Dashboards → Import
   - `infra/grafana/dashboards/jarvis-health.json` をアップロード

### 主要メトリクス

| メトリクス | 説明 | アラート閾値 |
|-----------|------|-------------|
| Request Rate | リクエスト/秒 | - |
| P99 Latency | 99パーセンタイル遅延 | > 2s |
| Error Rate | エラー率 | > 5% |
| Active Pods | 稼働Pod数 | < 2 |

---

## 5. アラート設定

### Slack 連携

```yaml
# alertmanager-config.yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/xxx'

route:
  receiver: 'slack-notifications'
  routes:
    - match:
        severity: critical
      receiver: 'slack-critical'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#jarvis-alerts'
        title: '{{ .CommonLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'slack-critical'
    slack_configs:
      - channel: '#jarvis-critical'
        title: '🚨 {{ .CommonLabels.alertname }}'
```

### PagerDuty 連携

```yaml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - routing_key: 'your-routing-key'
        severity: '{{ .CommonLabels.severity }}'
```

---

## 6. トラブルシューティング

### Pod が起動避ける

```bash
# 詳細を確認
kubectl describe pod <pod-name> -n jarvis
kubectl logs <pod-name> -n jarvis

# イベントを確認
kubectl get events -n jarvis --sort-by='.lastTimestamp'
```

### DB 接続エラー

```bash
# PostgreSQL に直接接続
kubectl exec -it jarvis-postgresql-0 -n jarvis -- psql -U jarvis

# 接続文字列を確認
kubectl get secret jarvis-secrets -n jarvis -o yaml
```

### メトリクスが表示されない

```bash
# ServiceMonitor を確認
kubectl get servicemonitor -n jarvis

# Prometheus targets を確認
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
open http://localhost:9090/targets
```

---

## 7. バックアップ・リストア

### PostgreSQL バックアップ

```bash
# バックアップ
kubectl exec jarvis-postgresql-0 -n jarvis -- \
  pg_dump -U jarvis jarvis > backup.sql

# リストア
kubectl exec -i jarvis-postgresql-0 -n jarvis -- \
  psql -U jarvis jarvis < backup.sql
```

### Qdrant スナップショット

```bash
# スナップショット作成
curl -X POST http://qdrant:6333/collections/jarvis/snapshots

# スナップショット一覧
curl http://qdrant:6333/collections/jarvis/snapshots
```

---

## 8. スケーリング

### 手動スケール

```bash
# API をスケール
kubectl scale deployment jarvis-api --replicas=5 -n jarvis

# Worker をスケール
kubectl scale deployment jarvis-worker --replicas=3 -n jarvis
```

### 自動スケール (HPA)

```bash
# HPA 状態を確認
kubectl get hpa -n jarvis

# メトリクスを確認
kubectl top pods -n jarvis
```

---

## チェックリスト

### デプロイ前

- [ ] `.env` / `secrets` が正しく設定されている
- [ ] Docker イメージがビルドされている
- [ ] DB マイグレーションが完了している
- [ ] テストがパスしている

### デプロイ後

- [ ] `/health` エンドポイントが 200 を返す
- [ ] Grafana でメトリクスが表示される
- [ ] ログが正しく収集されている
- [ ] アラートが正しく送信される
