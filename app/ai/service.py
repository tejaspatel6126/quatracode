"""
AI Service — Phase 08.

Orchestrates:
  1. Sanitize finding data (sanitizer.py)
  2. Build prompts (prompts.py)
  3. Call AI provider (provider.py)
  4. Parse and validate response (schemas.py)
  5. Return structured explanation or deterministic fallback

INVARIANT: This service NEVER modifies findings, severity, or risk scores.
It only produces explanations consumed by Phase 06 API and Phase 07 frontend.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from app.ai.prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_finding_prompt,
    build_scan_summary_prompt,
)
from app.ai.provider import AIProvider, AIProviderError, get_ai_provider
from app.ai.sanitizer import sanitize_finding
from app.ai.schemas import (
    AIStatus,
    FindingExplanation,
    ScanAISummary,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AIService:
    """
    AI Explanation Service.

    Accepts deterministic finding data; produces structured explanations.
    Falls back gracefully to deterministic text if AI is unavailable.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._settings = get_settings()
        self._provider = provider  # Injectable for testing

    def _get_provider(self) -> AIProvider:
        return self._provider or get_ai_provider()

    # ── Public API ─────────────────────────────────────────────────────────────

    async def explain_scan(
        self,
        scan_id: str,
        hostname: str,
        scheme: str,
        risk_score: float,
        risk_level: str,
        findings: list[dict],
    ) -> ScanAISummary:
        """
        Generate an AI explanation for an entire scan.

        Parameters
        ----------
        scan_id   : str  — scan UUID (for logging)
        hostname  : str  — target hostname
        scheme    : str  — http or https
        risk_score: float — deterministic risk score (0-100)
        risk_level: str   — deterministic risk level
        findings  : list[dict] — finding dicts from DB / finding engine

        Returns
        -------
        ScanAISummary — always returns, falling back to deterministic text
        """
        if not self._settings.AI_ENABLED:
            logger.debug("AI disabled — returning deterministic fallback for scan %s", scan_id)
            return self._fallback_summary(risk_score, risk_level, findings)

        # Limit to top 20 findings
        capped_findings = findings[:20]

        # Sanitize before sending to AI
        sanitized = [sanitize_finding(f) for f in capped_findings]

        # Build findings text
        findings_text = _format_findings_for_prompt(sanitized)

        # Generate per-finding explanations
        finding_explanations: list[FindingExplanation] = []
        for sf in sanitized[:10]:   # max 10 individual explanations
            expl = await self._explain_single_finding(sf)
            finding_explanations.append(expl)

        # Generate overall scan summary
        prompt = build_scan_summary_prompt(
            hostname=hostname,
            scheme=scheme,
            risk_score=risk_score,
            risk_level=risk_level,
            findings_text=findings_text,
        )

        try:
            raw = await self._get_provider().complete(SYSTEM_PROMPT, prompt)
            parsed = _parse_json_response(raw)

            summary = ScanAISummary(
                executive_summary    = _truncate(parsed.get("executive_summary", ""), 1500),
                technical_summary    = _truncate(parsed.get("technical_summary", ""), 1500),
                top_priorities       = [str(p)[:150] for p in (parsed.get("top_priorities") or [])[:5]],
                finding_explanations = finding_explanations,
                ai_status            = AIStatus.GENERATED,
                prompt_version       = PROMPT_VERSION,
                model_used           = self._settings.AI_MODEL,
            )
            logger.info(
                "AI summary generated for scan=%s findings=%d",
                scan_id, len(finding_explanations),
            )
            return summary

        except AIProviderError as exc:
            logger.warning(
                "AI provider failed for scan=%s code=%s — falling back",
                scan_id, exc.code,
            )
            fallback = self._fallback_summary(risk_score, risk_level, findings)
            fallback.finding_explanations = finding_explanations  # Keep any per-finding successes
            return fallback

        except Exception as exc:
            logger.exception("Unexpected AI error for scan=%s: %s", scan_id, exc)
            return self._fallback_summary(risk_score, risk_level, findings)

    async def _explain_single_finding(self, sf: dict) -> FindingExplanation:
        """
        Generate an explanation for a single sanitized finding.
        Falls back to deterministic text on any failure.
        """
        finding_code = sf.get("finding_code", "")
        evidence_text = " | ".join(sf.get("evidence", [])) or "No additional evidence."

        prompt = build_finding_prompt(
            finding_code  = finding_code,
            title         = sf.get("title", ""),
            severity      = sf.get("severity", ""),
            category      = sf.get("category", ""),
            description   = sf.get("description", ""),
            evidence_text = evidence_text,
            remediation   = sf.get("remediation", ""),
        )

        try:
            raw    = await self._get_provider().complete(SYSTEM_PROMPT, prompt)
            parsed = _parse_json_response(raw)

            return FindingExplanation(
                finding_code      = finding_code,
                summary           = _truncate(parsed.get("summary", ""), 600),
                why_it_matters    = _truncate(parsed.get("why_it_matters", ""), 800),
                impact            = _truncate(parsed.get("impact", ""), 800),
                recommendation    = _truncate(parsed.get("recommendation", ""), 1000),
                owner_explanation = _truncate(parsed.get("owner_explanation", ""), 600),
                ai_status         = AIStatus.GENERATED,
                prompt_version    = PROMPT_VERSION,
            )

        except (AIProviderError, Exception) as exc:
            logger.warning(
                "AI finding explanation failed for %s: %s — using fallback",
                finding_code, exc,
            )
            return _fallback_finding_explanation(sf)

    # ── Deterministic fallback ─────────────────────────────────────────────────

    def _fallback_summary(
        self,
        risk_score: float,
        risk_level: str,
        findings: list[dict],
    ) -> ScanAISummary:
        """Return a deterministic summary when AI is unavailable."""
        count = len(findings)
        level = risk_level.replace("_", " ").title()

        categories = list({
            (f.get("category") or "").replace("_", " ").title()
            for f in findings
            if f.get("category")
        })

        exec_summary = (
            f"The scan identified {count} security finding(s) with an overall risk level of {level} "
            f"(score: {risk_score:.0f}/100). "
            "Review the detailed findings below and prioritise the highest-severity items."
        ) if count else (
            f"No security findings were detected. Risk level: {level} (score: {risk_score:.0f}/100)."
        )

        tech_summary = (
            f"Scan detected {count} finding(s) across the following categories: "
            f"{', '.join(categories) or 'general security'}. "
            "See individual findings for technical detail and remediation guidance."
        ) if count else (
            "All security checks passed. No configuration issues were detected."
        )

        priorities = []
        for f in findings[:3]:
            title = f.get("title", "")
            if title:
                priorities.append(f"Address: {title}")

        return ScanAISummary(
            executive_summary    = exec_summary,
            technical_summary    = tech_summary,
            top_priorities       = priorities,
            finding_explanations = [_fallback_finding_explanation(sanitize_finding(f)) for f in findings[:10]],
            ai_status            = AIStatus.FALLBACK,
            prompt_version       = PROMPT_VERSION,
            model_used           = "",
        )


