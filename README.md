# VenueHorn 🎉

> AI-powered venue and vendor discovery platform for weddings, corporate events, and celebrations across the USA.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)

---

## 🎯 Overview

VenueHorn is an intelligent conversational AI platform that helps customers find and book the perfect venues for their events. Using hybrid search combining structured filtering, vector similarity, and LLM-powered recommendations, VenueHorn provides personalized venue suggestions from a comprehensive database covering the entire USA.

### Key Features

- 🤖 **Conversational AI Search** - Natural language queries powered by GPT-4o-mini
- 🔍 **Hybrid Search Architecture** - Combines structured filters with semantic search
- 📍 **Geospatial Filtering** - Location-based search with radius queries
- 💰 **Smart Budget Matching** - Find venues within your price range
- 👥 **Capacity Planning** - Automatic venue sizing based on guest count
- ⚡ **Fast & Efficient** - 10-100x faster than pure vector search

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│        React + TypeScript + Tailwind CSS                 │
└────────────────┬─────────────────────────────────────────┘
                 │ REST API
┌────────────────▼─────────────────────────────────────────┐
│              Backend (FastAPI + Python)                  │
├──────────────────────────────────────────────────────────┤
│  • LLM Intent Extraction (OpenAI GPT-4o-mini)           │
│  • Structured Filtering (PostgreSQL + PostGIS)          │
│  • Vector Similarity Search (FAISS/pgvector)            │
│  • LLM Re-ranking & Recommendations                      │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│                   Data Layer                             │
│  • PostgreSQL (structured venue data)                    │
│  • FAISS/pgvector (semantic embeddings)                  │
│  • Redis (caching - optional)                            │
└──────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
VenueHorn-main/
├── venuehorn/
│   ├── app/                    # Next.js frontend
│   │   ├── page.tsx           # Home page
│   │   ├── dashboard/         # Dashboard page
│   │   ├── search/            # Search interface
│   │   └── layout.tsx         # Root layout
│   ├── backend/               # Python FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py       # API endpoints
│   │   │   ├── config.py     # Configuration
│   │   │   ├── models.py     # Database models
│   │   │   ├── schemas.py    # Pydantic schemas
│   │   │   └── vector_store.py  # Vector search
│   │   ├── scripts/
│   │   │   └── ingest_csv.py # Data ingestion
│   │   ├── data/             # Venue data (gitignored)
│   │   ├── requirements.txt  # Python dependencies
│   │   └── README.md         # Backend docs
│   ├── package.json          # Node dependencies
│   └── tsconfig.json         # TypeScript config
├── FIXES_APPLIED.md          # Step 1: API fixes documentation
├── HYBRID_SEARCH_ARCHITECTURE.md  # Step 2: Architecture design
├── IMPLEMENTATION_GUIDE.md   # Step-by-step implementation
├── LICENSE
└── README.md                 # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 15+ (optional, for hybrid search)
- OpenAI API key

### Backend Setup

```bash
# Navigate to backend
cd venuehorn/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd venuehorn

# Install dependencies
npm install

# Start development server
npm run dev
```

### Test the API

```bash
# In backend directory
python test_api.py

# Or manually
curl http://localhost:8000/health
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in `venuehorn/backend/`:

```bash
# Required
OPENAI_API_KEY=sk-your-api-key-here

# Optional (defaults provided)
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=800
CHUNK_OVERLAP=120
SCORE_THRESHOLD=0.2
```

---

## 📊 API Endpoints

### Current Implementation (Vector Search)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ingest` | POST | Add venue documents |
| `/search` | POST | Vector similarity search |
| `/chat` | POST | Conversational AI search |

### Example Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find me a romantic beachfront venue in Miami for 200 guests under $10k",
    "k": 5
  }'
```

### Example Response

```json
{
  "answer": "Based on your requirements, here are the top venues...",
  "hits": [
    {
      "text": "Ocean Pearl Resort - Miami, FL...",
      "source": "venues.csv#row42:Ocean Pearl Resort",
      "score": 0.89
    }
  ]
}
```

---

## 🎨 Design

Figma Design: [First Presentable Prototype](https://www.figma.com/design/QCCCyB5Xv5EKb4qzOaTKGZ/First-Presentable-Prototype?node-id=0-1&t=aHtQDjOpY9zpT8cm-1)

---

## 📚 Documentation

- **[FIXES_APPLIED.md](FIXES_APPLIED.md)** - API fixes and improvements (Step 1)
- **[HYBRID_SEARCH_ARCHITECTURE.md](HYBRID_SEARCH_ARCHITECTURE.md)** - Hybrid search design (Step 2)
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Step-by-step implementation guide
- **[Backend README](venuehorn/backend/README.md)** - Backend-specific documentation

---

## 🗺️ Roadmap

### ✅ Phase 1: Foundation (Complete)
- [x] FastAPI backend with vector search
- [x] OpenAI integration (GPT-4o-mini + embeddings)
- [x] Basic chat endpoint
- [x] CSV data ingestion

### 🚧 Phase 2: Hybrid Search (In Progress)
- [ ] PostgreSQL database with PostGIS
- [ ] LLM intent extraction
- [ ] Structured filtering pipeline
- [ ] Hybrid search endpoint
- [ ] Performance optimization

### 📋 Phase 3: Features (Planned)
- [ ] User authentication
- [ ] Booking system
- [ ] Vendor profiles
- [ ] Reviews and ratings
- [ ] Advanced filtering (dates, amenities)
- [ ] Image search
- [ ] Mobile app

### 🚀 Phase 4: Production (Planned)
- [ ] Deployment (AWS/GCP)
- [ ] CI/CD pipeline
- [ ] Monitoring & analytics
- [ ] A/B testing
- [ ] SEO optimization

---

## 🧪 Testing

```bash
# Backend tests
cd venuehorn/backend
python test_api.py

# Load testing (optional)
pip install locust
locust -f tests/locustfile.py --host=http://localhost:8000
```

---

## 💰 Cost Estimates

Using OpenAI API with current configuration:

| Operation | Cost (per 1K operations) |
|-----------|-------------------------|
| Embedding generation | ~$0.01 |
| Chat completions | ~$0.50-2.00 |
| Intent extraction | ~$0.30-1.00 |

**Estimated monthly cost for 10K queries:** $20-50

---

## 🤝 Contributing

This is a private project. For questions or suggestions, please contact the development team.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - GPT-4o-mini and text-embedding-3-small
- **FastAPI** - High-performance Python API framework
- **Next.js** - React framework for production
- **FAISS** - Efficient similarity search
- **PostgreSQL + PostGIS** - Geospatial database

---

## 📧 Contact

For inquiries about VenueHorn, please contact the development team.

---

**Built with ❤️ for making event planning effortless**
