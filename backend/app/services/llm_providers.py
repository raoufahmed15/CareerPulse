import os
from pathlib import Path
from abc import ABC, abstractmethod

from dotenv import load_dotenv


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_FILE)


class LLMProvider(ABC):
    """Common interface every LLM backend must implement."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Send `prompt` to the LLM and return the raw text response.
        The caller (resume_parser.py) is responsible for turning
        that text into JSON and validating it.
        """
        raise NotImplementedError


# ============================================================
# Gemini
# ============================================================

class GeminiProvider(LLMProvider):

    def __init__(self, api_key: str = None, model_name: str = None):
        import google.generativeai as genai

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )

        genai.configure(api_key=self.api_key)

        self.model_name = model_name or os.getenv(
            "GEMINI_MODEL", "gemini-1.5-flash"
        )

        # response_mime_type="application/json" asks Gemini to
        # return JSON-only output (no markdown fences, no preamble).
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0,
            },
        )

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text


# ============================================================
# Groq
# ============================================================

class GroqProvider(LLMProvider):

    def __init__(self, api_key: str = None, model_name: str = None):
        from groq import Groq

        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )

        self.client = Groq(api_key=self.api_key)

        self.model_name = model_name or os.getenv(
            "GROQ_MODEL", "llama-3.3-70b-versatile"
        )

    def generate(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            # Groq's OpenAI-compatible JSON mode. The prompt must
            # still explicitly ask for JSON output (enforced below
            # in resume_parser.py's prompt template).
            response_format={"type": "json_object"},
            temperature=0,
        )
        return completion.choices[0].message.content


# ============================================================
# Factory
# ============================================================

_PROVIDERS = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


def get_llm_provider() -> LLMProvider:
    """
    Read LLM_PROVIDER from the environment and instantiate the
    matching provider. Defaults to "gemini".
    """

    provider_name = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    provider_cls = _PROVIDERS.get(provider_name)

    if provider_cls is None:
        raise RuntimeError(
            f"Unknown LLM_PROVIDER '{provider_name}'. "
            f"Supported values: {', '.join(_PROVIDERS)}"
        )

    return provider_cls()