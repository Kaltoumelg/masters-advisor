# src/nova_scraper.py

from typing import List, Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .http_client import fetch_html


def find_nova_master_overviews(base_url: str) -> List[str]:
    """
    Given https://www.novasbe.unl.pt/en/programs/masters,
    return all URLs that look like /en/programs/masters/*/overview.
    """
    html = fetch_html(base_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base_url, href)
        lower = full.lower()
        if "/en/programs/masters/" in lower and lower.rstrip("/").endswith("/overview"):
            urls.add(full)

    return sorted(urls)


def collect_nova_program_tabs(overview_url: str) -> Dict[str, str]:
    """
    For a specific master's program, starting from its overview URL,
    read the left-hand nav (Overview, Study Abroad, Fees, Program, etc.)
    and fetch each tab's text. Return {purpose: text}.
    """
    html = fetch_html(overview_url)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")

    # get overview page text
    pages = {"overview": soup.get_text(separator="\n", strip=True)}

    # collect left menu links
    nav_links = []
    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").strip().lower()
        href = a["href"]
        full = urljoin(overview_url, href)

        # crude filter: nav items we care about
        if text in {
            "overview",
            "study abroad",
            "fees",
            "careers",
            "program",
            "apply",
            "scholarships & funding",
            "student advising",
        }:
            nav_links.append((text, full))

    # fetch each distinct nav page
    for text, url in nav_links:
        if text in pages:
            continue
        h = fetch_html(url)
        if not h:
            continue
        s = BeautifulSoup(h, "html.parser")
        pages[text] = s.get_text(separator="\n", strip=True)

    return pages