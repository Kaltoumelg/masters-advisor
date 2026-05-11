# src/ingest_uni_homepages.py
import json
import requests
from bs4 import BeautifulSoup

from .db import SessionLocal
from .models import University, UniversityOverview
from .llm_client import call_llm  # same helper you use for masters summaries


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(t.strip() for t in soup.stripped_strings)
    return text


def summarize_homepage_text(university_name: str, text: str) -> str:
    system_prompt = (
        "You are writing a short, student-facing overview for a master's advising website. "
        "The tone should be clear, neutral and informative, aimed at someone considering applying "
        "for a master's at this university."
    )
    user_prompt = (
        f"University: {university_name}\n\n"
        f"Homepage extracted text:\n{text[:8000]}\n\n"
        "Write an overview (max 300 words) that covers:\n"
        "1) The university's academic reputation and strengths.\n"
        "2) International environment and language of campus (if mentioned).\n"
        "3) Campus location and feel.\n"
        "4) Any aspects that are especially relevant for master's students "
        "(career support, research focus, connections to industry).\n"
        "Avoid generic marketing fluff; be concrete and useful for a prospective master's student."
    )
    return call_llm(system_prompt, user_prompt)


def ingest_university_homepages(universities_json_path: str = "data/universities.json"):
    with open(universities_json_path, "r", encoding="utf-8") as f:
        universities_cfg = json.load(f)

    session = SessionLocal()
    try:
        for cfg in universities_cfg:
            name = cfg["name"]
            homepage_url = cfg["homepage_url"]

            uni = session.query(University).filter_by(name=name).one_or_none()
            if not uni:
                print(f"Skipping {name}: not found in universities table")
                continue

            print(f"Fetching homepage for {name}: {homepage_url}")

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                )
            }

            try:
                resp = requests.get(homepage_url, headers=headers, timeout=20)
                resp.raise_for_status()
            except Exception as e:
                print(f"Skipping {name} due to error fetching homepage: {e}")
                continue

            raw_text = extract_visible_text(resp.text)
            if not raw_text.strip():
                print(f"Skipping {name}: no visible text extracted from homepage")
                continue

            summary = summarize_homepage_text(name, raw_text)

            existing = (
                session.query(UniversityOverview)
                .filter_by(university_id=uni.id, source_url=homepage_url)
                .one_or_none()
            )
            if existing:
                existing.raw_text = raw_text
                existing.summary = summary
            else:
                obj = UniversityOverview(
                    university_id=uni.id,
                    source_url=homepage_url,
                    raw_text=raw_text,
                    summary=summary,
                )
                session.add(obj)
            session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    ingest_university_homepages()