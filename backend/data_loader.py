import csv
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

UNIVERSITY_ID_TO_NAME = {
    "1": "Nova SBE",
    "2": "ISCTE Business School",
    "3": "ISEG",
    "4": "FEP - University of Porto",
    "5": "University of Lisbon",
    "6": "University of Minho - EEG",
}


def find_file(filename: str) -> Path:
    paths = [
        ROOT_DIR / filename,
        ROOT_DIR / "data" / filename,
        Path(__file__).resolve().parent / filename,
        Path(__file__).resolve().parent / "data" / filename,
    ]

    for path in paths:
        if path.exists():
            return path

    raise FileNotFoundError(f"Could not find {filename}")


def read_csv(filename: str):
    path = find_file(filename)

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def clean_program_name(raw_name: str) -> str:
    if not raw_name:
        return "Unknown program"

    name = raw_name.strip()

    name = re.sub(r"\s*\|\s*.*$", "", name)
    name = re.sub(r"\s*-\s*Program Overview.*$", "", name, flags=re.I)
    name = re.sub(r"\s*Program Overview.*$", "", name, flags=re.I)
    name = re.sub(r"\s*NOVA SBE.*$", "", name, flags=re.I)
    name = re.sub(r"\s*Nova SBE.*$", "", name, flags=re.I)
    name = re.sub(r"\s*ISEG.*$", "", name, flags=re.I)
    name = re.sub(r"\s*ULisboa.*$", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip()

    return name


def load_all_matching_data():
    masters = read_csv("master_programs.csv")
    university_life = read_csv("university_life.csv")
    university_overviews = read_csv("university_overviews.csv")

    life_by_university = {
        str(row.get("university_id", "")): row
        for row in university_life
    }

    overview_by_university = {
        str(row.get("university_id", "")): row
        for row in university_overviews
    }

    enriched = []

    for master in masters:
        university_id = str(master.get("university_id", ""))
        life = life_by_university.get(university_id, {})
        overview = overview_by_university.get(university_id, {})

        university_name = (
            master.get("university_name")
            or overview.get("university_name")
            or overview.get("name")
            or UNIVERSITY_ID_TO_NAME.get(university_id, f"University ID {university_id}")
        )

        enriched.append({
            "id": master.get("id", ""),
            "university_id": university_id,
            "program_name_raw": master.get("name", ""),
            "program_name": clean_program_name(master.get("name", "")),
            "university": university_name,
            "official_url": master.get("official_url", ""),
            "city": master.get("city", ""),
            "program_summary": master.get("summary", ""),
            "university_life_summary": life.get("summary", ""),
            "university_overview_summary": overview.get("summary", ""),
        })

    return enriched