# ── Private helpers ───────────────────────────────────────────────────────────

def _fallback_finding_explanation(sf: dict) -> FindingExplanation:
    """Build a deterministic FindingExplanation from sanitized finding data."""
    return FindingExplanation(
        finding_code      = sf.get("finding_code", ""),
        summary           = sf.get("description") or sf.get("title") or "Security finding detected.",
        why_it_matters    = "This configuration issue may reduce the security of the target website.",
        impact            = "Review the finding description and apply the recommended remediation.",
        recommendation    = sf.get("remediation") or "Apply the recommended configuration change.",
        owner_explanation = sf.get("title") or "A security configuration issue was detected.",
        ai_status         = AIStatus.FALLBACK,
        prompt_version    = PROMPT_VERSION,
    )


def _format_findings_for_prompt(sanitized: list[dict]) -> str:
    """Format sanitized findings as structured text for the prompt."""
    if not sanitized:
        return "No findings detected."
    lines: list[str] = []
    for i, f in enumerate(sanitized, 1):
        evidence = " | ".join(f.get("evidence", [])) or "none"
        lines.append(
            f"{i}. [{f.get('severity', '?')}] {f.get('title', '?')} "
            f"(code: {f.get('finding_code', '?')}) — Evidence: {evidence}"
        )
    return "\n".join(lines)


def _parse_json_response(raw: str) -> dict:
    """
    Parse JSON from AI response.

    Handles cases where the model wraps JSON in markdown code fences.
    """
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last line if they are fence lines
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _truncate(text: str, max_len: int) -> str:
    if not text:
        return ""
    return text[:max_len]
