> Authority: ROADMAP (Level 5, Non-binding)

# Phase 2: 差別化機能 タスク詳細

**期間**: Week 9-16  
**目標スコア**: 88 → 103/100

---

## Sprint 9-10: Evidence評価システム (Week 17-20)

### Task 2.1: Evidence強度スコアリング

**目標**: 根拠の信頼性を定量評価（scite相当）

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 2.1.1 | EvidenceUnitスキーマ | `jarvis_core/evidence/schema.py` | Pydanticモデル、強度フィールド | 4h | [ ] |
| 2.1.2 | 強度分類定義 | `jarvis_core/evidence/grades.py` | Strong/Moderate/Weak/Insufficient | 2h | [ ] |
| 2.1.3 | ルールベーススコアラー | `jarvis_core/evidence/rule_scorer.py` | キーワード/パターン検出 | 6h | [ ] |
| 2.1.4 | LLMベーススコアラー | `jarvis_core/evidence/llm_scorer.py` | GPT-4による評価 | 6h | [ ] |
| 2.1.5 | アンサンブルスコアラー | `jarvis_core/evidence/ensemble.py` | ルール+LLM統合 | 4h | [ ] |
| 2.1.6 | 研究デザイン検出 | `jarvis_core/evidence/study_design.py` | RCT/コホート/症例報告分類 | 6h | [ ] |
| 2.1.7 | サンプルサイズ抽出 | `jarvis_core/evidence/extractors.py` | N数、検出力 | 4h | [ ] |
| 2.1.8 | 統計的有意性抽出 | `jarvis_core/evidence/extractors.py` | p値、CI抽出 | 4h | [ ] |
| 2.1.9 | バイアスリスク評価 | `jarvis_core/evidence/bias_risk.py` | ROB2準拠 | 6h | [ ] |
| 2.1.10 | パイプライン統合 | `configs/pipelines/e2e_oa10.yml` | evidence_gradingステージ追加 | 2h | [ ] |

**成果物例**:
```python
# jarvis_core/evidence/schema.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class EvidenceGrade(str, Enum):
    """根拠の強度グレード"""
    STRONG = "strong"           # メタ分析、大規模RCT
    MODERATE = "moderate"       # 小規模RCT、質の高い観察研究
    WEAK = "weak"              # 症例対照研究、症例シリーズ
    INSUFFICIENT = "insufficient"  # 専門家意見、症例報告
    UNKNOWN = "unknown"         # 評価不能

class StudyDesign(str, Enum):
    """研究デザイン分類"""
    META_ANALYSIS = "meta_analysis"
    SYSTEMATIC_REVIEW = "systematic_review"
    RCT = "randomized_controlled_trial"
    COHORT = "cohort_study"
    CASE_CONTROL = "case_control_study"
    CROSS_SECTIONAL = "cross_sectional_study"
    CASE_SERIES = "case_series"
    CASE_REPORT = "case_report"
    EXPERT_OPINION = "expert_opinion"
    IN_VITRO = "in_vitro_study"
    ANIMAL_STUDY = "animal_study"
    UNKNOWN = "unknown"

class BiasRisk(str, Enum):
    """バイアスリスク（ROB2準拠）"""
    LOW = "low"
    SOME_CONCERNS = "some_concerns"
    HIGH = "high"
    UNCLEAR = "unclear"

class EvidenceUnit(BaseModel):
    """根拠の最小単位"""
    evidence_id: str
    claim_id: str
    paper_id: str
    
    # テキスト情報
    text: str
    locator: dict = Field(description="section, paragraph, page")
    
    # 強度評価
    grade: EvidenceGrade = EvidenceGrade.UNKNOWN
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # 研究特性
    study_design: StudyDesign = StudyDesign.UNKNOWN
    sample_size: Optional[int] = None
    
    # 統計情報
    p_value: Optional[float] = None
    confidence_interval: Optional[tuple[float, float]] = None
    effect_size: Optional[float] = None
    
    # バイアス評価
    bias_risk: BiasRisk = BiasRisk.UNCLEAR
    bias_domains: dict = Field(default_factory=dict)
    
    # スコアリング詳細
    scoring_details: dict = Field(default_factory=dict)
```

