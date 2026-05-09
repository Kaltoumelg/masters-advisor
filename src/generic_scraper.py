# src/generic_scraper.py

from __future__ import annotations
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .http_client import fetch_html

# Only keep masters related to these themes
DOMAIN_HINTS = [
    "economics",
    "economic",
    "business",
    "management",
    "finance",
    "financial",
    "accounting",
    "analytics",
    "data analytics",
]

MASTER_HINTS = [
    "master",
    "masters",
    "msc",
    "m.sc",
    "m sc",
    "degree",
    "master of science",
    "masters of science",
]

SECTION_HINTS = [
    "overview",
    "structure",
    "curriculum",
    "program",
    "programme",
    "fees",
    "tuition",
    "scholarship",
    "funding",
    "admission",
    "apply",
    "careers",
    "outcomes",
    "study abroad",
    "mobility",
]


def _same_domain(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return pa.netloc == pb.netloc


def find_program_pages(masters_index_url: str) -> List[str]:
    """
    Generic logic:
    - Fetch a masters index page.
    - Return URLs that look like individual master programme pages
      AND whose URL or link text suggests economics/business/finance areas.
    """
    html = fetch_html(masters_index_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    base = masters_index_url
    candidates: Set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base, href)
        text = (a.get_text() or "").strip().lower()
        lower = full.lower()

        if not _same_domain(base, full):
            continue

        # must be a master's program link
        if not any(h in lower or h in text for h in MASTER_HINTS):
            continue

        # must be related to econ/business/finance/etc.
        if not any(d in lower or d in text for d in DOMAIN_HINTS):
            continue

        # avoid obvious generic pages
        if any(x in lower for x in ["apply", "admission", "eligibility", "events"]):
            continue

        candidates.add(full)

    return sorted(candidates)


def collect_program_sections(program_url: str) -> Dict[str, str]:
    """
    For one programme:
    - Fetch main programme page (section 'main').
    - Find subpages under same URL prefix with section-like hints.
    """
    html = fetch_html(program_url)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    sections: Dict[str, str] = {}

    sections["main"] = soup.get_text(separator="\n", strip=True)

    parsed = urlparse(program_url)
    prefix = parsed.path.rstrip("/")
    base = program_url

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base, href)
        text = (a.get_text() or "").strip().lower()
        lower = full.lower()

        if not _same_domain(base, full):
            continue

        if not urlparse(full).path.startswith(prefix):
            continue

        if full.rstrip("/") == program_url.rstrip("/"):
            continue

        if not any(h in lower or h in text for h in SECTION_HINTS):
            continue

        section_key = text if text else urlparse(full).path.split("/")[-1]
        if section_key in sections:
            continue

        h2 = fetch_html(full)
        if not h2:
            continue
        s2 = BeautifulSoup(h2, "html.parser")
        sections[section_key] = s2.get_text(separator="\n", strip=True)

    return sections