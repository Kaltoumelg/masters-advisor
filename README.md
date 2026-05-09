# Masters Advisor – AI-driven Masters & Events Aggregator

## Overview

This project aggregates master's programmes and events from a small set of Portuguese universities and uses a local LLM (via Ollama) to extract structured information.

Stack:
- Python
- SQLite
- Ollama (e.g., model `llama3`)

## Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install and run Ollama, and pull a model:

```bash
ollama pull llama3
ollama run llama3  # to test it works
```

3. Initialize the database:

```bash
python scripts/init_db.py
```

4. Test an LLM extraction call:

```bash
python scripts/demo_extract_one.py
```

Later you will:
- Run ingestion scripts to fetch real pages and populate `masters` and `events`.
- Build a web UI on top of the SQLite database.