```python
# jarvis_core/evidence/llm_scorer.py
from .schema import EvidenceUnit, EvidenceGrade
from ..llm import LLMProvider

GRADING_PROMPT = """
以下の根拠テキストを評価してください。

## 根拠テキスト
{evidence_text}

## 論文情報
- タイトル: {paper_title}
- 年: {paper_year}

## 評価基準
1. 研究デザイン（メタ分析 > RCT > コホート > 症例報告）
2. サンプルサイズ
3. 統計的有意性
4. バイアスリスク

## 出力形式（JSON）
{{
    "grade": "strong|moderate|weak|insufficient",
    "confidence": 0.0-1.0,
    "study_design": "研究デザイン",
    "reasoning": "評価理由"
}}
"""

class LLMEvidenceScorer:
    """LLMベースの根拠強度スコアラー"""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm
    
    async def score(
        self,
        evidence: EvidenceUnit,
        paper_context: dict
    ) -> EvidenceUnit:
        """根拠の強度をスコアリング"""
        prompt = GRADING_PROMPT.format(
            evidence_text=evidence.text,
            paper_title=paper_context.get("title", "Unknown"),
            paper_year=paper_context.get("year", "Unknown"),
        )
        
        response = await self.llm.complete(prompt, temperature=0.1)
        result = self._parse_response(response)
        
        evidence.grade = EvidenceGrade(result["grade"])
        evidence.confidence = result["confidence"]
        evidence.study_design = StudyDesign(result.get("study_design", "unknown"))
        evidence.scoring_details["llm_reasoning"] = result.get("reasoning", "")
        
        return evidence
```

---

### Task 2.2: Support/Contrast分類

**目標**: 引用が支持か反論かを判定（scite相当）

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 2.2.1 | CitationContextスキーマ | `jarvis_core/citation/schema.py` | 引用文脈モデル | 3h | [ ] |
| 2.2.2 | 引用文脈抽出 | `jarvis_core/citation/extractor.py` | 引用周辺テキスト抽出 | 4h | [ ] |
| 2.2.3 | 分類ラベル定義 | `jarvis_core/citation/labels.py` | Supporting/Contrasting/Mentioning | 1h | [ ] |
| 2.2.4 | ルールベース分類器 | `jarvis_core/citation/rule_classifier.py` | 否定語/肯定語パターン | 4h | [ ] |
| 2.2.5 | LLM分類器 | `jarvis_core/citation/llm_classifier.py` | Few-shot分類 | 4h | [ ] |
| 2.2.6 | 分類結果集計 | `jarvis_core/citation/aggregator.py` | 論文別サマリ | 3h | [ ] |
| 2.2.7 | 可視化データ出力 | `jarvis_core/citation/visualizer.py` | JSON/CSV出力 | 2h | [ ] |
| 2.2.8 | Bundle統合 | `jarvis_core/bundle/assembler.py` | citation_analysis.json追加 | 2h | [ ] |

**成果物例**:
```python
# jarvis_core/citation/schema.py
from pydantic import BaseModel
from enum import Enum

class CitationType(str, Enum):
    """引用タイプ"""
    SUPPORTING = "supporting"      # 支持・同意
    CONTRASTING = "contrasting"    # 反論・矛盾
    MENTIONING = "mentioning"      # 単純言及

class CitationContext(BaseModel):
    """引用文脈"""
    citation_id: str
    citing_paper_id: str
    cited_paper_id: str
    
    # テキスト
    citation_text: str          # 引用を含む文
    context_before: str         # 前の2-3文
    context_after: str          # 後の2-3文
    
    # 分類結果
    citation_type: CitationType
    confidence: float
    
    # 分類根拠
    reasoning: str | None = None
    key_phrases: list[str] = []  # 判断の根拠となったフレーズ

class CitationAnalysis(BaseModel):
    """論文の引用分析結果"""
    paper_id: str
    total_citations: int
    supporting_count: int
    contrasting_count: int
    mentioning_count: int
    
    # 詳細
    citations: list[CitationContext]
    
    # サマリ
    support_ratio: float  # supporting / (supporting + contrasting)
    controversy_score: float  # 論争度スコア
```

