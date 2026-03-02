---
name: browser-agent
description: "URLから論文メタデータ（タイトル・著者・DOI・アブストラクト）を抽出する軽量ブラウザエージェント。"
triggers:
  - browse
  - fetch
  - url
  - metadata extraction
  - scrape
dependencies: []
---
# Browser Agent

このスキルは、学術論文ページのURLからメタデータを自動抽出します。

## 対応サイト

- PubMed (pubmed.ncbi.nlm.nih.gov): タイトル、著者、DOI、アブストラクト、ジャーナル
- arXiv (arxiv.org): タイトル、著者、DOI、アブストラクト、カテゴリ
- 汎用HTML: OGP / citation_* メタタグからのベストエフォート抽出

## セキュリティ

許可ドメインリスト（allow-list）で制御されます。

## 使用方法

    jarvis browse <URL> [<URL2> ...] [--json] [--output results.json]
