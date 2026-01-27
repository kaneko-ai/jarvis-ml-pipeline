# Browser Agent Guide

## 概要とセキュリティモデル

Browser Subagent は Playwright を用いてブラウザ操作を行い、ページナビゲーション・スクリーンショット・テキスト抽出などを実行します。
セキュリティモデルは `SecurityPolicy` で管理され、許可 URL リストや JavaScript 実行可否を制御できます。

## セットアップ（Playwright インストール）

```bash
uv pip install "jarvis-research-os[browser]"
python -m playwright install chromium
```

## SecurityPolicy の設定

`configs/browser_security.yaml` で制御します。

```yaml
js_execution: false
url_allow_list:
  - "pubmed.ncbi.nlm.nih.gov"
  - "arxiv.org"
url_deny_list:
  - "example.com"
```

## 組み込みエージェントの使用方法

### PubMed

```python
from jarvis_core.browser.subagent import BrowserSubagent
from jarvis_core.browser.schema import SecurityPolicy

policy = SecurityPolicy(url_allow_list=["pubmed.ncbi.nlm.nih.gov"])
agent = BrowserSubagent(security_policy=policy, headless=True)
```

### arXiv

```python
policy = SecurityPolicy(url_allow_list=["arxiv.org"])
```

### PDF Download

```python
policy = SecurityPolicy(url_allow_list=["doi.org", "publisher.example"])
```

## 録画機能の使用方法

```python
agent.start_recording()
await agent.navigate("https://pubmed.ncbi.nlm.nih.gov")
recording_path = agent.stop_recording()
print(recording_path)
```

録画は `jarvis_core/browser/recording.py` の `BrowserRecorder` に保存されます。
