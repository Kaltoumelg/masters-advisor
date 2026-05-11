# src/ingest_uni_life.py
import json
import requests
from bs4 import BeautifulSoup

from .db import SessionLocal
from .models import University, UniversityLife
from .llm_client import call_llm


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(t.strip() for t in soup.stripped_strings)
    return text


def summarize_life_text(university_name: str, text: str) -> str:
    system_prompt = (
        "You are extracting student life and non-academic offerings for a master's advising tool. "
        "The result will be used for matching student interests, so DO NOT over-summarize or drop "
        "specific names of clubs, associations, sports, or services."
    )
    user_prompt = (
        f"University: {university_name}\n\n"
        f"Student life / events extracted text:\n{text[:8000]}\n\n"
        "Produce a structured JSON-like text with these sections:\n"
        "1) clubs_and_associations: a bullet list of named clubs, associations, and student groups "
        "(keep the exact names where possible).\n"
        "2) sports_and_facilities: bullet list of sports, teams, and major facilities.\n"
        "3) support_services: bullet list of services (career office, mental health, housing, etc.).\n"
        "4) campus_culture: 3-5 bullets capturing themes about campus life and community.\n"
        "Do not remove specific club or service names; include them so they can be matched to "
        "student interests later."
    )
    return call_llm(system_prompt, user_prompt)


def ingest_university_life(universities_json_path: str = "data/universities.json"):
    with open(universities_json_path, "r", encoding="utf-8") as f:
        universities_cfg = json.load(f)

    session = SessionLocal()
    try:
        for cfg in universities_cfg:
            name = cfg["name"]
            events_url = cfg["events_index_url"]

            uni = session.query(University).filter_by(name=name).one_or_none()
            if not uni:
                print(f"Skipping {name}: not found in universities table")
                continue

            print(f"Fetching student life/events for {name}: {events_url}")

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                )
            }

            try:
                resp = requests.get(events_url, headers=headers, timeout=20)
                resp.raise_for_status()
            except Exception as e:
                print(f"Skipping {name} due to error fetching life/events: {e}")
                continue

            raw_text = extract_visible_text(resp.text)
            if not raw_text.strip():
                print(f"Skipping {name}: no visible text extracted from life/events page")
                continue

            summary = summarize_life_text(name, raw_text)

            existing = (
                session.query(UniversityLife)
                .filter_by(university_id=uni.id, source_url=events_url)
                .one_or_none()
            )
            if existing:
                existing.raw_text = raw_text
                existing.summary = summary
            else:
                obj = UniversityLife(
                    university_id=uni.id,
                    source_url=events_url,
                    raw_text=raw_text,
                    summary=summary,
                )
                session.add(obj)
            session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    ingest_university_life()