---

## Sprint 11-12: 引用分析・可視化 (Week 21-24)

### Task 2.3: 引用ネットワーク可視化

**目標**: ResearchRabbit/Litmaps相当の可視化

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 2.3.1 | グラフデータ構造 | `jarvis_core/graph/schema.py` | Node/Edge Pydanticモデル | 3h | [ ] |
| 2.3.2 | 引用グラフ構築 | `jarvis_core/graph/builder.py` | NetworkX統合 | 4h | [ ] |
| 2.3.3 | クラスタリング | `jarvis_core/graph/clustering.py` | Louvain/Leiden法 | 4h | [ ] |
| 2.3.4 | 重要度スコアリング | `jarvis_core/graph/centrality.py` | PageRank/被引用数 | 3h | [ ] |
| 2.3.5 | タイムライン生成 | `jarvis_core/graph/timeline.py` | 年別論文配置 | 3h | [ ] |
| 2.3.6 | JSON出力（D3.js用） | `jarvis_core/graph/export.py` | force-directed用データ | 3h | [ ] |
| 2.3.7 | Dashboard統合 | `dashboard/graph.html` | インタラクティブ表示 | 8h | [ ] |
| 2.3.8 | CLI可視化コマンド | `jarvis_cli.py` | `visualize-graph` | 2h | [ ] |

**成果物例**:
```python
# jarvis_core/graph/schema.py
from pydantic import BaseModel
from typing import Optional

class GraphNode(BaseModel):
    """グラフノード（論文）"""
    id: str
    paper_id: str
    title: str
    year: int
    citation_count: int
    
    # クラスタリング
    cluster_id: Optional[int] = None
    cluster_label: Optional[str] = None
    
    # 重要度
    importance_score: float = 0.0
    pagerank: float = 0.0
    
    # 表示用
    x: Optional[float] = None
    y: Optional[float] = None
    size: float = 1.0
    color: Optional[str] = None

class GraphEdge(BaseModel):
    """グラフエッジ（引用関係）"""
    id: str
    source: str  # citing paper
    target: str  # cited paper
    
    # 引用タイプ
    citation_type: str  # supporting/contrasting/mentioning
    
    # 重み
    weight: float = 1.0
    
    # 表示用
    color: Optional[str] = None
    width: float = 1.0

class CitationGraph(BaseModel):
    """引用ネットワークグラフ"""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    
    # クラスタ情報
    clusters: list[dict] = []
    
    # メタデータ
    metadata: dict = {}
    
    # 統計
    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    
    def to_d3_json(self) -> dict:
        """D3.js force-directed graph用JSON出力"""
        return {
            "nodes": [n.model_dump() for n in self.nodes],
            "links": [
                {"source": e.source, "target": e.target, **e.model_dump()}
                for e in self.edges
            ],
            "clusters": self.clusters,
            "metadata": self.metadata,
        }
```

---

### Task 2.4: Contradiction検出パイプライン

**目標**: PaperQA2 contracrow相当

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 2.4.1 | Claim正規化 | `jarvis_core/contradiction/normalizer.py` | 主張の標準形式変換 | 4h | [ ] |
| 2.4.2 | 類似Claim検出 | `jarvis_core/contradiction/similarity.py` | 意味的類似度計算 | 4h | [ ] |
| 2.4.3 | 矛盾検出ロジック | `jarvis_core/contradiction/detector.py` | LLM判定 | 6h | [ ] |
| 2.4.4 | 矛盾スコアリング | `jarvis_core/contradiction/scorer.py` | 確信度算出 | 3h | [ ] |
| 2.4.5 | 矛盾レポート生成 | `jarvis_core/contradiction/reporter.py` | Markdown出力 | 3h | [ ] |
| 2.4.6 | パイプライン設定 | `configs/pipelines/contracrow.yml` | 矛盾検出専用パイプライン | 2h | [ ] |
| 2.4.7 | CLIコマンド追加 | `jarvis_cli.py` | `find-contradictions` | 2h | [ ] |

