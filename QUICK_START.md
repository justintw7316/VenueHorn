# VenueHorn - Quick Start Guide

## 🚀 Test VenueHorn in 5 Minutes!

This guide will help you set up and test the complete VenueHorn AI system with your sample data.

---

## Prerequisites

- Python 3.9+ installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

---

## Step 1: Set Up Python Environment

```bash
# Navigate to backend directory
cd venuehorn/backend

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed fastapi-0.115.0 uvicorn-0.30.6 openai-1.40.6 ...
```

---

## Step 2: Configure OpenAI API Key

```bash
# Create .env file from template
cp .env.example .env

# Edit .env and add your API key
# You can use nano, vim, or any text editor
nano .env
```

**Add this line to .env:**
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**Save and exit** (Ctrl+X, then Y, then Enter in nano)

---

## Step 3: Ingest Sample Data

```bash
# Run the enhanced ingestion pipeline
python3 scripts/ingest_venues_enhanced.py "data/Sample Test Venues_Vendors - Venues.csv"
```

**What this does:**
- ✅ Validates 108 venue records
- ✅ Parses capacities (handles "Up to 120", "Max Seated: 175", etc.)
- ✅ Geocodes locations (FREE - uses US Census + caching)
- ✅ Extracts amenities from descriptions
- ✅ Estimates price tiers
- ✅ Generates embeddings with OpenAI
- ✅ Creates vector search index

**Expected output:**
```
============================================================
VenueHorn Data Ingestion Pipeline
============================================================
Reading CSV from: data/Sample Test Venues_Vendors - Venues.csv
Read 108 venues from CSV

Validating venue data...
  Total rows: 108
  Valid rows: 95
  Geocoded: 87

Processing and enriching venue data...
Processed 95 venues successfully

Generating embeddings and indexing...
Added 187 chunks to vector index

============================================================
Ingestion Complete!
============================================================
Total venues in CSV: 108
Successfully processed: 95
Geocoded: 87
Indexed chunks: 187
```

**⏱️ Time:** ~2-3 minutes (geocoding + embedding generation)

**💰 Cost:** ~$0.01 (embeddings only)

---

## Step 4: Start the API Server

```bash
# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Your server is now running!**

Leave this terminal open and running. Open a **new terminal** for the next steps.

---

## Step 5: Test the API

### Option A: Use the Test Script (Easiest)

In a **new terminal**:

```bash
cd venuehorn/backend
source .venv/bin/activate  # Activate venv again
python3 test_api.py
```

**Expected output:**
```
============================================================
VenueHorn API Test Suite
============================================================

Testing /health endpoint...
Status: 200
Response: {'status': 'ok'}

Testing /search endpoint...
Status: 200
Response: {
  "hits": [
    {
      "text": "Venue: AC Hotel By Marriott Boston Cambridge...",
      "source": "AC Hotel By Marriott Boston Cambridge - Cambridge, Massachusetts",
      "score": 0.85
    }
  ]
}

Testing /chat endpoint...
Status: 200
AI Response: Based on your requirements, I found several great venues...
```

### Option B: Manual Testing with curl

**Test 1: Health Check**
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok"}`

**Test 2: Search for Wedding Venues**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need a wedding venue in Miami for 200 guests",
    "k": 5
  }'
```

**Test 3: Find Beach Venues**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "romantic beachfront venue with ocean views",
    "k": 3
  }'
```

**Test 4: Corporate Event Space**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need a venue for a corporate event with 100 people, needs AV equipment and parking",
    "k": 5
  }'
```

**Test 5: Budget-Friendly Venue**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "affordable venue in Alabama for a birthday party, about 50 guests",
    "k": 5
  }'
```

---

## Step 6: Explore the Results

### Check Processed Data

```bash
# View the cleaned venue data
cat data/processed_venues.json | head -50

# Or open in a text editor
nano data/processed_venues.json
```

**Example venue:**
```json
{
  "name": "Zuri Restaurant",
  "city": "Miami",
  "state": "Florida",
  "latitude": 25.8008,
  "longitude": -80.1953,
  "min_capacity": null,
  "max_capacity": null,
  "price_tier": "mid",
  "amenities": [],
  "venue_type": "Restaurant",
  "description": "Book your event at Zuri today!...",
  "phone": "(305) 522-8552",
  "email": null
}
```

### Check Geocoding Cache

```bash
# See what addresses were geocoded
cat data/geocode_cache.json | head -30
```

### Check Logs

```bash
# View detailed ingestion logs
tail -50 data/ingestion.log
```

---

## Example API Responses

### Search Response (Raw Chunks)
```json
{
  "hits": [
    {
      "text": "Venue: Zoo Miami\nType: Aquarium / Zoo\nLocation: Miami, Florida\nCapacity: up to 3000 guests\nDescription: Zoo Miami is an unforgettable destination...",
      "source": "Zoo Miami - Miami, Florida",
      "score": 0.87
    }
  ]
}
```

