"""JARVIS PRISMA Module.

PRISMA flow diagram generation for systematic reviews.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.4
"""

from jarvis_core.experimental.prisma.generator import PRISMAGenerator, generate_prisma_flow
from jarvis_core.experimental.prisma.schema import (
    ExclusionReason,
    PRISMAData,
    PRISMAStage,
)

__all__ = [
    "PRISMAData",
    "PRISMAStage",
    "ExclusionReason",
    "PRISMAGenerator",
    "generate_prisma_flow",
]