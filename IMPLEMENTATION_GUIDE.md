# VenueHorn - Quick Implementation Guide

## Overview

This guide provides step-by-step instructions to implement the hybrid search architecture.

---

## Phase 1: Database Setup (Immediate)

### Install PostgreSQL with Extensions

```bash
# macOS
brew install postgresql@15 postgis

# Ubuntu
sudo apt-get install postgresql-15 postgresql-15-postgis-3

# Start PostgreSQL
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Ubuntu
```

### Install pgvector Extension

```bash
# Clone and install pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Or use Docker
docker run -d \
  --name venuehorn-db \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

### Create Database

```sql
-- Connect to PostgreSQL
psql postgres

-- Create database
CREATE DATABASE venuehorn;

-- Connect to database
\c venuehorn

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy text search

-- Verify
SELECT postgis_version();
SELECT vector_version();
```

---

## Phase 2: Migrate Data (CSV → PostgreSQL)

### Update requirements.txt

```bash
# Add to backend/requirements.txt
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.12.1
geoalchemy2==0.14.2
pandas==2.1.3
```

### Create Migration Script

```bash
# Install dependencies
pip install -r requirements.txt

# Create migration script
python scripts/migrate_csv_to_db.py
```

### Migration Script (create this file)

```python
# scripts/migrate_csv_to_db.py
import csv
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Base, Venue

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost/venuehorn"

async def migrate_csv(csv_path: str):
    """Migrate CSV data to PostgreSQL."""

    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Read CSV
    venues = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse capacity
            capacity_str = row.get('Total Number of Attendees', '')
            max_capacity = None
            if capacity_str:
                # Extract number from strings like "Up to 120"
                import re
                match = re.search(r'(\d+)', capacity_str.replace(',', ''))
                if match:
                    max_capacity = int(match.group(1))

            # Create venue object
            venue = Venue(
                name=row['Venue Name'] or 'Unknown',
                holding_company=row.get('Venue Holding Company'),
                brand=row.get('Venue Brand'),
                website=row.get('Venue Website'),
                description=row.get('Venue Description'),
                venue_type=row.get('Venue Type'),
                email=row.get('Venue Email'),
                phone=row.get('Venue Phone'),
                address=row.get('Venue Address'),
                city=row.get('Venue City'),
                state=row.get('Venue State'),
                zip_code=row.get('Venue Zip Code'),
                max_capacity=max_capacity,
                num_spaces=int(row['Number of Spaces']) if row.get('Number of Spaces') else None,
                has_catering='catering' in (row.get('Space Catering') or '').lower(),
            )
            venues.append(venue)

    # Insert in batches
    async with async_session() as session:
        async with session.begin():
            session.add_all(venues)
        await session.commit()

    print(f"✅ Migrated {len(venues)} venues to database")
    await engine.dispose()

if __name__ == "__main__":
    csv_file = "data/Sample Test Venues_Vendors - Venues.csv"
    asyncio.run(migrate_csv(csv_file))
```

---

## Phase 3: Implement Intent Extraction

### Create Intent Extractor

```python
# app/intent_extractor.py
# (Use the code from HYBRID_SEARCH_ARCHITECTURE.md)
```

### Test Intent Extraction

```python
# test_intent.py
from app.intent_extractor import IntentExtractor
from openai import OpenAI

client = OpenAI(api_key="your-key")
extractor = IntentExtractor(client)

# Test queries
queries = [
    "I need a wedding venue in Miami for 200 guests under $10k",
    "Looking for a rustic barn in Nashville for my corporate retreat",
    "Beachfront hotel with ocean views, capacity 150-200, romantic setting",
]

for query in queries:
    intent = extractor.extract(query)
    print(f"\nQuery: {query}")
    print(f"Intent: {intent.dict()}")
```

---

## Phase 4: Update API Endpoints

### Add Hybrid Search Endpoint

```python
# app/main.py
from .hybrid_search import HybridSearchEngine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create database connection
engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@app.post("/search/hybrid")
async def hybrid_search(request: ChatRequest) -> Dict:
    """
    Hybrid search endpoint combining structured filters,
    vector similarity, and LLM re-ranking.
    """
    async with async_session() as session:
        search_engine = HybridSearchEngine(
            db_session=session,
            vector_store=vector_store,
            openai_client=client
        )

        results = await search_engine.search(
            query=request.query,
            max_results=request.k,
            enable_reranking=True
        )

        return {
            "query": request.query,
            "results": [
                {
                    "id": r["venue"].id,
                    "name": r["venue"].name,
                    "city": r["venue"].city,
                    "state": r["venue"].state,
                    "capacity": r["venue"].max_capacity,
                    "score": r["score"],
                    "explanation": r.get("explanation", ""),
                }
                for r in results
            ]
        }
