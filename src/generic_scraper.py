# src/generic_scraper.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from .http_client import fetch_html
from .llm_client import call_llm


# -------- Data models --------

@dataclass
class Program:
    university_name: str
    slug: str
    main_url: str
    subpages: Dict[str, str]  # e.g. {"fees": url, "program": url, ...}


# -------- Keyword config (generic, not Nova-specific) --------

MASTER_HINTS = [
    "master",
    "masters",
    "master of science",
    "masters of science",
    "msc",
    "2nd-cycle",
    "2nd cycle",
    "second cycle",
]

DOMAIN_HINTS = [
    "economics",
    "finance",
    "business",
    "management",
    "analytics",
    "data science",
]

EXCLUDE_SECTIONS = [
    "/research",
    "/faculty-research",
    "/news",
    "/events",
    "/blog",
    "/library",
    "/people",
    "/about",
    "/alumni",
]

BAD_SUFFIX_WORDS = [
    "fees",
    "fee",
    "tuition",
    "study-abroad",
    "mobility",
    "exchange",
    "career",
    "careers",
    "apply",
    "admission",
    "requirements",
    "scholarship",
]

SUBTAB_KEYWORDS = {
    "fees": ["fee", "tuition", "scholarship", "cost"],
    "program": ["program", "programme", "curriculum", "structure", "study-plan"],
    "study_abroad": ["study-abroad", "mobility", "exchange"],
    "careers": ["career", "employment", "prospect", "employability"],
    "admissions": ["apply", "admission", "application", "requirements"],
}


# -------- Small utilities --------

def _same_domain(a: str, b: str) -> bool:
    return urlparse(a).netloc == urlparse(b).netloc


def _path_prefix_allowed(path: str) -> bool:
    """Filter out obvious non-program sections."""
    lower = path.lower()
    for ex in EXCLUDE_SECTIONS:
        if lower.startswith(ex):
            return False
    return True


def _derive_program_key(url: str) -> Optional[str]:
    """
    Derive a program key from URL path.

    For Nova-like URLs:
      /en/programs/masters/law-management/how-to-apply -> programmes/masters/law-management
    All tabs under that prefix are the same program.

    For simpler patterns, falls back to last segment.
    """
    path = urlparse(url).path.rstrip("/")
    parts = [p for p in path.split("/") if p]

    if not parts:
        return None

    # Try to find "masters" segment and use the next part as slug
    if "masters" in parts:
        i = parts.index("masters")
        if i + 1 < len(parts):
            # program key is "masters/<slug>"
            return "masters/" + parts[i + 1]

    # Fallback: use the last segment as a key
    return parts[-1]


# -------- Step 1: collect candidates from masters_index_url --------

def collect_master_candidates(masters_index_url: str) -> Dict[str, List[Tuple[str, str, str]]]:
    html = fetch_html(masters_index_url)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    base = masters_index_url

    candidates: Dict[str, List[Tuple[str, str, str]]] = {}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base, href)

        if not _same_domain(base, full):
            continue

        path = urlparse(full).path
        if not _path_prefix_allowed(path):
            continue

        lower_url = full.lower()
        text = (a.get_text() or "").strip()
        lower_text = text.lower()

        if not any(h in lower_url or h in lower_text for h in MASTER_HINTS):
            continue
        if not any(d in lower_url or d in lower_text for d in DOMAIN_HINTS):
            continue

        key = _derive_program_key(full)
        if not key:
            continue

        context = lower_text
        candidates.setdefault(key, []).append((full, text, context))

    return candidates


# -------- Step 2: LLM-based main URL selection per slug --------

def choose_main_program_url_with_llm(
    university_name: str,
    slug: str,
    options: List[Tuple[str, str, str]],  # (url, anchor_text, context)
) -> str:
    """
    Use the LLM to pick ONE main overview page for this master's program.

    All options belong to the same program (same slug).
    """
    lines = []
    for i, (url, anchor, ctx) in enumerate(options, start=1):
        lines.append(f"{i}. URL: {url}\n   Anchor: {anchor}\n   Context: {ctx}")
    options_text = "\n\n".join(lines)

    system_prompt = (
        "You classify university website links for master's programs. "
        "All given links belong to the SAME master's program. "
        "Pick the ONE link that is the main overview/landing page "
        "for prospective students. Do NOT pick pages that are only about "
        "fees, admissions, careers, or study abroad unless there is no "
        "dedicated overview page."
    )

    user_prompt = (
        f"University: {university_name}\n"
        f"Program slug: {slug}\n\n"
        "Here are candidate links:\n\n"
        f"{options_text}\n\n"
        "Answer with ONLY the number of the best option (1, 2, 3, ...)."
    )

    raw = call_llm(system_prompt, user_prompt).strip()

    idx: Optional[int] = None
    for ch in raw:
        if ch.isdigit():
            idx = int(ch) - 1
            break

    if idx is None or not (0 <= idx < len(options)):
        return _fallback_choose_main_program_url(options)

    return options[idx][0]


