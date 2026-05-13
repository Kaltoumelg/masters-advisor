# GradMatch — AI‑Powered Master’s Programme Advisor

> **Your background. Your goals. Your best‑fit master’s.**

GradMatch is a web tool that helps prospective students in Portugal discover, compare, and apply to master’s programmes in Economics, Business, Finance, and Data‑related fields. It combines a structured programme database with an AI‑driven matching engine that evaluates each student’s profile (CV, grades, goals, and preferences) and returns three personalised, ranked recommendations with fit scores, admission likelihood, and concrete next‑step advice.

---

## How the System Works

GradMatch has two main parts:

1. **Offline ingestion pipeline** – scrapes university websites, summarises content with a local LLM, and exports CSV files.
2. **Online recommendation API** – takes a student’s CV + quiz answers and uses Gemini to rank programmes in real time.

### Phase 1 — Offline ingestion (single entrypoint)

The ingestion pipeline is responsible for building and refreshing the programme knowledge base. It is driven by `main_ingest.py`, which acts as a single entrypoint and runs **all three** ingestion steps in sequence:

1. **Database initialisation**

   `init_db()` creates all tables and ensures every university defined in `data/universities.json` exists in the `universities` table with the correct key, name, base URL, and city.

2. **Master’s programmes ingestion**

   For each configured university key in `UNIVERSITIES`, `ingest_university_masters(uni_key)`:

   - Visits the master’s index page and discovers candidate programme URLs using `src/generic_scraper.py`.
   - For each programme URL, collects content from the main page plus relevant sub‑tabs (admissions, fees, curriculum, etc.) using `collect_program_sections`.
   - Uses `src/summarizer.py` to call a local Ollama model (Llama 3) and produce a structured programme summary.
   - Applies a staleness check (`MASTERS_STALE_DAYS`) and skips programmes that have been fetched recently.
   - Stores results in `masters.db` as `MasterProgram` rows and contributes to `master_programs.csv`.

3. **University homepage ingestion**

   After all master’s programmes are processed, `main_ingest.py` calls `src/ingest_uni_homepages.ingest_university_homepages()`, which:

   - Reads `data/universities.json` to get each university’s homepage URL.
   - Fetches and cleans the visible text (removing script/style/no‑script).
   - Calls the local LLM (`call_llm` via `llm_client.py`) with a prompt tuned to produce a concise, student‑facing overview (reputation, campus feel, international environment, and master’s‑relevant aspects).
   - Saves or updates `UniversityOverview` rows and exports `university_overviews.csv`.

4. **Student life ingestion**

   Finally, `main_ingest.py` calls `src/ingest_uni_life.ingest_university_life()`, which:

   - Uses `data/universities.json` to locate each university’s student life / events index URL.
   - Extracts visible text and asks the LLM for a structured breakdown:
     - clubs_and_associations
     - sports_and_facilities
     - support_services
     - campus_culture
   - Keeps exact names of clubs and services to power interest‑based matching.
   - Saves or updates `UniversityLife` rows and exports `university_life.csv`.

Running **one command**:

```bash
python main_ingest.py
```

initialises the database and fully refreshes the three CSV files the backend uses at runtime.

### Phase 2 — Real‑time recommendation (backend)

The backend exposes a FastAPI service that the frontend calls to obtain recommendations:

1. A student uploads a CV (PDF) and fills out a short quiz.
2. The API extracts plain text from the CV using PyMuPDF (`backend/cv_parser.py`).
3. It loads and joins `master_programs.csv`, `university_overviews.csv`, and `university_life.csv` into enriched programme records (`backend/data_loader.py`).
4. A deterministic pre‑filter removes clearly incompatible options (e.g., language mismatch, way over budget) and computes baseline scores (`backend/scoring.py`).
5. The student profile and filtered programme list are sent to Gemini via `backend/recommender.py` to:
   - Rank the remaining programmes.
   - Generate explanations and improvement tips.
6. The API returns exactly three recommended programmes with:
   - Fit score
   - Admission difficulty estimate
   - Natural‑language reasoning

In production, the backend only depends on Gemini; Ollama is used **only** during offline ingestion.


## Setup & Running

### Prerequisites

- Python 3.11+
- Local installation of [Ollama](https://ollama.com/) (for ingestion)
- Gemini API key (for the recommendation backend)

Using a virtual environment is recommended.

### 1. Install dependencies

From the project root:

```bash
# Ingestion pipeline
pip install -r requirements.txt

# Backend API
pip install -r backend/requirements.txt
```

### 2. Configure and start Ollama (ingestion only)

Pull and serve the model used by the ingestion pipeline:

```bash
ollama pull llama3
ollama serve   # keep this running while ingestion runs
```

If your config uses a different model/tag (e.g. `llama3:8b`), pull that instead.

### 3. Run the ingestion pipeline (all three steps)

From the project root:

```bash
python main_ingest.py
```

This will:

- Initialise the database.
- Ingest all master’s programmes for every configured university.
- Ingest all university homepages.
- Ingest all student life / events pages.
- Regenerate `master_programs.csv`, `university_overviews.csv`, and `university_life.csv`.

You can re‑run this command periodically; master’s programmes newer than `MASTERS_STALE_DAYS` (in `src/config.py`) will be skipped to save time.

### 4. Configure the backend

Create a `.env` file inside `backend/` (or set environment variables in your hosting platform):

```text
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash   # optional override; this is the default
```

Ensure the three CSVs generated by ingestion are present in the project root:

- `master_programs.csv`
- `university_overviews.csv`
- `university_life.csv`

### 5. Run the backend locally

```bash
cd backend
uvicorn app:app --reload
```

By default, the API will be at `http://localhost:8000`.

Key endpoints:

| Method | Path         | Description                                                    |
|--------|--------------|----------------------------------------------------------------|
| GET    | `/`          | Simple root/health check                                       |
| GET    | `/health`    | Health check (JSON)                                            |
| GET    | `/version`   | Returns model/version and expected output fields               |
| POST   | `/recommend` | Main endpoint — accepts CV + quiz answers, returns 3 matches  |

---

## Adding Universities

To add a new university:

1. Append a new object to `data/universities.json`:

   ```json
   {
     "name": "Example University",
     "city": "Example City",
     "homepage_url": "https://example.edu",
     "masters_index_url": "https://example.edu/masters",
     "events_index_url": "https://example.edu/student-life"
   }
   ```

2. Run the ingestion pipeline again:

   ```bash
   python main_ingest.py
   ```

The generic scraper and the homepage/life ingestors will automatically process the new university without additional code changes.

---

## Tech Stack

| Component         | Technology                                      |
|------------------|--------------------------------------------------|
| Frontend         | Lovable (React + Tailwind)                       |
| Backend API      | Python 3.11, FastAPI, Uvicorn                    |
| Scraping         | Requests, BeautifulSoup                          |
| Ingestion LLM    | Ollama (Llama 3) — local, used offline           |
| Matching LLM     | Google Gemini 2.5 Flash — used by the backend    |
| CV Parsing       | PyMuPDF (fitz)                                   |
| Storage (offline)| SQLite (`masters.db`)                            |
| Storage (runtime)| CSVs (`master_programs.csv`, `university_*.csv`) |

---

## Notes

- **No student data is stored.** CV text is processed in memory for each request and not persisted.
- **Ollama is only required for ingestion.** The production backend (e.g., on Render) only needs access to the CSVs and a Gemini API key.
- **The CSV files are the runtime knowledge base.** SQLite is an internal detail of the ingestion pipeline and is not used by the online API.