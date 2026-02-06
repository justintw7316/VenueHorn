"""
Geocoding utilities with caching for VenueHorn.
Converts addresses to lat/lng coordinates with efficient caching.
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple, Dict
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeoLocation:
    """Geocoded location information."""
    latitude: float
    longitude: float
    formatted_address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "USA"


class GeocodeCache:
    """File-based cache for geocoding results."""

    def __init__(self, cache_file: str = "data/geocode_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, dict] = {}
        self._load_cache()

    def _load_cache(self):
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} geocoded addresses from cache")
            except Exception as e:
                logger.warning(f"Could not load geocode cache: {e}")
                self.cache = {}
        else:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save geocode cache: {e}")

    @staticmethod
    def _address_key(address: str, city: str, state: str, zip_code: str = '') -> str:
        """Generate cache key from address components."""
        components = [address, city, state, zip_code]
        address_str = ' '.join(c.strip().lower() for c in components if c)
        return hashlib.md5(address_str.encode()).hexdigest()

    def get(self, address: str, city: str, state: str, zip_code: str = '') -> Optional[GeoLocation]:
        """Get cached geocode result."""
        key = self._address_key(address, city, state, zip_code)
        if key in self.cache:
            return GeoLocation(**self.cache[key])
        return None

    def set(self, address: str, city: str, state: str, zip_code: str, location: GeoLocation):
        """Cache a geocode result."""
        key = self._address_key(address, city, state, zip_code)
        self.cache[key] = asdict(location)
        self._save_cache()


class Geocoder:
    """
    Geocoder with multiple providers and caching.

    Supports:
    1. Cache lookup (instant)
    2. Nominatim (free, rate-limited)
    3. US Census Geocoder (free, USA only)
    4. Manual fallback (city/state center)
    """

    # Approximate city centers for fallback
    MAJOR_CITIES = {
        ('miami', 'florida'): (25.7617, -80.1918),
        ('new york', 'new york'): (40.7128, -74.0060),
        ('los angeles', 'california'): (34.0522, -118.2437),
        ('chicago', 'illinois'): (41.8781, -87.6298),
        ('houston', 'texas'): (29.7604, -95.3698),
        ('phoenix', 'arizona'): (33.4484, -112.0740),
        ('philadelphia', 'pennsylvania'): (39.9526, -75.1652),
        ('san antonio', 'texas'): (29.4241, -98.4936),
        ('san diego', 'california'): (32.7157, -117.1611),
        ('dallas', 'texas'): (32.7767, -96.7970),
        ('boston', 'massachusetts'): (42.3601, -71.0589),
        ('birmingham', 'alabama'): (33.5186, -86.8104),
        ('montgomery', 'alabama'): (32.3668, -86.3000),
        ('nashville', 'tennessee'): (36.1627, -86.7816),
    }

    def __init__(self, cache_file: str = "data/geocode_cache.json"):
        self.cache = GeocodeCache(cache_file)
        self.request_count = 0
        self.cache_hits = 0

    def geocode(
        self,
        address: Optional[str],
        city: str,
        state: str,
        zip_code: Optional[str] = None
    ) -> Optional[GeoLocation]:
        """
        Geocode an address with caching and fallbacks.

        Args:
            address: Street address
            city: City name
            state: State name
            zip_code: Zip code (optional)

        Returns:
            GeoLocation or None if geocoding fails
        """
        if not city or not state:
            logger.warning("Cannot geocode without city and state")
            return None

        # Check cache first
        cached = self.cache.get(address or '', city, state, zip_code or '')
        if cached:
            self.cache_hits += 1
            return cached

        self.request_count += 1

        # Try US Census Geocoder (free, accurate for US)
        location = self._geocode_census(address, city, state, zip_code)
        if location:
            self.cache.set(address or '', city, state, zip_code or '', location)
            return location

        # Try Nominatim (free, rate-limited)
        location = self._geocode_nominatim(address, city, state, zip_code)
        if location:
            self.cache.set(address or '', city, state, zip_code or '', location)
            return location

        # Fallback to city center
        location = self._geocode_city_fallback(city, state)
        if location:
            logger.info(f"Using city center fallback for {city}, {state}")
            self.cache.set(address or '', city, state, zip_code or '', location)
            return location

        logger.warning(f"Could not geocode: {address}, {city}, {state}")
        return None

    def _geocode_census(
        self,
        address: Optional[str],
        city: str,
        state: str,
        zip_code: Optional[str]
    ) -> Optional[GeoLocation]:
        """Geocode using US Census Geocoder (free, USA only)."""
        try:
            import requests

            # Build address string
            if address and zip_code:
                address_str = f"{address}, {city}, {state} {zip_code}"
            elif address:
                address_str = f"{address}, {city}, {state}"
            else:
                address_str = f"{city}, {state}"

            url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
            params = {
                "address": address_str,
                "benchmark": "2020",
                "format": "json"
            }

            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get("result", {}).get("addressMatches"):
                match = data["result"]["addressMatches"][0]
                coords = match["coordinates"]

                return GeoLocation(
                    latitude=coords["y"],
                    longitude=coords["x"],
                    formatted_address=match["matchedAddress"],
                    city=city,
                    state=state,
                    zip_code=zip_code
                )

        except Exception as e:
            logger.debug(f"Census geocoding failed: {e}")

        return None

    def _geocode_nominatim(
        self,
        address: Optional[str],
        city: str,
        state: str,
        zip_code: Optional[str]
    ) -> Optional[GeoLocation]:
        """Geocode using Nominatim (free, rate-limited to 1 req/sec)."""
        try:
            import requests

            # Respect rate limit
            time.sleep(1)

            # Build query
            if address:
                query = f"{address}, {city}, {state}, USA"
            else:
                query = f"{city}, {state}, USA"

            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": query,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            headers = {
                "User-Agent": "VenueHorn/1.0"
            }

            response = requests.get(url, params=params, headers=headers, timeout=5)
            data = response.json()

            if data:
                result = data[0]
                return GeoLocation(
                    latitude=float(result["lat"]),
                    longitude=float(result["lon"]),
                    formatted_address=result.get("display_name", query),
                    city=city,
                    state=state,
                    zip_code=zip_code
                )

        except Exception as e:
            logger.debug(f"Nominatim geocoding failed: {e}")

        return None

    def _geocode_city_fallback(self, city: str, state: str) -> Optional[GeoLocation]:
        """Use approximate city center as fallback."""
        key = (city.lower().strip(), state.lower().strip())

        if key in self.MAJOR_CITIES:
            lat, lng = self.MAJOR_CITIES[key]
            return GeoLocation(
                latitude=lat,
                longitude=lng,
                formatted_address=f"{city}, {state}, USA",
                city=city,
                state=state
            )

        # Try just state name
        state_lower = state.lower()
        for (c, s), coords in self.MAJOR_CITIES.items():
            if s == state_lower:
                # Use first major city in state as very rough fallback
                return GeoLocation(
                    latitude=coords[0],
                    longitude=coords[1],
                    formatted_address=f"{city}, {state}, USA (approximate)",
                    city=city,
                    state=state
                )

        return None

    def get_stats(self) -> dict:
        """Get geocoding statistics."""
        total_requests = self.request_count + self.cache_hits
        cache_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "cache_hits": self.cache_hits,
            "api_calls": self.request_count,
            "cache_hit_rate": f"{cache_rate:.1f}%"
        }
