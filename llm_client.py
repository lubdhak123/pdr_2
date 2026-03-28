import os
import re

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "mistral")


_TOKENS_BY_TYPE: dict[str, int] = {
    "LOOKUP":          80,
    "EXPLANATION":    380,
    "COMPARISON":     420,
    "SCENARIO":       380,
    "DECISION_LETTER": 500,
    "RISK_ASSESSMENT": 100,
    "AGGREGATE":       120,
    "UNKNOWN":          60,
}



def _looks_like_grounding_failure(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "need access to a database",
            "don't have that ability",
            "do not have that ability",
            "i don't have access",
            "i do not have access",
            "hypothetical data",
            "assuming the following data",
        )
    )


def _compact_response(text: str) -> str:
    cleaned_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[\-\*\+\d\.\)\s]+", "", line)
        cleaned_lines.append(line)

    compact = " ".join(cleaned_lines)
    compact = re.sub(r"\s+", " ", compact).strip()
    return compact or "Insufficient data."


def _generate(system_prompt: str, user_prompt: str, num_predict: int = 60) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": num_predict,
            },
        },
        timeout=120,
    )

    response.raise_for_status()
    return response.json()["response"]


def call_ollama(system_prompt: str, user_prompt: str, query_type: str = "LOOKUP") -> str:
    tokens = _TOKENS_BY_TYPE.get(query_type, 80)

    response_text = _generate(system_prompt, user_prompt, num_predict=tokens)

    if _looks_like_grounding_failure(response_text) and "CONTEXT:" in user_prompt:
        retry_system = (
            system_prompt
            + "\nYou already have all required facts in the USER prompt CONTEXT block. "
            + "Do NOT say you lack database access. Do NOT invent or simulate data."
        )
        response_text = _generate(retry_system, user_prompt, num_predict=tokens)

    # Multi-paragraph query types: return raw text (formatter handles layout)
    if query_type in ("EXPLANATION", "COMPARISON", "DECISION_LETTER", "SCENARIO"):
        return response_text.strip()

    return _compact_response(response_text)
