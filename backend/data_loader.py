import sqlite3
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "app.db"


def load_masters_from_database():
    """
    Loads masters from app.db if it exists.
    Falls back to test data if database is missing or empty.
    """

    if not DB_PATH.exists():
        return get_fallback_masters()

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
        SELECT
            masters.id,
            masters.name AS program_name,
            masters.official_url,
            masters.summary,
            masters.city,
            universities.name AS university_name
        FROM masters
        LEFT JOIN universities
            ON masters.university_id = universities.id
        """

        rows = cursor.execute(query).fetchall()
        conn.close()

        masters = [dict(row) for row in rows]

        if not masters:
            return get_fallback_masters()

        return masters

    except Exception as e:
        print("Database loading error:", e)
        return get_fallback_masters()


def get_fallback_masters():
    """
    Temporary data so Lovable connection can be tested even before app.db is ready.
    """
    return [
        {
            "id": 1,
            "program_name": "MSc in Finance",
            "university_name": "Nova SBE",
            "city": "Carcavelos",
            "official_url": "https://www.novasbe.unl.pt/",
            "summary": "Master in Finance taught in English. Strong fit for students interested in banking, investment, consulting, financial analysis, and international careers. Competitive admissions and high tuition."
        },
        {
            "id": 2,
            "program_name": "MSc in Management",
            "university_name": "Católica Lisbon",
            "city": "Lisbon",
            "official_url": "https://clsbe.lisboa.ucp.pt/",
            "summary": "Master in Management taught in English. Good fit for students interested in consulting, strategy, marketing, entrepreneurship, and general management careers."
        },
        {
            "id": 3,
            "program_name": "MSc in Business Analytics",
            "university_name": "Nova SBE",
            "city": "Carcavelos",
            "official_url": "https://www.novasbe.unl.pt/",
            "summary": "Master focused on analytics, data, management, business intelligence, statistics, and decision-making. Strong fit for students with quantitative interests."
        }
    ]