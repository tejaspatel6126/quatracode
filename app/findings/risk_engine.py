"""
Risk Engine — Phase 05.

Converts a list of SecurityFindings into a deterministic RiskResult.

DESIGN RULES:
  - Deterministic: same findings + scoring_version → same score, always.
  - Score range: 0–100 (PHASE_05 §26).
  - Severity weights from documented spec (§27).
  - INFO findings contribute 0 risk (§34).
  - Duplicate findings must not inflate score — FindingEngine deduplicates first.
  - No user-controlled weights.
  - No AI.

SCORING ALGORITHM (version "1.0"):
  1. Assign weight to each finding by severity.
  2. Sum raw weights.
  3. Normalize to 0–100 using a defined maximum raw score.
  4. Apply floor(clamp(score, 0, 100)).
  5. Map final score to RiskLevel.

Weights (severity → raw points):
  CRITICAL → 40
  HIGH     → 25
  MEDIUM   → 10
  LOW      →  5
  INFO     →  0

MAX_RAW_SCORE: 100 (normalization ceiling).
Score capped at 100 regardless of raw sum.
Empty findings → score 0 (cleanest possible).
"""

from __future__ import annotations

import datetime
import logging

from app.findings.models import (
    RiskLevel,
    RiskResult,
    ScoreContribution,
    SecurityFinding,
    Severity,
)

logger = logging.getLogger(__name__)

# ── Scoring constants (PHASE_05 §27) ──────────────────────────────────────────
# Do not change without bumping SCORING_VERSION.

SCORING_VERSION = "1.0"

# Severity → raw points contribution
_SEVERITY_WEIGHTS: dict[Severity, float] = {
    Severity.CRITICAL: 40.0,
    Severity.HIGH:     25.0,
    Severity.MEDIUM:   10.0,
    Severity.LOW:       5.0,
    Severity.INFO:      0.0,
}

# Raw score at which we reach 100 on the normalized scale.
# This is intentionally set so 2 CRITICALs (80 raw) → ~80, capped at 100.
_MAX_RAW_SCORE: float = 100.0

# Risk level thresholds (PHASE_05 §30)
_RISK_THRESHOLDS: list[tuple[float, RiskLevel]] = [
    (80.0, RiskLevel.CRITICAL),
    (60.0, RiskLevel.HIGH),
    (40.0, RiskLevel.MEDIUM),
    (20.0, RiskLevel.LOW),
    ( 0.0, RiskLevel.VERY_LOW),
]


class RiskEngine:
    """
    Calculates the overall risk score from a list of deduplicated SecurityFindings.

    Usage:
        engine = RiskEngine()
        result = engine.calculate(findings)
    """

    def calculate(self, findings: list[SecurityFinding]) -> RiskResult:
        """
        Produce a deterministic RiskResult from a list of SecurityFindings.

        Parameters
        ----------
        findings : list[SecurityFinding]
            Deduplicated findings from FindingEngine.run().

        Returns
        -------
        RiskResult
            Score, risk level, breakdown, scoring version.
        """
        if not findings:
            return self._empty_result()

        severity_counts: dict[str, int] = {s.value: 0 for s in Severity}
        contributions:   list[ScoreContribution] = []
        raw_total = 0.0

        for finding in findings:
            weight = _SEVERITY_WEIGHTS[finding.severity]
            raw_total += weight
            severity_counts[finding.severity.value] += 1

            # Individual contribution as fraction of max, pre-normalization
            contribution_pct = (weight / _MAX_RAW_SCORE) * 100.0

            contributions.append(ScoreContribution(
                finding_id   = finding.finding_id,
                severity     = finding.severity,
                weight       = weight,
                contribution = round(min(contribution_pct, 100.0), 2),
            ))

        # Normalize and clamp
        normalized = (raw_total / _MAX_RAW_SCORE) * 100.0
        final_score = round(max(0.0, min(100.0, normalized)), 2)

        risk_level = _score_to_level(final_score)

        result = RiskResult(
            score           = final_score,
            risk_level      = risk_level,
            finding_count   = len(findings),
            severity_counts = severity_counts,
            contributions   = contributions,
            scoring_version = SCORING_VERSION,
            findings        = findings,
            computed_at     = datetime.datetime.now(tz=datetime.timezone.utc),
        )

        logger.info(
            "Risk engine: score=%.2f level=%s findings=%d (CRIT=%d HIGH=%d MED=%d LOW=%d)",
            final_score,
            risk_level.value,
            len(findings),
            severity_counts.get("CRITICAL", 0),
            severity_counts.get("HIGH", 0),
            severity_counts.get("MEDIUM", 0),
            severity_counts.get("LOW", 0),
        )

        return result

    def _empty_result(self) -> RiskResult:
        return RiskResult(
            score           = 0.0,
            risk_level      = RiskLevel.VERY_LOW,
            finding_count   = 0,
            severity_counts = {s.value: 0 for s in Severity},
            contributions   = [],
            scoring_version = SCORING_VERSION,
            findings        = [],
            computed_at     = datetime.datetime.now(tz=datetime.timezone.utc),
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _score_to_level(score: float) -> RiskLevel:
    """Map a 0–100 score to a RiskLevel using documented thresholds (§30)."""
    for threshold, level in _RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return RiskLevel.VERY_LOW
