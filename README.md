# VenueHorn

Venue and vendor discovery for events, powered by conversational AI.

## Stack

- **Backend**: FastAPI, FAISS, OpenAI
- **Frontend**: Next.js 14 (TypeScript)

## Getting started

### Backend

```bash
cd venuehorn/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Ingest venues

```bash
python3 scripts/ingest_csv.py "data/Sample Test Venues_Vendors - Venues.csv"
```

### Frontend

```bash
cd venuehorn
npm install && npm run dev
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/status` | GET | Index stats |
| `/ingest` | POST | Add venue documents |
| `/search` | POST | Vector similarity search |
| `/chat` | POST | Conversational AI with session memory |

### Chat example

```bash
# Start a conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "wedding venue in Miami for 200 guests"}'

# Follow up using the returned conversation_id
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "do any of those have outdoor space?", "conversation_id": "<id>"}'
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | required | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed origins |
| `ENVIRONMENT` | `development` | Runtime environment |

## Design

Figma: https://www.figma.com/design/QCCCyB5Xv5EKb4qzOaTKGZ/First-Presentable-Prototype

## License

MIT