### Chat Response (AI-Generated)
```json
{
  "answer": "Based on your requirements for a wedding venue in Miami for 200 guests, I found several excellent options:\n\n1. **Zoo Miami** - This unique venue can accommodate up to 3,000 guests and offers an unforgettable experience incorporating nature and animals. Perfect for couples looking for something truly different!\n\n2. **Zuri Restaurant** - Located in Miami's Wynwood district, this Moroccan-inspired venue offers vibrant atmosphere and authentic cuisine. While specific capacity isn't listed, it's ideal for intimate celebrations with a unique cultural flair.\n\nWould you like more details about any of these venues, or would you prefer to see other options?",
  "hits": [
    {
      "text": "Venue: Zoo Miami...",
      "source": "Zoo Miami - Miami, Florida",
      "score": 0.87
    },
    {
      "text": "Venue: Zuri Restaurant...",
      "source": "Zuri Restaurant - Miami, Florida",
      "score": 0.82
    }
  ]
}
```

---

## What's Happening Behind the Scenes?

### When you query "wedding venue in Miami for 200 guests":

1. **Your query** → Converted to embedding (1536-dimensional vector)
2. **Vector search** → Finds top 5 most similar venue descriptions
3. **Context building** → Combines venue info into readable format
4. **LLM call** → GPT-4o-mini generates personalized response
5. **Response** → Returns AI answer + matching venues

**Total time:** ~1-2 seconds

---

## Inspect Your Data Files

After ingestion, check these files:

```bash
ls -lh data/

# You should see:
# index.faiss            - Vector index (~500KB for 108 venues)
# meta.json              - Metadata (~50KB)
# geocode_cache.json     - Geocoding cache (~10KB)
# processed_venues.json  - Cleaned data (~100KB)
# ingestion.log          - Logs
```

---

## Common Issues & Solutions

### "ModuleNotFoundError: No module named 'openai'"
**Fix:** Make sure virtual environment is activated
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "AuthenticationError: Invalid API key"
**Fix:** Check your `.env` file has correct OpenAI API key
```bash
cat .env  # Should show: OPENAI_API_KEY=sk-...
```

### "Address already in use" (port 8000 busy)
**Fix:** Use a different port
```bash
uvicorn app.main:app --reload --port 8001
# Then test on http://localhost:8001
```

### No results from search
**Fix:** Make sure data was ingested successfully
```bash
# Check if index exists
ls -lh data/index.faiss

# Re-run ingestion if needed
python3 scripts/ingest_venues_enhanced.py "data/Sample Test Venues_Vendors - Venues.csv"
```

---

## Try Different Queries!

Here are some fun queries to try:

```bash
# Specific location
"venues in Birmingham, Alabama"

# Event type
"brewery or bar for a birthday party"

# Amenities
"outdoor venue with parking and catering"

# Capacity
"small intimate venue for 50 people"

# Style
"elegant luxury hotel for corporate event"

# Multiple criteria
"romantic restaurant in Florida with ocean views for 100 guests"
```

---

## View Real-Time Logs

Watch the API logs while testing:

```bash
# In the terminal where uvicorn is running, you'll see:
INFO:     127.0.0.1:52156 - "POST /chat HTTP/1.1" 200 OK
```

---

## Stop the Server

When you're done testing:

1. Go to terminal running uvicorn
2. Press `Ctrl+C`
3. Deactivate virtual environment: `deactivate`

---

## What You've Tested

✅ **Data Ingestion** - Validated, cleaned, geocoded 95 venues
✅ **Vector Search** - FAISS similarity search
✅ **Embedding Generation** - OpenAI text-embedding-3-small
✅ **LLM Integration** - GPT-4o-mini conversational AI
✅ **API Endpoints** - FastAPI with full CRUD operations
✅ **Error Handling** - Graceful failures and logging

---

## Next Steps

Now that you've tested locally:

1. **Try more queries** - Test edge cases and different scenarios
2. **Review results** - Check `processed_venues.json` for data quality
3. **Tweak settings** - Adjust `app/config.py` (chunk size, score threshold)
4. **Add more data** - Ingest additional CSV files
5. **Build frontend** - Connect Next.js UI to the API
6. **Deploy** - Push to GitHub and deploy to cloud

---

## Performance Stats

From your sample data (108 venues):

| Metric | Value |
|--------|-------|
| Ingestion time | ~2-3 min |
| Query response time | ~1-2 sec |
| Embeddings cost | ~$0.01 |
| Chat completions cost | ~$0.001 per query |
| Vector index size | ~500 KB |
| Geocoding cost | **FREE** |

---

## 🎉 You're All Set!

You now have a fully functional AI-powered venue search system running locally!

**Questions?** Check the documentation:
- [Backend README](venuehorn/backend/README.md)
- [Data Ingestion Guide](venuehorn/backend/DATA_INGESTION.md)
- [Architecture Design](HYBRID_SEARCH_ARCHITECTURE.md)

**Happy testing! 🚀**
