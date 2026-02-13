# JARVIS Research OS クイックスタートガイド

> Authority: REFERENCE (Level 2, Non-binding)


## はじめに

JARVIS Research OSは、学術研究のためのローカルファースト研究支援システムです。
このガイドでは、基本的な使い方を説明します。

## インストール

### 1. 環境準備

```bash
# リポジトリをクローン
git clone https://github.com/your-org/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# 仮想環境作成
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 依存関係インストール
pip install -e .
```

> より高速なセットアップを行う場合は `uv sync` を利用できます。

### 2. オプション: ローカルLLM（Ollama）

```bash
# Ollamaインストール（https://ollama.ai）
# モデルをダウンロード
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

## 基本的な使い方

### 文献検索

```python
from jarvis_core.sources import UnifiedSourceClient

# クライアント作成（メールアドレスでレート制限緩和）
client = UnifiedSourceClient(email="your@email.com")

# 検索実行
papers = client.search(
    "machine learning radiology diagnosis",
    max_results=20
)

# 結果表示
for paper in papers[:5]:
    print(f"📄 {paper.title}")
    print(f"   著者: {', '.join(paper.authors[:3])}")
    print(f"   年: {paper.year}")
    print(f"   DOI: {paper.doi}")
    print()
```

### 証拠グレーディング

```python
from jarvis_core.analysis.grade_system import EnsembleGrader

grader = EnsembleGrader(use_llm=False)  # ルールベースのみ

assessment = grader.grade(
    evidence_id="ev1",
    claim_id="claim1",
    claim_text="AI診断は放射線科医より正確である",
    evidence_text="このランダム化比較試験では、500名の患者を対象に...",
)

print(f"研究デザイン: {assessment.study_design.value}")
print(f"最終レベル: {assessment.final_level.value}")
print(f"信頼度: {assessment.confidence_score:.2f}")
```

### PRISMA図生成

```python
from jarvis_core.reporting.prisma_generator import generate_prisma

markdown = generate_prisma(
    search_results=all_papers,
    screened_results=screened,
    included_results=included,
    title="システマティックレビュー"
)
```

## 新機能 (Phase 12)

### PDF フルテキスト解析

```python
from jarvis_core.ingestion.pdf_parser import parse_pdf
from pathlib import Path

# PDF を解析
paper = parse_pdf(Path("path/to/paper.pdf"))

print(f"タイトル: {paper.title}")
print(f"抄録: {paper.abstract[:200]}...")
print(f"抽出されたセクション数: {len(paper.sections)}")
print(f"抽出された表の数: {len(paper.tables)}")
print(f"抽出された図の数: {len(paper.figures)}")
```

### 統計的主張検証

```python
from jarvis_core.verification.stat_verifier import verify_statistical_claim

result = verify_statistical_claim(
    claim="The treatment showed significant improvement (p < 0.05)",
    data={
        "p_value": 0.03,
        "sample_size": 120,
        "effect_size": 0.45,
        "ci_low": 0.2,
        "ci_high": 0.7
    }
)

print(f"検証結果: {'有効' if result.is_valid else '問題あり'}")
print(f"検出された問題: {result.issues}")
```

### エビデンス統合

```python
from jarvis_core.orchestrator.agents.synthesis import EvidenceSynthesisAgent, Paper
import asyncio

agent = EvidenceSynthesisAgent()

papers = [
    Paper(title="Study A", abstract="RCT showing positive results..."),
    Paper(title="Study B", abstract="Meta-analysis confirming..."),
]

report = asyncio.run(agent.synthesize(papers, "Treatment efficacy"))

print(f"要約: {report.summary}")
print(f"証拠の強さ: {report.strength_of_evidence}")
print(f"ギャップ: {report.gaps}")
```


## 新しいCLIコマンド

```bash
# MCP Hub
jarvis mcp list --config configs/mcp_config.json

# Skills
jarvis skills list

# Rules
jarvis rules list

# Workflows
jarvis workflows list
```

## 次のステップ

- [API リファレンス](API_REFERENCE.md) - 詳細なAPI仕様
- [ドキュメントハブ](README.md) - 運用方針と最新の実装ノート
