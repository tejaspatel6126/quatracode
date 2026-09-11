"""
AI Provider abstraction — Phase 08.

Defines the AIProvider interface and the concrete OpenAIProvider.
Additional providers can be added without changing service.py or the API.

SECURITY:
  - API key is read from settings only — never hardcoded.
  - API key is NEVER sent to the frontend.
  - Requests have strict timeouts.
  - Raw provider errors are never exposed to the user.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


# ── Abstract base ─────────────────────────────────────────────────────────────

class AIProvider(ABC):
    """Abstract interface for AI providers."""

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Send a completion request and return the raw text response.

        Raises AIProviderError on failure.
        """
        ...


# ── Error types ───────────────────────────────────────────────────────────────

class AIProviderError(Exception):
    """Raised when the AI provider call fails for any reason."""
    def __init__(self, code: str, message: str) -> None:
        self.code    = code
        self.message = message
        super().__init__(f"{code}: {message}")


# ── OpenAI-compatible provider ────────────────────────────────────────────────

class OpenAIProvider(AIProvider):
    """
    Concrete provider for OpenAI (and OpenAI-compatible) APIs.

    Works with:
      - OpenAI (AI_PROVIDER=openai, AI_MODEL=gpt-4o-mini etc.)
      - Google Gemini via OpenAI-compatible endpoint
      - Any other OpenAI-compatible API

    Configuration (all via environment / .env — never hardcoded):
      AI_API_KEY  — provider API key
      AI_MODEL    — model identifier
      AI_TIMEOUT  — request timeout in seconds
      AI_MAX_TOKENS — maximum tokens in the response
    """

    # Provider-specific base URLs
    _BASE_URLS: dict[str, str] = {
        "openai":  "https://api.openai.com/v1",
        "gemini":  "https://generativelanguage.googleapis.com/v1beta/openai",
        "groq":    "https://api.groq.com/openai/v1",
    }

    def __init__(self) -> None:
        self._settings = get_settings()

    def _base_url(self) -> str:
        provider = self._settings.AI_PROVIDER.lower()
        return self._BASE_URLS.get(provider, self._BASE_URLS["openai"])

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        settings = self._settings

        if not settings.AI_API_KEY:
            raise AIProviderError("AI_UNAVAILABLE", "AI API key is not configured.")

        url = f"{self._base_url()}/chat/completions"

        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "max_tokens":  settings.AI_MAX_TOKENS,
            "temperature": 0.3,   # Low temperature for consistent explanations
        }

        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type":  "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException:
            logger.warning("AI provider request timed out after %ss", settings.AI_TIMEOUT)
            raise AIProviderError("AI_TIMEOUT", "AI request timed out.")
        except httpx.HTTPError as exc:
            logger.warning("AI provider HTTP error: %s", type(exc).__name__)
            raise AIProviderError("AI_PROVIDER_ERROR", "AI provider connection failed.")

        if response.status_code == 429:
            raise AIProviderError("AI_RATE_LIMITED", "AI provider rate limit exceeded.")

        if not response.is_success:
            logger.warning(
                "AI provider returned HTTP %d: %s",
                response.status_code,
                response.text[:200],
            )
            raise AIProviderError(
                "AI_PROVIDER_ERROR",
                f"AI provider returned HTTP {response.status_code}.",
            )

        try:
            data    = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            logger.warning("AI provider response malformed: %s", exc)
            raise AIProviderError("AI_INVALID_RESPONSE", "AI response could not be parsed.")

        return content


# ── Factory ───────────────────────────────────────────────────────────────────

def get_ai_provider() -> AIProvider:
    """
    Return the configured AI provider instance.

    Currently supports: openai, gemini, groq (all OpenAI-compatible).
    Falls back to OpenAIProvider for unknown providers since most
    modern providers support the OpenAI chat completions API.
    """
    settings = get_settings()
    provider_name = settings.AI_PROVIDER.lower()

    if provider_name in ("openai", "gemini", "groq", ""):
        return OpenAIProvider()

    # Default — try OpenAI-compatible
    logger.warning(
        "Unknown AI provider %r — attempting OpenAI-compatible protocol.", provider_name
    )
    return OpenAIProvider()
