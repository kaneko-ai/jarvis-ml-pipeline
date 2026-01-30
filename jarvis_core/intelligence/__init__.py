"""
JARVIS Intelligence Module

Phase 1-4: 知能密度向上
- Phase 1: 判断材料化（5軸評価）
- Phase 2: 再利用知能（DecisionItem）
- Phase 3: 自己評価（成績表）
- Phase 4: 研究パートナー（問い生成）
"""

from .action_planner import (
    ActionItem,
    ActionPlanner,
    ActionType,
)
from .decision import (
    DecisionMaker,
    DecisionStatus,
    JudgmentDecision,
    RejectReason,
)
from .decision_item import (
    DecisionItem,
    DecisionPattern,
    DecisionStore,
)
from .evaluator_v2 import (
    EvaluationAxis,
    IntelligentEvaluator,
    ScoreBreakdown,
)
from .goldset_index import (
    GoldsetEntry,
    GoldsetIndex,
)
from .mandatory_search import (
    MandatorySearchJudge,
    MandatorySearchResult,
    Phase2Decision,
    SimilarJudgment,
)
from .metrics_collector import (
    JudgmentMetrics,
    MetricsCollector,
)
from .outcome_tracker import (
    OutcomeRecord,
    OutcomeStatus,
    OutcomeTracker,
)
from .patterns import PatternExtractor
from .question_generator import QuestionGenerator
from .research_partner import (
    KeyQuestions,
    ResearchPartner,
    ResearchPartnerOutput,
    StrategicAssessment,
)
from .similarity import SimilaritySearcher

__all__ = [
    # Phase 1
    "EvaluationAxis",
    "ScoreBreakdown",
    "IntelligentEvaluator",
    "DecisionStatus",
    "RejectReason",
    "JudgmentDecision",
    "DecisionMaker",
    # Phase 2
    "DecisionPattern",
    "DecisionItem",
    "DecisionStore",
    "SimilaritySearcher",
    "PatternExtractor",
    # Phase 3
    "OutcomeStatus",
    "OutcomeRecord",
    "OutcomeTracker",
    "JudgmentMetrics",
    "MetricsCollector",
    # Phase 4
    "QuestionGenerator",
    "ActionType",
    "ActionItem",
    "ActionPlanner",
    # Phase 2 (強化)
    "GoldsetEntry",
    "GoldsetIndex",
    "SimilarJudgment",
    "MandatorySearchResult",
    "Phase2Decision",
    "MandatorySearchJudge",
    # Research Partner (Phase 4-7)
    "StrategicAssessment",
    "KeyQuestions",
    "ResearchPartnerOutput",
    "ResearchPartner",
]