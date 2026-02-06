# VenueHorn AI Search (FastAPI)

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
# Then edit .env and add your OpenAI API key
```

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

**Optional environment variables** (defaults are set in `app/config.py`):
- `OPENAI_MODEL=gpt-4o-mini` (default, recommended for production)
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small` (default)

Run the API:

```bash
uvicorn app.main:app --reload --port 8001
```

## Ingest a CSV file

```bash
cd backend
source .venv/bin/activate
python3 scripts/ingest_csv.py "data/Sample Test Venues_Vendors - Venues.csv"
```

## Testing

Run the test suite to verify everything is working:

```bash
# In one terminal, start the server:
uvicorn app.main:app --reload --port 8000

# In another terminal, run the tests:
python test_api.py
```

Or test manually with curl:

```bash
# Health check
curl http://localhost:8000/health

# Chat with the AI
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "I need a wedding venue for 200 guests in Miami", "k": 5}'
```

## Endpoints

- `GET /health` - Health check
- `POST /ingest` - Add venue documents to the vector database
  ```json
  {"documents": [{"text": "...", "source": "optional"}]}
  ```
- `POST /search` - Vector similarity search (returns raw chunks)
  ```json
  {"query": "...", "k": 6}
  ```
- `POST /chat` - Conversational AI search (returns AI-generated response)
  ```json
  {"query": "...", "k": 6}
  ```

## Notes

- Vector index and metadata are stored in `backend/data/`.
- `score_threshold` and chunk settings can be adjusted in `app/config.py`.