**成果物例**:
```python
# jarvis_core/contradiction/schema.py
from pydantic import BaseModel
from enum import Enum

class ContradictionType(str, Enum):
    """矛盾タイプ"""
    DIRECT = "direct"              # 直接的な主張の対立
    METHODOLOGICAL = "methodological"  # 方法論的な矛盾
    SCOPE = "scope"                # 適用範囲の矛盾
    STATISTICAL = "statistical"    # 統計的な矛盾
    TEMPORAL = "temporal"          # 時間的な矛盾（新知見による否定）

class Contradiction(BaseModel):
    """矛盾の検出結果"""
    contradiction_id: str
    
    # 矛盾する2つの主張
    claim_a: str
    claim_a_paper_id: str
    claim_a_year: int
    
    claim_b: str
    claim_b_paper_id: str
    claim_b_year: int
    
    # 矛盾の詳細
    contradiction_type: ContradictionType
    confidence: float
    
    # 説明
    explanation: str
    key_differences: list[str]
    
    # 解決のヒント
    resolution_hint: str | None = None
    possible_reasons: list[str] = []
```

---

## Sprint 13-14: 系統的レビュー対応 (Week 25-28)

### Task 2.5: PRISMA準拠フローチャート自動生成

**目標**: Rayyan相当のSR対応

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 2.5.1 | PRISMAデータモデル | `jarvis_core/prisma/schema.py` | 各段階の数値記録 | 3h | [ ] |
| 2.5.2 | スクリーニング記録 | `jarvis_core/prisma/tracker.py` | Identification→Screening→Included | 4h | [ ] |
| 2.5.3 | 除外理由記録 | `jarvis_core/prisma/exclusion.py` | カテゴリ別除外数 | 3h | [ ] |
| 2.5.4 | Mermaidフローチャート生成 | `jarvis_core/prisma/flowchart.py` | PRISMA 2020準拠 | 4h | [ ] |
| 2.5.5 | PDF出力 | `jarvis_core/prisma/pdf_export.py` | ReportLab統合 | 4h | [ ] |
| 2.5.6 | Word出力 | `jarvis_core/prisma/docx_export.py` | python-docx統合 | 3h | [ ] |
| 2.5.7 | Bundle統合 | `jarvis_core/bundle/assembler.py` | prisma_flowchart.md追加 | 2h | [ ] |

**成果物例**:
```python
# jarvis_core/prisma/schema.py
from pydantic import BaseModel

class PRISMAData(BaseModel):
    """PRISMA 2020 フローチャートデータ"""
    
    # Identification
    records_identified_databases: int = 0
    records_identified_registers: int = 0
    records_identified_other: int = 0
    
    # Duplicates
    records_removed_duplicates: int = 0
    records_removed_automation: int = 0
    records_removed_other: int = 0
    
    # Screening
    records_screened: int = 0
    records_excluded_screening: int = 0
    
    # Eligibility
    reports_sought_retrieval: int = 0
    reports_not_retrieved: int = 0
    reports_assessed_eligibility: int = 0
    
    # Exclusion reasons
    exclusion_reasons: dict[str, int] = {}
    
    # Included
    studies_included_review: int = 0
    reports_included_review: int = 0
    
    def to_mermaid(self) -> str:
        """Mermaidフローチャート生成"""
        return f"""
flowchart TD
    subgraph Identification
        A1[Records from databases<br>n={self.records_identified_databases}]
        A2[Records from registers<br>n={self.records_identified_registers}]
        A3[Records from other<br>n={self.records_identified_other}]
    end
    
    A1 & A2 & A3 --> B[Records before screening<br>n={self.records_identified_databases + self.records_identified_registers + self.records_identified_other}]
    
    B --> C[Duplicates removed<br>n={self.records_removed_duplicates}]
    C --> D[Records screened<br>n={self.records_screened}]
    
    D --> E[Records excluded<br>n={self.records_excluded_screening}]
    D --> F[Reports sought<br>n={self.reports_sought_retrieval}]
    
    F --> G[Reports not retrieved<br>n={self.reports_not_retrieved}]
    F --> H[Reports assessed<br>n={self.reports_assessed_eligibility}]
    
    H --> I[Reports excluded<br>n={sum(self.exclusion_reasons.values())}]
    H --> J[Studies included<br>n={self.studies_included_review}]
"""
```

