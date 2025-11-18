"""
Location normalization for badge generation.
Validates and standardizes location strings to ensure they can be geocoded.
"""
import time
from typing import Optional, Dict
import requests
from pathlib import Path
import json


class LocationNormalizer:
    """Normalizes location strings to standard City, State/Country format."""

    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize normalizer with optional cache.

        Args:
            cache_file: Path to JSON cache file for normalized locations
        """
        self.cache_file = cache_file or Path("output/location_normalization_cache.json")
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, str]:
        """Load normalization cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self) -> None:
        """Save normalization cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def normalize(self, location_str: str, retry_delay: float = 1.0) -> Optional[str]:
        """
        Normalize a location string to standard format.

        Handles:
        - Neighborhoods (extracts city/state)
        - Misspellings (uses geocoding to find correct match)
        - Various formats (standardizes to City, State or City, Country)

        Args:
            location_str: Raw location string from user input
            retry_delay: Delay between API calls (seconds)

        Returns:
            Normalized location string, or None if unable to normalize
        """
        if not location_str or not location_str.strip():
            return None

        # Check cache first
        if location_str in self.cache:
            cached = self.cache[location_str]
            return cached if cached != "" else None

        # Try geocoding the location
        try:
            time.sleep(retry_delay)  # Rate limiting

            geocode_result = self._geocode(location_str)

            if geocode_result:
                normalized = self._format_normalized(geocode_result)
                self.cache[location_str] = normalized
                self._save_cache()
                return normalized
            else:
                # Cache failure as empty string to avoid repeated API calls
                self.cache[location_str] = ""
                self._save_cache()
                return None

        except Exception as e:
            print(f"  Warning: Failed to normalize location '{location_str}': {e}")
            return None

    def _geocode(self, location_str: str) -> Optional[Dict]:
        """
        Geocode a location string using Nominatim API.

        Args:
            location_str: Location to geocode

        Returns:
            Geocoding result dict or None
        """
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location_str,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "accept-language": "en"  # Force English names for international consistency
        }
        headers = {
            "User-Agent": "BadgeGenerator/1.0"
        }

        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            results = response.json()
            if results:
                return results[0]

        return None

    def _format_normalized(self, geocode_result: Dict) -> str:
        """
        Format geocoding result into normalized location string.

        Priority:
        1. City, State (for US locations)
        2. City, Country (for international locations)
        3. State, Country (if no city available)

        Args:
            geocode_result: Result from geocoding API

        Returns:
            Formatted location string
        """
        address = geocode_result.get("address", {})

        # Extract components
        city = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("county")  # Fallback to county if no city
        )
        state = address.get("state")
        country = address.get("country")

        # US locations: City, State
        if country in ("United States", "United States of America"):
            if city and state:
                # Abbreviate state if possible
                state_abbrev = self._abbreviate_state(state)
                return f"{city}, {state_abbrev}"
            elif state:
                return state

        # International: City, Country (or State, Country if no city)
        if city and country:
            return f"{city}, {country}"
        elif state and country:
            # For international locations, state might be the city-level entity
            return f"{state}, {country}"
        elif country:
            return country

        # Fallback to original display name
        return geocode_result.get("display_name", "").split(",")[0]

    def _abbreviate_state(self, state_name: str) -> str:
        """Convert US state name to abbreviation."""
        state_abbrevs = {
            "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
            "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
            "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
            "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
            "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
            "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
            "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
            "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
            "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
            "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
            "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
            "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
            "Wisconsin": "WI", "Wyoming": "WY"
        }
        return state_abbrevs.get(state_name, state_name)


def normalize_location(location_str: str) -> Optional[str]:
    """
    Convenience function to normalize a single location.

    Args:
        location_str: Raw location string

    Returns:
        Normalized location or None
    """
    normalizer = LocationNormalizer()
    return normalizer.normalize(location_str)