def _fallback_choose_main_program_url(
    options: List[Tuple[str, str, str]]
) -> str:
    """
    Heuristic backup if LLM output is unusable.
    Prefer overview, then URLs without bad suffix words, then shortest path.
    """
    def score(url: str, anchor: str, ctx: str) -> Tuple[int, int]:
        lower = url.lower()
        path_len = len(urlparse(url).path)
        is_bad = any(w in lower for w in BAD_SUFFIX_WORDS)

        if "overview" in lower:
            return (0, path_len)
        if not is_bad:
            return (1, path_len)
        return (2, path_len)

    best_url = min(options, key=lambda t: score(t[0], t[1], t[2]))[0]
    return best_url


# -------- Step 3: from main URL to all sub-tabs for that master --------

def _program_prefix(main_url: str) -> str:
    """
    Compute prefix for all pages of this master.
    Example: /en/programs/masters/business-analytics/overview
             -> /en/programs/masters/business-analytics
    """
    path = urlparse(main_url).path.rstrip("/")
    parts = [p for p in path.split("/") if p]

    if parts and parts[-1] in {"overview", "program", "fees", "study-abroad"}:
        parts = parts[:-1]

    return "/" + "/".join(parts)


def extract_master_subtabs(main_program_url: str) -> Dict[str, str]:
    """
    Given the main master page, find sub-tabs (fees, program, etc.)
    belonging to the same program slug, and label them by type.

    Returns: {subtab_type: url}
    """
    html = fetch_html(main_program_url)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    base = main_program_url

    prefix = _program_prefix(main_program_url).lower()
    subtabs: Dict[str, str] = {}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base, href)

        path = urlparse(full).path.lower()
        text = (a.get_text() or "").strip().lower()

        # stay under same master prefix
        if not path.startswith(prefix):
            continue

        # classify into subtab type
        for subtab, keywords in SUBTAB_KEYWORDS.items():
            if any(k in path or k in text for k in keywords):
                subtabs.setdefault(subtab, full)
                break

    return subtabs


# -------- Public entry: scrape masters for one university (if you need it) --------

def scrape_university_masters(university: Dict) -> List[Program]:
    """
    university: one entry from universities.json:
      {
        "name": "...",
        "masters_index_url": "...",
        ...
      }

    Returns a list of Program objects (one per master).
    """
    masters_index_url = university["masters_index_url"]
    uni_name = university["name"]

    candidates_by_slug = collect_master_candidates(masters_index_url)
    programs: List[Program] = []

    for slug, options in candidates_by_slug.items():
        if not options:
            continue

        main_url = choose_main_program_url_with_llm(uni_name, slug, options)
        subtabs = extract_master_subtabs(main_url)

        programs.append(
            Program(
                university_name=uni_name,
                slug=slug,
                main_url=main_url,
                subpages=subtabs,
            )
        )

    return programs


# -------- Backwards-compatible API for main_ingest.py --------

def find_program_pages(masters_index_url: str) -> List[str]:
    uni_name = urlparse(masters_index_url).netloc
    candidates_by_key = collect_master_candidates(masters_index_url)
    canonical_urls: List[str] = []

    for key, options in candidates_by_key.items():
        if not options:
            continue
        main_url = choose_main_program_url_with_llm(uni_name, key, options)
        canonical_urls.append(main_url)

    return sorted(set(canonical_urls))


def _extract_visible_text(html: str) -> str:
    """Simple text extractor: remove script/style, return visible text."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    parts: List[str] = []
    for elem in soup.stripped_strings:
        parts.append(elem)

    return "\n".join(parts)


def collect_program_sections(main_url: str) -> Dict[str, str]:
    """
    Expected by main_ingest.py.

    Given ONE program URL (main/overview page),
    detect sub-tabs for the same master's program and
    return {section_name: text} for main + subpages.

    Section names:
      - 'overview' for the main page
      - keys from SUBTAB_KEYWORDS (e.g. 'fees', 'program', 'study_abroad', ...)
    """
    sections: Dict[str, str] = {}

    # main page
    main_html = fetch_html(main_url)
    if main_html:
        sections["overview"] = _extract_visible_text(main_html)

    # discover sub-tabs
    subpages = extract_master_subtabs(main_url)
    for name, url in subpages.items():
        html = fetch_html(url)
        if not html:
            continue
        sections[name] = _extract_visible_text(html)

    return sections