---

### Task 2.6: PICO抽出

**目標**: 系統的レビューの構造化

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 2.6.1 | PICOスキーマ | `jarvis_core/pico/schema.py` | Population/Intervention/Comparison/Outcome | 2h | [ ] |
| 2.6.2 | LLM抽出器 | `jarvis_core/pico/extractor.py` | 構造化抽出 | 6h | [ ] |
| 2.6.3 | NER補助抽出 | `jarvis_core/pico/ner_extractor.py` | spaCy/scispaCy | 4h | [ ] |
| 2.6.4 | PICO一致度スコア | `jarvis_core/pico/matcher.py` | 検索クエリとの一致度 | 3h | [ ] |
| 2.6.5 | パイプライン統合 | `configs/pipelines/e2e_oa10.yml` | pico_extractステージ強化 | 2h | [ ] |

---

## Sprint 15-16: マルチモーダル解析 (Week 29-32)

### Task 2.7: マルチモーダルPDF解析

**目標**: PaperQA2相当の図表抽出

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 2.7.1 | PDFパーサー抽象化 | `jarvis_core/extraction/pdf/base.py` | Protocol定義 | 3h | [ ] |
| 2.7.2 | PyMuPDF図表抽出 | `jarvis_core/extraction/pdf/pymupdf_extractor.py` | 画像/テーブル検出 | 6h | [ ] |
| 2.7.3 | テーブルOCR | `jarvis_core/extraction/pdf/table_ocr.py` | Camelot/Tabula統合 | 4h | [ ] |
| 2.7.4 | 図表キャプション抽出 | `jarvis_core/extraction/pdf/caption_extractor.py` | 位置ベース関連付け | 4h | [ ] |
| 2.7.5 | Vision LLM統合 | `jarvis_core/extraction/pdf/vision_llm.py` | GPT-4V/Claude Vision | 6h | [ ] |
| 2.7.6 | 図表エンリッチメント | `jarvis_core/extraction/pdf/enrichment.py` | 合成キャプション生成 | 4h | [ ] |
| 2.7.7 | メディアストレージ | `jarvis_core/extraction/pdf/media_store.py` | 画像保存・参照 | 3h | [ ] |
| 2.7.8 | Bundle統合 | `jarvis_core/bundle/assembler.py` | media/ディレクトリ追加 | 2h | [ ] |

---

## Phase 2 完了チェックリスト

- [ ] Task 2.1: Evidence強度スコアリング
- [ ] Task 2.2: Support/Contrast分類
- [ ] Task 2.3: 引用ネットワーク可視化
- [ ] Task 2.4: Contradiction検出パイプライン
- [ ] Task 2.5: PRISMA準拠フローチャート自動生成
- [ ] Task 2.6: PICO抽出
- [ ] Task 2.7: マルチモーダルPDF解析

**Phase 2 完了基準**:
- Evidence評価がscite相当の精度
- 引用グラフがDashboardで表示可能
- PRISMAフローチャート自動生成
- 図表抽出がPDFから動作
