# src/llm_client.py

import logging
from typing import List, Dict
import requests

from .config import OLLAMA_URL, LLM_MODEL

logger = logging.getLogger(__name__)


def call_llm(system_prompt: str, user_prompt: str, timeout: int = 120) -> str:
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]
    except Exception as e:
        logger.warning("LLM call failed: %s", e)
        return ""