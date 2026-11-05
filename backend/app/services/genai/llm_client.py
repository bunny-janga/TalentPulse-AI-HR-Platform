"""Provider-agnostic LLM client (Gemini, Groq or OpenAI) built on the standard library only.

Why this replaced the old client:
* the old default model name did not exist, so EVERY live call failed silently and users got canned text;
* failures were swallowed with `except: pass`, so nobody could tell the "AI" was not running.
Now failures are logged with a reason, callers receive an explicit mode ("live" or "offline"), and the UI shows it.
A short circuit-breaker stops a dead provider from adding a timeout to every request.
"""
import json
import logging
import time
import urllib.error
import urllib.request
from typing import Optional, Tuple

from app.core.config import settings

log = logging.getLogger("talentpulse.llm")


class LLMUnavailable(Exception):
    """Raised when no provider is configured or the provider call failed."""


class LLMClient:
    COOLDOWN_SECONDS = 45

    def __init__(self):
        self._down_until = 0.0
        self.last_error: Optional[str] = None

    # ---- configuration -------------------------------------------------
    @property
    def provider(self) -> str:
        return (settings.LLM_PROVIDER or "gemini").strip().lower()

    def _key(self) -> Optional[str]:
        key = {"gemini": settings.GEMINI_API_KEY, "groq": settings.GROQ_API_KEY, "openai": settings.OPENAI_API_KEY}.get(self.provider)
        return key.strip() if key and key.strip() else None

    @property
    def model_name(self) -> str:
        return {"gemini": settings.GEMINI_MODEL, "groq": settings.GROQ_MODEL, "openai": settings.OPENAI_MODEL}.get(self.provider, settings.GEMINI_MODEL)

    def is_configured(self) -> bool:
        return self._key() is not None

    # ---- transport -----------------------------------------------------
    def _post(self, url: str, headers: dict, payload: dict) -> dict:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", **headers}, method="POST")
        with urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as resp:  # noqa: S310 (fixed https endpoints)
            return json.loads(resp.read().decode("utf-8"))

    def _call(self, prompt: str, system: Optional[str], temperature: float) -> str:
        key = self._key()
        if self.provider == "gemini":
            body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": temperature}}
            if system:
                body["systemInstruction"] = {"parts": [{"text": system}]}
            data = self._post(f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent", {"x-goog-api-key": key}, body)
            parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts).strip()
        base = "https://api.groq.com/openai/v1" if self.provider == "groq" else "https://api.openai.com/v1"
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        data = self._post(f"{base}/chat/completions", {"Authorization": f"Bearer {key}"}, {"model": self.model_name, "messages": messages, "temperature": temperature})
        return (data["choices"][0]["message"]["content"] or "").strip()

    # ---- public API ----------------------------------------------------
    def complete(self, prompt: str, system: Optional[str] = None, temperature: float = 0.2) -> str:
        """Return model text or raise LLMUnavailable (never returns fabricated text)."""
        if not self.is_configured():
            self.last_error = f"No API key configured for provider '{self.provider}'"
            raise LLMUnavailable(self.last_error)
        if time.monotonic() < self._down_until:
            raise LLMUnavailable(self.last_error or "LLM temporarily unavailable")
        try:
            text = self._call(prompt, system, temperature)
            if not text:
                raise LLMUnavailable("The model returned an empty response")
            self.last_error = None
            return text
        except LLMUnavailable as exc:
            self.last_error = str(exc)
            raise
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "ignore")[:200]
            except Exception:  # pragma: no cover
                pass
            self.last_error = f"{self.provider} HTTP {exc.code}: {detail}"
        except Exception as exc:  # network, timeout, bad JSON
            self.last_error = f"{self.provider} call failed: {exc}"
        log.warning("LLM call failed (%s); using offline fallback", self.last_error)
        self._down_until = time.monotonic() + self.COOLDOWN_SECONDS
        raise LLMUnavailable(self.last_error)

    def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.2) -> Tuple[Optional[str], str]:
        """(text, mode): mode is 'live' with text, or 'offline' with None so the caller can build a grounded fallback."""
        try:
            return self.complete(prompt, system, temperature), "live"
        except LLMUnavailable:
            return None, "offline"


llm_client = LLMClient()
