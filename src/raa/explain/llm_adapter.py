"""Local-only language generation for user-requested prediction reports."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:1.5b"
REPORT_TIMEOUT_SECONDS = 45.0
PROHIBITED_REPORT_PHRASES = (
    "you have",
    "confirmed cancer",
    "diagnosed with",
    "treatment",
    "recommend",
    "should",
    "must",
    "consult",
    "doctor",
    "seek medical",
    "emergency",
    "urgent",
)


class LLMUnavailableError(RuntimeError):
    """Raised if local report text cannot be generated safely."""


@dataclass(frozen=True)
class LocalReportNarrative:
    """Short model-generated paragraph stored inside a deterministic report."""

    text: str


def configured_model() -> str:
    """Return the installed local model name; remote endpoints cannot be configured."""
    return os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def generate_prediction_narrative(
    facts: dict[str, object], *, timeout: float = REPORT_TIMEOUT_SECONDS
) -> LocalReportNarrative:
    """Generate 2-3 report sentences from structured result facts using local Ollama."""
    model = configured_model()
    expected_output = str(facts.get("model_output", "")).casefold()
    expected_route = str(facts.get("route", "")).casefold()
    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 180},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Write a short, plain-language paragraph for a software result report. "
                    "Use only the supplied facts. Do not diagnose, recommend actions, change "
                    "the model output, or add medical claims. The output is a mammographic "
                    "mass-label estimate, not a person's diagnosis."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Summarize these facts in 2 or 3 sentences. Preserve the exact model output "
                    "and route. State that health details outside the mammogram fields are report "
                    "context only. Do not add advice or new numbers. Facts: "
                    + json.dumps(facts, ensure_ascii=True, sort_keys=True)
                ),
            },
        ],
    }
    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = re.sub(r"\s+", " ", body["message"]["content"]).strip()
        normalized = text.casefold()
        if (
            not text
            or len(text) > 900
            or not expected_output
            or not expected_route
            or expected_output not in normalized
            or expected_route not in normalized
            or any(phrase in normalized for phrase in PROHIBITED_REPORT_PHRASES)
        ):
            raise LLMUnavailableError("The local model returned an unusable report paragraph.")
        return LocalReportNarrative(text=text)
    except LLMUnavailableError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, TypeError) as error:
        raise LLMUnavailableError(
            "The local Ollama model could not generate the report paragraph."
        ) from error