```

---

## Phase 5: Performance Optimization

### Add Redis Caching

```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis  # Ubuntu

# Start Redis
redis-server

# Add to requirements.txt
redis==5.0.1
```

```python
# app/cache.py
import redis
import json
import hashlib
from typing import Optional, Any

cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def cache_key(prefix: str, data: str) -> str:
    """Generate cache key."""
    hash_val = hashlib.md5(data.encode()).hexdigest()
    return f"{prefix}:{hash_val}"

def get_cached(key: str) -> Optional[Any]:
    """Get from cache."""
    data = cache.get(key)
    return json.loads(data) if data else None

def set_cached(key: str, value: Any, ttl: int = 3600):
    """Set in cache with TTL."""
    cache.setex(key, ttl, json.dumps(value))
```

### Pre-compute Embeddings

```python
# scripts/precompute_embeddings.py
import asyncio
from app.models import Venue
from app.vector_store import vector_store

async def precompute_all_embeddings():
    """Pre-compute embeddings for all venues."""
    async with async_session() as session:
        result = await session.execute(select(Venue))
        venues = result.scalars().all()

        for venue in venues:
            if venue.description and not venue.description_embedding:
                embedding = vector_store._embed([venue.description])[0]
                venue.description_embedding = embedding.tolist()

        await session.commit()
        print(f"✅ Computed embeddings for {len(venues)} venues")

if __name__ == "__main__":
    asyncio.run(precompute_all_embeddings())
```

---

## Testing Strategy

### 1. Unit Tests

```python
# tests/test_intent_extraction.py
import pytest
from app.intent_extractor import IntentExtractor

def test_location_extraction():
    query = "wedding venue in Miami"
    intent = extractor.extract(query)
    assert intent.location.city.lower() == "miami"

def test_capacity_extraction():
    query = "venue for 200 guests"
    intent = extractor.extract(query)
    assert intent.capacity.target == 200
```

### 2. Integration Tests

```python
# tests/test_hybrid_search.py
import pytest
from app.hybrid_search import HybridSearchEngine

@pytest.mark.asyncio
async def test_end_to_end_search():
    results = await search_engine.search(
        "romantic wedding venue in Miami for 150 guests"
    )
    assert len(results) > 0
    assert all(r["venue"].city.lower() == "miami" for r in results)
```

### 3. Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
# Run load test
locust -f tests/locustfile.py --host=http://localhost:8000
```

---

## Deployment Checklist

- [ ] PostgreSQL database with pgvector
- [ ] All venues migrated from CSV
- [ ] Embeddings pre-computed
- [ ] Redis cache configured
- [ ] Environment variables set
- [ ] Database indexes created
- [ ] API endpoints tested
- [ ] Load testing completed
- [ ] Monitoring set up (Sentry, DataDog, etc.)
- [ ] Documentation updated

---

## Monitoring & Observability

### Add Logging

```python
# app/logging_config.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/venuehorn.log')
    ]
)
```

### Track Metrics

```python
# app/metrics.py
from prometheus_client import Counter, Histogram

search_requests = Counter('search_requests_total', 'Total search requests')
search_duration = Histogram('search_duration_seconds', 'Search duration')

@app.middleware("http")
async def track_metrics(request, call_next):
    if request.url.path.startswith("/search"):
        search_requests.inc()
        with search_duration.time():
            response = await call_next(request)
        return response
    return await call_next(request)
```

---

## Cost Optimization Tips

1. **Cache aggressively** - Intent extraction and search results
2. **Batch embeddings** - Pre-compute, don't generate on-demand
3. **Use cheaper models** - gpt-4o-mini for intent, Flash for simple queries
4. **Implement rate limiting** - Prevent abuse
5. **Monitor token usage** - Set alerts for high usage

---

## Next: GitHub Setup

Ready to proceed with **Step 3: Setting up your private GitHub repository**?
