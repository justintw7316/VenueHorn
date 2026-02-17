#!/bin/bash
# VenueHorn Quick Demo Script
# This script sets up and tests the entire VenueHorn system

set -e  # Exit on error

echo "============================================================"
echo "VenueHorn Quick Demo"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo ""
    echo "Please create a .env file with your OpenAI API key:"
    echo ""
    echo "  cp .env.example .env"
    echo "  # Then edit .env and add: OPENAI_API_KEY=sk-your-key-here"
    echo ""
    exit 1
fi

# Check if OpenAI key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  OpenAI API key not configured${NC}"
    echo ""
    echo "Please edit .env and add your OpenAI API key:"
    echo "  OPENAI_API_KEY=sk-your-actual-key-here"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Check if data is already ingested
if [ -f data/index.faiss ]; then
    echo -e "${YELLOW}📊 Vector index already exists${NC}"
    read -p "Re-ingest data? This will overwrite existing index (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Re-ingesting data..."
        python3 scripts/ingest_venues_enhanced.py "data/Sample Test Venues_Vendors - Venues.csv"
    else
        echo "Using existing index..."
    fi
else
    echo "Ingesting sample venue data..."
    python3 scripts/ingest_venues_enhanced.py "data/Sample Test Venues_Vendors - Venues.csv"
fi

echo ""
echo -e "${GREEN}✅ Data ingestion complete${NC}"
echo ""

# Show some stats
if [ -f data/processed_venues.json ]; then
    VENUE_COUNT=$(cat data/processed_venues.json | grep -c '"name"')
    echo "📊 Statistics:"
    echo "   Venues indexed: $VENUE_COUNT"

    if [ -f data/geocode_cache.json ]; then
        GEOCODED_COUNT=$(cat data/geocode_cache.json | grep -c '"latitude"')
        echo "   Geocoded locations: $GEOCODED_COUNT"
    fi

    if [ -f data/index.faiss ]; then
        INDEX_SIZE=$(ls -lh data/index.faiss | awk '{print $5}')
        echo "   Vector index size: $INDEX_SIZE"
    fi
fi

echo ""
echo "============================================================"
echo "🚀 Starting VenueHorn API Server"
echo "============================================================"
echo ""
echo "Server will start on: http://localhost:8000"
echo ""
echo "Try these example queries in another terminal:"
echo ""
echo -e "${YELLOW}# Test 1: Health check${NC}"
echo "curl http://localhost:8000/health"
echo ""
echo -e "${YELLOW}# Test 2: Find wedding venue in Miami${NC}"
echo 'curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '"'"'{"query": "wedding venue in Miami for 200 guests", "k": 5}'"'"''
echo ""
echo -e "${YELLOW}# Test 3: Find beachfront venue${NC}"
echo 'curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '"'"'{"query": "romantic beachfront venue with ocean views", "k": 3}'"'"''
echo ""
echo -e "${YELLOW}# Or run the full test suite:${NC}"
echo "python3 test_api.py"
echo ""
echo "============================================================"
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Start the server
uvicorn app.main:app --reload --port 8000
