"""
Thin client around the Gemini "generateContent" REST endpoint, plus the
prompt templates for the two jobs this app needs:

  1. analyze_requirement()  -> score + issues + a quick suggested rewrite
  2. enhance_requirement()  -> a fuller rewrite that addresses the issues
                                the user confirmed they want fixed

Both functions return a parsed + Pydantic-validated object, or raise
AIClientError with a short, user-safe message (never leaks raw provider
errors/stack traces upward).
"""
import json
import re
import logging
from typing import Optional

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.models.schemas import Issue, AIAnalysisPayload, AIEnhancementPayload

logger = logging.getLogger("ai_requirement_doctor.ai_client")


class AIClientError(Exception):
    """Raised for any AI-call failure. Message is safe to show the user."""


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM_PROMPT = """You are a strict, expert business/systems analyst reviewing a single \
software requirement statement for quality. You are skeptical by default: assume vague wording \
hides real risk.

Score the requirement from 0-100 using this rubric:
- Clarity (0-40): Are all terms concrete and unambiguous? Deduct heavily for vague qualifiers \
like "fast", "quickly", "many", "user-friendly", "secure" with no defined threshold.
- Measurability (0-30): Can the requirement be objectively tested/verified as met or not met? \
Deduct for anything that can't be turned into a pass/fail test.
- Completeness (0-30): Does it cover performance targets, scale/load, error/failure handling, \
security, data constraints, and edge cases where relevant? Deduct for each important dimension \
left unaddressed.

For every problem you find, emit one issue object with:
- "severity": "critical" | "important" | "minor"
- "category": "ambiguity" | "missing" | "conflict" | "other"
- "title": a short label (max ~8 words)
- "explanation": one or two sentences explaining the problem and, where useful, what a fix \
would look like

Also produce a "suggested_rewrite": a single improved version of the requirement that resolves \
the most important issues with concrete, plausible values (clearly a suggestion, not a fact you \
claim to know).

Respond with ONLY valid JSON matching this exact shape, no markdown fences, no commentary:
{"score": <int 0-100>, "issues": [{"severity": "...", "category": "...", "title": "...", \
"explanation": "..."}], "suggested_rewrite": "<string>"}

--- EXAMPLE 1 ---
Requirement: "The application should load quickly and support many users."
Output:
{"score": 18, "issues": [
{"severity": "critical", "category": "ambiguity", "title": "\\"quickly\\" is undefined", \
"explanation": "There is no defined load-time target, so it's impossible to test or verify. \
Specify a maximum acceptable load time, e.g. under 2 seconds."},
{"severity": "critical", "category": "missing", "title": "Maximum response time", \
"explanation": "No response-time SLA is given for normal operations, only page load is \
mentioned."},
{"severity": "important", "category": "missing", "title": "Expected concurrent users", \
"explanation": "\\"many users\\" gives no numeric target, so capacity planning and load testing \
are impossible."},
{"severity": "minor", "category": "missing", "title": "Failure/degradation behavior", \
"explanation": "The requirement does not say what should happen when load exceeds capacity, \
e.g. graceful degradation vs. hard failure."}
], "suggested_rewrite": "The application shall load its main page within 2 seconds (95th \
percentile) under normal conditions and support at least 10,000 concurrent users, degrading to \
a read-only mode if that threshold is exceeded rather than failing outright."}

--- EXAMPLE 2 ---
Requirement: "Users must be able to reset their password securely."
Output:
{"score": 35, "issues": [
{"severity": "critical", "category": "ambiguity", "title": "\\"securely\\" is undefined", \
"explanation": "No security mechanism or standard is specified (e.g. email token, MFA, \
expiry window), so this cannot be verified as met."},
{"severity": "important", "category": "missing", "title": "Token/link expiry not specified", \
"explanation": "How long a reset link remains valid affects both security and usability but is \
unstated."},
{"severity": "important", "category": "missing", "title": "Rate limiting / abuse prevention", \
"explanation": "There is no mention of limits on reset attempts, which is a common attack \
vector."},
{"severity": "minor", "category": "missing", "title": "Audit/notification behavior", \
"explanation": "Whether the user is notified by email when their password changes is not \
addressed."}
], "suggested_rewrite": "Users must be able to reset their password via a single-use, \
time-limited (30 minute) email link sent to their verified address; reset requests are rate-\
limited to 5 per hour per account, and a confirmation email is sent whenever a password is \
successfully changed."}

Now analyze the requirement given by the user and return only the JSON object."""


