# src/summarizer.py

from typing import Dict
from .llm_client import call_llm


def summarize_program_texts(pages: Dict[str, str]) -> str:
    """
    pages: mapping from section name ('overview', 'fees', 'program', ...) to text.
    """
    chunks = []
    for name, text in pages.items():
        chunks.append(f"=== {name.upper()} ===\n{text}")
    combined = "\n\n".join(chunks)

    system_prompt = (
        "You are helping a student understand a master's program. "
        "Write a single clear summary. Include: field, language, "
        "location, duration, admission requirements, application deadlines/status, "
        "tuition/fees (EU vs non-EU if available), scholarships/funding, "
        "program structure, exchange/study-abroad options, and notable features."
    )

    user_prompt = (
        "Here are sections from the official website for one master's program. "
        "Summarize them into one coherent description.\n\n"
        f"{combined[:12000]}"
    )

    return call_llm(system_prompt, user_prompt)