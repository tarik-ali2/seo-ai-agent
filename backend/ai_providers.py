"""
Unified AI provider abstraction.

Priority:
  1. Google Gemini  (if GEMINI_API_KEY is set)
  2. Anthropic Claude (if ANTHROPIC_API_KEY is set)

Both providers are asked to return structured JSON only.
The caller always receives a plain Python dict — never raw text.
"""
import os
import json
from logger import get_logger

log = get_logger("seo_agent.ai_providers")

# Primary Gemini model (override with GEMINI_MODEL env var)
# Fallback cascade: gemini-2.5-flash → gemini-2.0-flash-lite → gemini-2.0-flash
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_GEMINI_FALLBACK_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash"]

# Anthropic fallback model
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


# ── Public API ────────────────────────────────────────────────────────────────

def generate_json(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2048,
) -> dict:
    """
    Send prompts to the best available AI provider and return parsed JSON dict.

    Tries Gemini first, automatically falls back to Anthropic on any failure.
    Returns {"error": "..."} if no provider is configured or all fail.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        # Try primary model, then each fallback model before giving up on Gemini
        models_to_try = [GEMINI_MODEL] + [m for m in _GEMINI_FALLBACK_MODELS if m != GEMINI_MODEL]
        for model in models_to_try:
            result = _gemini(system_prompt, user_prompt, max_tokens, gemini_key, model=model)
            if not _is_error(result):
                return result
            err = result.get("error", "unknown")
            # Auth/billing errors are fatal — don't try other models
            if _is_fatal_error(err):
                log.warning("Gemini auth/billing error, skipping all Gemini models: %s", err)
                break
            log.warning("Gemini model %s failed (%s), trying next model", model, err[:120])

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key.startswith("sk-ant"):
        result = _anthropic(system_prompt, user_prompt, max_tokens, anthropic_key)
        if not _is_error(result):
            return result
        log.warning("Anthropic also failed: %s", result.get("error", "unknown"))

    return {
        "error": (
            "No AI provider available. "
            "Set GEMINI_API_KEY or ANTHROPIC_API_KEY in backend/.env"
        )
    }


def active_provider() -> str:
    """Return which provider will be tried first: 'gemini', 'anthropic', or 'none'."""
    if os.getenv("GEMINI_API_KEY", "").strip():
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY", "").strip().startswith("sk-ant"):
        return "anthropic"
    return "none"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _is_error(result: dict) -> bool:
    return isinstance(result, dict) and "error" in result


def _is_fatal_error(err_msg: str) -> bool:
    """Returns True for errors that shouldn't trigger a model retry.

    Only hard auth failures are fatal — quota/rate limits should try the next model.
    """
    lower = err_msg.lower()
    # 429 RESOURCE_EXHAUSTED and 503 UNAVAILABLE are transient — retry with next model
    if "resource_exhausted" in lower or "unavailable" in lower:
        return False
    return any(w in lower for w in ("api_key", "invalid_api", "permission_denied", "not enabled"))


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that some models add despite being told not to."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first line (```json / ```) and last line (```)
        inner = lines[1:] if lines[0].startswith("```") else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner)
    return text.strip()


# ── Gemini provider ───────────────────────────────────────────────────────────

def _gemini(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    api_key: str,
    model: str | None = None,
) -> dict:
    model = model or GEMINI_MODEL
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                max_output_tokens=max_tokens,
                temperature=0.3,
            ),
        )

        raw = response.text.strip() if response.text else ""
        if not raw:
            return {"error": "Gemini returned empty response"}

        result = json.loads(_strip_fences(raw))
        log.info("Gemini (%s) responded — %d chars", model, len(raw))
        return result

    except json.JSONDecodeError as e:
        log.warning("Gemini JSON parse error: %s | raw: %.200s", e, raw if "raw" in dir() else "")
        return {"error": f"Gemini JSON parse error: {e}"}
    except Exception as e:
        err_type = type(e).__name__
        err_msg = str(e)
        log.warning("Gemini %s: %s", err_type, err_msg)
        return {"error": f"Gemini {err_type}: {err_msg}", "provider": "gemini"}


# ── Anthropic provider ────────────────────────────────────────────────────────

def _anthropic(system_prompt: str, user_prompt: str, max_tokens: int, api_key: str) -> dict:
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = message.content[0].text.strip()
        result = json.loads(_strip_fences(raw))
        log.info("Anthropic (%s) responded — %d chars", ANTHROPIC_MODEL, len(raw))
        return result

    except json.JSONDecodeError as e:
        log.warning("Anthropic JSON parse error: %s", e)
        return {"error": f"Anthropic JSON parse error: {e}"}
    except Exception as e:
        err_type = type(e).__name__
        log.warning("Anthropic %s: %s", err_type, e)
        return {"error": f"Anthropic {err_type}: {str(e)}", "provider": "anthropic"}
