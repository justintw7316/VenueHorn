# Backend

FastAPI service for venue search and conversational AI.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

## Ingest data

```bash
python3 scripts/ingest_csv.py "data/Sample Test Venues_Vendors - Venues.csv"
```

Or run the enhanced pipeline with geocoding and validation:

```bash
python3 scripts/ingest_venues_enhanced.py "data/Sample Test Venues_Vendors - Venues.csv"
```

## Endpoints

```
GET  /health    liveness probe
GET  /status    index stats (chunk count, sources)
POST /ingest    add venue documents to the vector index
POST /search    raw vector similarity search
POST /chat      conversational AI with session memory
```

## Configuration

See `.env.example` for all available settings. Required: `OPENAI_API_KEY`.

## Data

Place CSV files in `data/`. The directory is gitignored. The ingestion scripts write the FAISS index, metadata, and geocoding cache to `data/` as well.

## Tests

```bash
python3 test_api.py        # integration tests (requires running server)
python3 test_ingestion.py  # unit tests for data validation
```
