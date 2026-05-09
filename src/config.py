# src/config.py

from dataclasses import dataclass
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "app.db"
DB_URL = f"sqlite:///{DB_PATH}"

OLLAMA_URL = "http://localhost:11434/api/chat"
LLM_MODEL = "llama3"

MASTERS_STALE_DAYS = 30
EVENTS_STALE_DAYS = 1


@dataclass
class UniversityConfig:
    key: str
    name: str
    city: str
    homepage_url: str
    masters_index_url: str
    events_index_url: str
    type: str  # "nova", "catolica", "iseg", "porto", "ulisboa", ...


def load_universities_config() -> dict[str, UniversityConfig]:
    with open(BASE_DIR / "data" / "universities.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    configs = {}
    for idx, item in enumerate(raw):
        name = item["name"]
        key = (
            name.lower()
            .replace(" ", "_")
            .replace("á", "a")
            .replace("ã", "a")
            .replace("é", "e")
        )
        # simple type mapping: you can refine or override if needed
        if "nova" in name.lower():
            uni_type = "nova"
        elif "católica" in name.lower() or "catolica" in name.lower():
            uni_type = "catolica"
        elif "iseg" in name.lower():
            uni_type = "iseg"
        elif "porto" in name.lower():
            uni_type = "porto"
        elif "lisbon" in name.lower() or "lisboa" in name.lower():
            uni_type = "ulisboa"
        else:
            uni_type = "generic"

        cfg = UniversityConfig(
            key=key,
            name=name,
            city=item.get("city", ""),
            homepage_url=item["homepage_url"],
            masters_index_url=item["masters_index_url"],
            events_index_url=item["events_index_url"],
            type=uni_type,
        )
        configs[key] = cfg
    return configs


UNIVERSITIES = load_universities_config()