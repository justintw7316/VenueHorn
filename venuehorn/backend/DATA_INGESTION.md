```# Data Ingestion Pipeline

## Overview

Enhanced data ingestion pipeline for VenueHorn with validation, cleaning, geocoding, and quality reporting.

## Features

### ✅ Data Validation
- **Required field checks** (name, location, description)
- **Email validation** with cleaning
- **Phone number formatting**
- **Website URL validation**
- **Duplicate detection** (same name + location)

### 🔧 Data Cleaning & Enrichment
- **Capacity parsing** - Handles various formats:
  - "Up to 120"
  - "Max Seated: 175Max Standing: 100"
  - "150-200 guests"
  - Plain numbers
- **Price tier estimation** - Based on venue type and name:
  - Budget (churches, schools, community centers)
  - Mid-range (restaurants, breweries, bars)
  - Luxury (hotels, resorts, country clubs)
  - Ultra-luxury (Ritz, Four Seasons, etc.)
- **Amenity extraction** - Auto-detects from descriptions:
  - Parking, catering, bar, outdoor space
  - Pool, WiFi, AV equipment, dance floor
  - Stage, accommodation, accessibility, beach access

### 🌍 Geocoding
- **Multi-provider support**:
  1. File cache (instant, zero cost)
  2. US Census Geocoder (free, accurate)
  3. Nominatim/OpenStreetMap (free, rate-limited)
  4. City center fallback (approximate)
- **Automatic caching** - Never geocode same address twice
- **Batch processing** - Respects rate limits

### 📊 Comprehensive Reporting
- Validation statistics
- Geocoding success rates
- Data quality warnings
- Processing errors

---

## Usage

### Basic Ingestion

```bash
cd venuehorn/backend

# Full pipeline with all features
python scripts/ingest_venues_enhanced.py "data/Sample Test Venues_Vendors - Venues.csv"
```

### Advanced Options

```bash
# Skip geocoding (faster, but no location data)
python scripts/ingest_venues_enhanced.py "data/venues.csv" --no-geocoding

# Skip embedding generation (for testing data validation only)
python scripts/ingest_venues_enhanced.py "data/venues.csv" --no-embedding

# Skip validation (not recommended)
python scripts/ingest_venues_enhanced.py "data/venues.csv" --skip-validation
```

---

## Output Files

After ingestion, you'll find:

```
backend/data/
├── index.faiss              # Vector index (FAISS)
├── meta.json                # Chunk metadata
├── geocode_cache.json       # Geocoding cache (reusable!)
├── processed_venues.json    # Cleaned venue data
└── ingestion.log           # Detailed logs
```

---

## Example Output

```
==============================================================
VenueHorn Data Ingestion Pipeline
==============================================================
Reading CSV from: data/Sample Test Venues_Vendors - Venues.csv
Read 108 venues from CSV

Validating venue data...
Validation complete:
  Total rows: 108
  Valid rows: 95
  Missing names: 0
  Missing locations: 8
  Missing descriptions: 13
  Potential duplicates: 2

Processing and enriching venue data...
Processed 10/108 venues...
Processed 20/108 venues...
...
Processed 95 venues successfully

Creating search documents...
Generating embeddings and indexing...
Added 187 chunks to vector index

==============================================================
Ingestion Complete!
==============================================================
Total venues in CSV: 108
Successfully processed: 95
Geocoded: 87
Indexed chunks: 187
Skipped (invalid): 13
Errors: 0

Geocoding stats: {
  "total_requests": 87,
  "cache_hits": 0,
  "api_calls": 87,
  "cache_hit_rate": "0.0%"
}

