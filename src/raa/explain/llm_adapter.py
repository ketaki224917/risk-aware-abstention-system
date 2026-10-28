"""Local-only LLM status summary for the questionnaire intake.

The prompt is fixed and contains no user answers or model-derived cancer class.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:1.5b"
SUMMARY_TIMEOUT_SECONDS = 45.0
PROHIBITED_TERMS = (
    "cancer",
    "malignant",
    "benign",
    "diagnos",
    "medical",
    "doctor",
    "treatment",
    "screening",
    "recommend",
    "advice",
    "should",
    "likely",
    "probability",
    "risk score",
    "positive",
    "negative",
    "consult",
    "seek care",
    "contact",
    "professional",
    "specialist",
    "clinician",
    "physician",
    "provider",
    "referral",
    "follow-up",
    "urgent",
    "emergency",
)


class LLMUnavailableError(RuntimeError):
    """Raised when the local LLM is unavailable or returns unsafe/unusable text."""


@dataclass(frozen=True)
class LocalSummary:
    text: str
    model: str


def configured_model() -> str:
    """Return the local Ollama model name, without accepting a remote endpoint."""
    return os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _validate_summary(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    normalized = cleaned.casefold()
    has_review = "human review" in normalized
    no_prediction = any(
        phrase in normalized
        for phrase in (
            "no prediction",
            "no class estimate",
            "did not produce a class estimate",
            "did not make a prediction",
            "no class prediction",
        )
    )
    contains_prohibited_claim = any(term in normalized for term in PROHIBITED_TERMS)
    if (
        not cleaned
        or len(cleaned) > 600
        or not has_review
        or not no_prediction
        or contains_prohibited_claim
    ):
        raise LLMUnavailableError("The local model did not return a safe, status-only explanation.")
    return cleaned


def generate_intake_status_summary(*, timeout: float = SUMMARY_TIMEOUT_SECONDS) -> LocalSummary:
    """Ask the local Ollama model to explain the fixed abstention status only.

    Questionnaire answers, ages, symptoms, and model features are intentionally
    not accepted as arguments and are never included in the request.
    """
    model = configured_model()
    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 100},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write a brief status explanation for a nonclinical research software "
                    "report. Do not make or infer predictions. Do not give medical information, "
                    "advice, or recommendations."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Using only these fixed facts, write one or two short sentences: the "
                    "software returned Human Review because its current model cannot assess the "
                    "questionnaire inputs; no class estimate or prediction was produced. Do not "
                    "mention diseases, diagnoses, symptoms, clinical actions, or advice. Do not "
                    "add any other claims. The output must include the words Human Review and "
                    "that no prediction or class estimate was produced."
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
        text = body["message"]["content"]
        return LocalSummary(text=_validate_summary(text), model=model)
    except LLMUnavailableError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, TypeError) as error:
        raise LLMUnavailableError(
            "The local Ollama model could not be reached or returned an invalid response."
        ) from error
