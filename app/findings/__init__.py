"""
Phase 05 — Finding & Risk Engine package.

Public API:
    FindingEngine  — converts ScanResult → list[SecurityFinding]
    RiskEngine     — converts findings → RiskResult
    SecurityFinding, RiskResult, Evidence  — domain models
    FindingId, Severity, RiskLevel         — constants / enums
"""

from app.findings.engine import FindingEngine
from app.findings.risk_engine import RiskEngine
from app.findings.models import (
    Evidence,
    FindingCategory,
    FindingId,
    RiskLevel,
    RiskResult,
    ScoreContribution,
    SecurityFinding,
    Severity,
)
from app.findings.registry import RULE_REGISTRY, FindingRule, get_rule, all_rules

__all__ = [
    # Engines
    "FindingEngine",
    "RiskEngine",
    # Models
    "Evidence",
    "FindingCategory",
    "FindingId",
    "RiskLevel",
    "RiskResult",
    "ScoreContribution",
    "SecurityFinding",
    "Severity",
    # Registry
    "RULE_REGISTRY",
    "FindingRule",
    "get_rule",
    "all_rules",
]
