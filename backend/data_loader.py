import csv
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def find_file(filename: str) -> Path | None:
    possible_paths = [
        ROOT_DIR / filename,
        ROOT_DIR / "data" / filename,
        Path(__file__).resolve().parent / filename,
        Path(__file__).resolve().parent / "data" / filename,
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


def read_csv_file(filename: str):
    path = find_file(filename)

    if not path:
        print(f"WARNING: {filename} not found.")
        return []

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_all_matching_data():
    masters = read_csv_file("master_programs.csv")
    university_life = read_csv_file("university_life.csv")
    university_overviews = read_csv_file("university_overviews.csv")

    life_by_university = {
        str(row.get("university_id", "")): row
        for row in university_life
    }

    overview_by_university = {
        str(row.get("university_id", "")): row
        for row in university_overviews
    }

    enriched_masters = []

    for master in masters:
        university_id = str(master.get("university_id", ""))

        life = life_by_university.get(university_id, {})
        overview = overview_by_university.get(university_id, {})

        enriched_masters.append({
            "id": master.get("id", ""),
            "university_id": university_id,
            "program_name": master.get("name", "Unknown program"),
            "official_url": master.get("official_url", ""),
            "program_summary": master.get("summary", ""),
            "city": master.get("city", ""),
            "last_fetched_at": master.get("last_fetched_at", ""),
            "university_life_summary": life.get("summary", ""),
            "university_overview_summary": overview.get("summary", ""),
            "university_source_url": overview.get("source_url", "") or life.get("source_url", ""),
        })

    return enriched_masters