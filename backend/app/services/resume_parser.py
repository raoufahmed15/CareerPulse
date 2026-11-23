"""
LLM-based Resume Parser.

Replaces manual/regex parsing (checkpoint section 4). Raw OCR/PDF
text is sent to an LLM, which returns structured JSON. That JSON
is then validated against ResumeSchema (Pydantic) before it is
trusted anywhere else in the system (checkpoint section 8).

Pipeline:

    raw_text
        -> LLM (llm_providers.get_llm_provider)
        -> JSON string
        -> dict
        -> ResumeSchema (Pydantic validation)
        -> Resume Object
"""

import json
import logging
import re
from typing import Any, Dict

from pydantic import ValidationError

from app.schemas.resume import ResumeSchema
from app.services.llm_providers import get_llm_provider


logger = logging.getLogger(__name__)


class ResumeParsingError(Exception):
    """Raised whenever the LLM output cannot be turned into a valid ResumeSchema."""


# ============================================================
# Prompt
# ============================================================

_SYSTEM_INSTRUCTIONS = """You are a resume/CV parser.

You will be given raw text extracted from a CV (via PDF extraction
or OCR). The text may contain OCR artifacts: missing spaces between
words, broken lines, or misread characters (e.g. "1" instead of "I").
Use your best judgment to reconstruct the intended meaning.

Return ONLY a single JSON object, with no markdown code fences and
no explanation text before or after it. The JSON object MUST use
exactly this shape (omit nothing, use null or empty lists/strings
for anything not present in the CV):

{
  "name": string or null,
  "title": string or null,
  "email": string or null,
  "phone": string or null,
  "location": string or null,
  "summary": string or null,
  "skills": [string, ...],
  "education": [
    {
      "institution": string or null,
      "degree": string or null,
      "field_of_study": string or null,
      "start_date": string or null,
      "end_date": string or null,
      "description": string or null
    }
  ],
  "experience": [
    {
      "company": string or null,
      "role": string or null,
      "location": string or null,
      "start_date": string or null,
      "end_date": string or null,
      "description": string or null,
      "responsibilities": [string, ...]
    }
  ],
  "projects": [
    {
      "name": string or null,
      "description": string or null,
      "technologies": [string, ...],
      "url": string or null
    }
  ],
  "certifications": [
    {"name": string or null, "issuer": string or null, "date": string or null}
  ],
  "courses": [
    {"name": string or null, "provider": string or null, "date": string or null}
  ],
  "languages": [
    {"name": string or null, "proficiency": string or null}
  ]
}

Rules:
- Do not invent information that is not in the text.
- Dates should be kept as they appear in the CV (e.g. "2021", "Jan 2021 - Present").
- "skills" should be a flat, de-duplicated list of individual skills, not sentences.
"""


def _build_prompt(raw_text: str) -> str:
    return f"{_SYSTEM_INSTRUCTIONS}\n\nCV TEXT:\n\"\"\"\n{raw_text}\n\"\"\"\n"


# ============================================================
# JSON extraction
# ============================================================

def _extract_json(llm_output: str) -> Dict[str, Any]:
    """
    LLM providers with JSON mode enabled should return clean JSON,
    but this is a defensive layer in case markdown fences or stray
    text slip through.
    """

    if not llm_output or not llm_output.strip():
        raise ValueError("Empty response from LLM.")

    text = llm_output.strip()

    # Strip ```json ... ``` or ``` ... ``` fences if present
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # Fallback: grab the outermost { ... } block
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end < start:
            raise ValueError("No JSON object found in LLM response.")

        text = text[start : end + 1]

    return json.loads(text)


# ============================================================
# Public API
# ============================================================

def parse_resume(raw_text: str) -> ResumeSchema:
    """
    Turn raw resume text into a validated ResumeSchema.

    Raises ResumeParsingError if the LLM call fails, the response
    is not valid JSON, or the JSON does not match ResumeSchema.
    """

    if not raw_text or not raw_text.strip():
        raise ResumeParsingError("Empty resume text provided.")

    provider = get_llm_provider()
    prompt = _build_prompt(raw_text)

    try:
        llm_output = provider.generate(prompt)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        raise ResumeParsingError(f"LLM request failed: {e}") from e

    try:
        data = _extract_json(llm_output)
    except Exception as e:
        logger.error("Failed to parse LLM output as JSON: %s", e)
        raise ResumeParsingError(f"LLM did not return valid JSON: {e}") from e

    try:
        resume = ResumeSchema.model_validate(data)
    except ValidationError as e:
        logger.error("Resume schema validation failed: %s", e)
        raise ResumeParsingError(f"Resume data failed validation: {e}") from e

    return resume