ENHANCEMENT_SYSTEM_PROMPT = """You are a strict, expert business/systems analyst. You previously \
reviewed a requirement and identified issues. The user has now confirmed they want the \
requirement rewritten to address those issues (and may have supplied extra context/answers).

Rewrite the requirement into a single, complete, testable statement that resolves as many of the \
confirmed issues as reasonably possible, using the user's extra notes where given and otherwise \
filling gaps with clearly reasonable, industry-typical placeholder values. Do not invent specific \
company facts you weren't given (e.g. real company names, dates) — invented numeric targets \
(response times, user counts, retry limits) are fine and expected since that is the point of the \
exercise.

Then re-score the new requirement 0-100 using the same rubric as before (clarity, measurability, \
completeness), and list a short bullet summary of what changed.

Respond with ONLY valid JSON, no markdown fences, no commentary, matching exactly:
{"enhanced_requirement": "<string>", "new_score": <int 0-100>, "summary_of_changes": ["<string>", ...]}

Now produce the enhanced requirement."""


def _extract_json(raw_text: str) -> dict:
    """Gemini is instructed to return raw JSON, but strip markdown fences
    defensively in case it adds them anyway, then parse."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    # If there's leading/trailing prose around the JSON object, grab the
    # outermost {...} block.
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse AI JSON response: %s", exc)
        raise AIClientError(
            "The AI returned a response we couldn't understand. Please try again."
        ) from exc


async def _call_gemini(system_prompt: str, user_content: str) -> str:
    if not settings.GEMINI_API_KEY:
        raise AIClientError(
            "The server is not configured with an AI provider API key. "
            "Set GEMINI_API_KEY on the backend."
        )

    url = (
        f"{settings.GEMINI_API_BASE}/models/{settings.GEMINI_MODEL}:generateContent"
        f"?key={settings.GEMINI_API_KEY}"
    )
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.GEMINI_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json=body)
    except httpx.TimeoutException as exc:
        raise AIClientError("The AI provider took too long to respond. Please try again.") from exc
    except httpx.HTTPError as exc:
        logger.error("Network error calling Gemini: %s", exc)
        raise AIClientError("Could not reach the AI provider. Please try again shortly.") from exc

    if resp.status_code == 429:
        raise AIClientError("The AI provider is rate-limiting requests. Please try again shortly.")
    if resp.status_code >= 400:
        logger.error("Gemini API error %s: %s", resp.status_code, resp.text[:500])
        raise AIClientError("The AI provider returned an error. Please try again.")

    try:
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError) as exc:
        logger.error("Unexpected Gemini response shape: %s", exc)
        raise AIClientError("Received an unexpected response from the AI provider.") from exc

    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_requirement(requirement_text: str) -> AIAnalysisPayload:
    raw = await _call_gemini(ANALYSIS_SYSTEM_PROMPT, requirement_text)
    parsed = _extract_json(raw)
    try:
        return AIAnalysisPayload.model_validate(parsed)
    except ValidationError as exc:
        logger.warning("AI analysis payload failed validation: %s", exc)
        raise AIClientError(
            "The AI response didn't match the expected format. Please try again."
        ) from exc


async def enhance_requirement(
    requirement_text: str, issues: list[Issue], user_notes: Optional[str]
) -> AIEnhancementPayload:
    issues_block = "\n".join(
        f"- [{i.severity}/{i.category}] {i.title}: {i.explanation}" for i in issues
    ) or "(no specific issues supplied — use your own judgement)"

    user_content = (
        f"Original requirement:\n{requirement_text}\n\n"
        f"Confirmed issues to address:\n{issues_block}\n\n"
        f"User-supplied extra context/answers: {user_notes or '(none provided)'}"
    )

    raw = await _call_gemini(ENHANCEMENT_SYSTEM_PROMPT, user_content)
    parsed = _extract_json(raw)
    try:
        return AIEnhancementPayload.model_validate(parsed)
    except ValidationError as exc:
        logger.warning("AI enhancement payload failed validation: %s", exc)
        raise AIClientError(
            "The AI response didn't match the expected format. Please try again."
        ) from exc
