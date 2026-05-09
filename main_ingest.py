# main_ingest.py

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy import select

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import UNIVERSITIES, MASTERS_STALE_DAYS
from src.db import Base, engine, SessionLocal
from src.models import University, MasterProgram
from src.generic_scraper import find_program_pages, collect_program_sections
from src.summarizer import summarize_program_texts
from src.http_client import fetch_html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        for cfg in UNIVERSITIES.values():
            uni = session.execute(
                select(University).where(University.key == cfg.key)
            ).scalar_one_or_none()
            if not uni:
                uni = University(
                    key=cfg.key,
                    name=cfg.name,
                    base_url=cfg.masters_index_url,
                    city=cfg.city,
                )
                session.add(uni)
        session.commit()
    finally:
        session.close()


def ingest_university_masters(uni_key: str):
    cfg = UNIVERSITIES[uni_key]
    logger.info("Ingesting masters for %s from %s", cfg.name, cfg.masters_index_url)

    session = SessionLocal()
    try:
        uni = session.execute(
            select(University).where(University.key == cfg.key)
        ).scalar_one_or_none()
    finally:
        session.close()

    if not uni:
        logger.error("University %s not found in DB", cfg.name)
        return

    # 1) From masters index page, find ECON/BUS/FIN programme URLs
    program_urls = find_program_pages(cfg.masters_index_url)
    logger.info(
        "Found %d candidate ECON/BUS/FIN programme URLs for %s",
        len(program_urls),
        cfg.name,
    )

    session = SessionLocal()
    try:
        for url in program_urls:
            logger.info("Processing program: %s", url)

            existing = session.execute(
                select(MasterProgram).where(MasterProgram.official_url == url)
            ).scalar_one_or_none()

            if existing and existing.last_fetched_at:
                if existing.last_fetched_at > datetime.utcnow() - timedelta(
                    days=MASTERS_STALE_DAYS
                ):
                    logger.info("Skipping fresh program: %s", url)
                    continue

            # 2) Collect sections (main page + subpages under same prefix)
            sections = collect_program_sections(url)
            if not sections:
                logger.warning("No sections collected for %s", url)
                continue

            # 3) Summarize with LLM
            summary = summarize_program_texts(sections)
            if not summary:
                logger.warning("No summary produced for %s", url)
                continue

            # 4) Derive programme title from <title>
            title = url
            html = fetch_html(url)
            if html:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(html, "html.parser")
                t = soup.find("title")
                if t:
                    title = t.get_text(strip=True)

            if existing:
                existing.name = title
                existing.summary = summary
                existing.city = uni.city
            else:
                mp = MasterProgram(
                    university_id=uni.id,
                    name=title,
                    official_url=url,
                    summary=summary,
                    city=uni.city,
                )
                session.add(mp)

            session.commit()
            logger.info("Saved program: %s", title)
    finally:
        session.close()


def main():
    init_db()

    target_names = {
        "University of Minho - EEG",
    }

    for key, cfg in UNIVERSITIES.items():
        if cfg.name not in target_names:
            continue
        ingest_university_masters(key)

if __name__ == "__main__":
    main()