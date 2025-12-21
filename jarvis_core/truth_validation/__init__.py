"""Truth Validation package.

Per V4-B, this provides truthfulness validation for claims and facts.
"""
from .claim_fact import ClaimFactChecker, check_claim_fact_alignment

__all__ = ["ClaimFactChecker", "check_claim_fact_alignment"]