Saved processed venues to: data/processed_venues.json
```

---

## Data Quality Checks

The pipeline automatically checks for:

### ❌ Issues Detected
- Missing venue name (skipped)
- Missing city or state (warning)
- Missing description (warning)
- Invalid email format (warning)
- Invalid website URL (warning)
- Duplicate venues (warning with similarity score)

### ✅ Auto-Fixes Applied
- Phone numbers formatted to (XXX) XXX-XXXX
- Emails cleaned and lowercased
- Websites prefixed with https://
- Capacity extracted from various formats
- Amenities detected from descriptions
- Price tiers estimated

---

## Performance

| Metric | Value |
|--------|-------|
| Processing speed | ~10 venues/second |
| Geocoding (cached) | Instant |
| Geocoding (API) | ~1 address/second |
| Embedding generation | ~5 venues/second |
| **Total for 1000 venues** | ~5 minutes |

**Note:** First run is slower due to geocoding. Subsequent runs use cache and are much faster.

---

## Geocoding Cache

The geocoding cache saves API calls and speeds up repeated ingestion:

```json
{
  "a1b2c3d4e5f6...": {
    "latitude": 25.7617,
    "longitude": -80.1918,
    "formatted_address": "123 Main St, Miami, FL 33101, USA",
    "city": "Miami",
    "state": "Florida",
    "zip_code": "33101",
    "country": "USA"
  }
}
```

**Benefits:**
- Zero cost for repeated ingestion
- Instant lookups
- Shareable across team
- Preserves manual corrections

---

## Processed Venues Format

The pipeline outputs cleaned data to `processed_venues.json`:

```json
[
  {
    "name": "Ocean Pearl Resort",
    "venue_type": "Hotel",
    "city": "Miami",
    "state": "Florida",
    "latitude": 25.7617,
    "longitude": -80.1918,
    "min_capacity": 180,
    "max_capacity": 300,
    "price_tier": "luxury",
    "amenities": [
      "parking",
      "catering",
      "bar",
      "pool",
      "wifi",
      "accommodation",
      "beach_access"
    ],
    "email": "info@oceanpearl.com",
    "phone": "(305) 555-1234",
    "website": "https://oceanpearl.com",
    "description": "Stunning beachfront resort..."
  }
]
```

---

## Troubleshooting

### "Geocoding failed"
- **Cause:** API rate limit or invalid address
- **Fix:** Uses city center fallback automatically
- **Note:** Check `geocode_cache.json` for results

### "Missing description" warnings
- **Cause:** CSV has empty description field
- **Fix:** Venue is still processed, but search quality may be lower
- **Action:** Add descriptions manually if needed

### "Duplicate detected"
- **Cause:** Same venue name + city in CSV
- **Fix:** Remove duplicates from CSV before ingesting
- **Note:** Pipeline shows similarity score

### Embedding generation slow
- **Cause:** OpenAI API rate limits
- **Fix:** Normal for large datasets
- **Option:** Use `--no-embedding` for testing, then run separately

---

## Integration with Database

To migrate to PostgreSQL (future):

```python
from app.models import Venue
from sqlalchemy.ext.asyncio import AsyncSession
import json

# Load processed venues
with open('data/processed_venues.json') as f:
    venues_data = json.load(f)

# Insert into database
async with async_session() as session:
    for venue_data in venues_data:
        venue = Venue(**venue_data)
        session.add(venue)
    await session.commit()
```

---

## Next Steps

1. **Review output** - Check `processed_venues.json` for data quality
2. **Test search** - Try querying with the `/chat` endpoint
3. **Iterate** - Fix CSV issues and re-run (uses cache!)
4. **Migrate to DB** - Move to PostgreSQL for hybrid search
5. **Add more data** - Ingest additional CSV files

---

## Tips for Best Results

1. **Clean your CSV first** - Remove obvious duplicates
2. **Provide descriptions** - Critical for search quality
3. **Include addresses** - Improves geocoding accuracy
4. **Run validation only** - Use `--no-embedding` to test data quality
5. **Keep the cache** - Don't delete `geocode_cache.json`
6. **Check logs** - Review `ingestion.log` for warnings

---

## Cost Estimation

| Operation | Cost | Notes |
|-----------|------|-------|
| Geocoding | **FREE** | US Census + Nominatim |
| Embeddings | ~$0.01 per 1000 venues | OpenAI text-embedding-3-small |
| Vector index | **FREE** | FAISS (local) |

**Example:** 10,000 venues = ~$0.10 for embeddings only

---

## Support

For issues or questions:
- Check `ingestion.log` for detailed error messages
- Review `processed_venues.json` for data quality
- Verify OpenAI API key is set in `.env`
- Ensure CSV encoding is UTF-8
