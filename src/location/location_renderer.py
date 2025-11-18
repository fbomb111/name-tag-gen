"""
Location graphic renderer for name badges.

Converts location strings (e.g., "Dayton, Ohio") into visual graphics showing
state/country outlines with a star marker at the city position.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
import time
import re

import requests
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry


@dataclass
class ParsedLocation:
    """Structured representation of a parsed location string."""
    original: str
    city: str
    region: Optional[str] = None  # State/province
    country: Optional[str] = None


@dataclass
class GeocodedLocation:
    """Geographic coordinates for a location."""
    latitude: float
    longitude: float
    display_name: str


class LocationParser:
    """Parses location strings into structured components."""

    # Common US state abbreviations and names
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
        'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
        'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas',
        'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts',
        'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
        'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico',
        'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma',
        'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
        'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
        'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming',
        'District of Columbia'
    }

    def parse(self, location_str: str) -> ParsedLocation:
        """
        Parse a location string into components.

        Examples:
            "Dayton, Ohio" -> ParsedLocation(city="Dayton", region="Ohio", country="USA")
            "Paris, France" -> ParsedLocation(city="Paris", country="France")
            "Toronto, ON, Canada" -> ParsedLocation(city="Toronto", region="ON", country="Canada")
        """
        parts = [p.strip() for p in location_str.split(',')]

        if len(parts) == 1:
            # Just city name
            return ParsedLocation(original=location_str, city=parts[0])

        elif len(parts) == 2:
            # City, State/Country
            city, second = parts
            # Check if second part is a US state
            if second in self.US_STATES:
                return ParsedLocation(
                    original=location_str,
                    city=city,
                    region=second,
                    country="United States"
                )
            else:
                return ParsedLocation(
                    original=location_str,
                    city=city,
                    country=second
                )

        elif len(parts) >= 3:
            # City, State/Province, Country
            city, region, country = parts[0], parts[1], parts[2]
            return ParsedLocation(
                original=location_str,
                city=city,
                region=region,
                country=country
            )

        return ParsedLocation(original=location_str, city=location_str)


class Geocoder:
    """Geocodes location strings using Nominatim (OpenStreetMap) API."""

    BASE_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "NameTagGenerator/1.0"

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize geocoder.

        Args:
            cache_dir: Optional directory to cache geocoding results
        """
        self.cache_dir = cache_dir
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Nominatim requires 1 req/sec max

    def _rate_limit(self):
        """Ensure we don't exceed Nominatim's rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def geocode(self, location: ParsedLocation) -> Optional[GeocodedLocation]:
        """
        Geocode a parsed location to coordinates.

        Returns None if geocoding fails.
        """
        # Build search query
        query_parts = [location.city]
        if location.region:
            query_parts.append(location.region)
        if location.country:
            query_parts.append(location.country)
        query = ", ".join(query_parts)

        # Rate limit
        self._rate_limit()

        # Make API request
        try:
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            headers = {'User-Agent': self.USER_AGENT}

            response = requests.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            results = response.json()
            if not results:
                return None

            result = results[0]
            return GeocodedLocation(
                latitude=float(result['lat']),
                longitude=float(result['lon']),
                display_name=result['display_name']
            )

        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Geocoding failed for '{query}': {e}")
            return None


class BoundaryFetcher:
    """Fetches state/country boundary geometries from Natural Earth data."""

    def __init__(self, data_dir: Path):
        """
        Initialize boundary fetcher.

        Args:
            data_dir: Path to directory containing Natural Earth shapefiles
        """
        self.data_dir = Path(data_dir)
        self.countries_path = self.data_dir / "countries" / "ne_110m_admin_0_countries.shp"
        self.states_path = self.data_dir / "states" / "ne_110m_admin_1_states_provinces.shp"

        # Load shapefiles into memory (cache them)
        self._countries_gdf: Optional[gpd.GeoDataFrame] = None
        self._states_gdf: Optional[gpd.GeoDataFrame] = None

    @property
    def countries_gdf(self) -> gpd.GeoDataFrame:
        """Lazy load countries GeoDataFrame."""
        if self._countries_gdf is None:
            self._countries_gdf = gpd.read_file(self.countries_path)
        return self._countries_gdf

    @property
    def states_gdf(self) -> gpd.GeoDataFrame:
        """Lazy load states GeoDataFrame."""
        if self._states_gdf is None:
            self._states_gdf = gpd.read_file(self.states_path)
        return self._states_gdf

    def get_boundary(self, location: ParsedLocation) -> Optional[BaseGeometry]:
        """
        Get the boundary geometry for a location.

        Returns the most specific boundary available:
        1. State/province if available
        2. Country if available
        3. None if not found
        """
        # Try state/province first
        if location.region:
            state_geom = self._get_state_boundary(
                location.region,
                location.country or "United States"
            )
            if state_geom is not None:
                return state_geom

        # Fall back to country
        if location.country:
            return self._get_country_boundary(location.country)

        return None

    def _get_state_boundary(self, region: str, country: str) -> Optional[BaseGeometry]:
        """Get state/province boundary geometry."""
        gdf = self.states_gdf

        # Normalize country name for matching
        country_normalized = country.lower()
        if country_normalized in ['usa', 'us', 'united states', 'united states of america']:
            country_match = gdf['admin'].str.lower().str.contains('united states', na=False)
        else:
            country_match = gdf['admin'].str.lower().str.contains(country_normalized, na=False)

        # Try exact name match
        region_lower = region.lower()
        name_match = gdf['name'].str.lower() == region_lower

        # Try postal code match (for US states like "OH")
        postal_match = gdf['postal'].str.lower() == region_lower if 'postal' in gdf.columns else False

        matches = gdf[country_match & (name_match | postal_match)]

        if len(matches) > 0:
            return matches.iloc[0].geometry

        return None

    def _get_country_boundary(self, country: str) -> Optional[BaseGeometry]:
        """Get country boundary geometry."""
        gdf = self.countries_gdf
        country_lower = country.lower()

        # Try exact name match
        name_match = gdf['NAME'].str.lower() == country_lower

        # Try common name match
        common_match = gdf['NAME_LONG'].str.lower().str.contains(country_lower, na=False) if 'NAME_LONG' in gdf.columns else False

        matches = gdf[name_match | common_match]

        if len(matches) > 0:
            return matches.iloc[0].geometry

        return None


class CoordinateTransformer:
    """Transforms geographic coordinates to pixel coordinates within a bounding box."""

    def __init__(self, boundary: BaseGeometry, canvas_size: Tuple[float, float]):
        """
        Initialize coordinate transformer.

        Args:
            boundary: Shapely geometry defining the boundary
            canvas_size: (width, height) in pixels for output canvas
        """
        self.boundary = boundary
        self.canvas_width, self.canvas_height = canvas_size

        # Get boundary bounding box
        minx, miny, maxx, maxy = boundary.bounds
        self.geo_bounds = (minx, miny, maxx, maxy)

        # Calculate scale to fit boundary in canvas with padding
        padding_ratio = 0.1  # 10% padding on each side
        geo_width = maxx - minx
        geo_height = maxy - miny

        # Calculate scale factors
        scale_x = self.canvas_width * (1 - 2 * padding_ratio) / geo_width
        scale_y = self.canvas_height * (1 - 2 * padding_ratio) / geo_height

        # Use minimum scale to fit entire boundary
        self.scale = min(scale_x, scale_y)

        # Calculate offsets to center the boundary
        scaled_width = geo_width * self.scale
        scaled_height = geo_height * self.scale
        self.offset_x = (self.canvas_width - scaled_width) / 2
        self.offset_y = (self.canvas_height - scaled_height) / 2

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[float, float]:
        """
        Convert geographic coordinates to pixel coordinates.

        Args:
            lon: Longitude
            lat: Latitude

        Returns:
            (x, y) pixel coordinates
        """
        minx, miny, maxx, maxy = self.geo_bounds

        # Normalize to 0-1 range within bounds
        norm_x = (lon - minx) / (maxx - minx) if maxx != minx else 0.5
        norm_y = (maxy - lat) / (maxy - miny) if maxy != miny else 0.5  # Flip Y axis

        # Scale and offset
        pixel_x = norm_x * (maxx - minx) * self.scale + self.offset_x
        pixel_y = norm_y * (maxy - miny) * self.scale + self.offset_y

        return pixel_x, pixel_y


class SVGRenderer:
    """Renders boundary outlines and location markers as SVG."""

    def __init__(self, canvas_size: Tuple[float, float]):
        """
        Initialize SVG renderer.

        Args:
            canvas_size: (width, height) in pixels
        """
        self.canvas_width, self.canvas_height = canvas_size

    def render(self, boundary: BaseGeometry, marker_pos: Tuple[float, float],
               output_path: Path) -> None:
        """
        Render boundary outline with marker as SVG.

        Args:
            boundary: Shapely geometry for boundary
            marker_pos: (x, y) pixel coordinates for star marker
            output_path: Path to save SVG file
        """
        # Initialize coordinate transformer
        transformer = CoordinateTransformer(boundary, (self.canvas_width, self.canvas_height))

        # Convert boundary to SVG path
        path_data = self._geometry_to_svg_path(boundary, transformer)

        # Generate star marker
        star_svg = self._create_star_marker(marker_pos[0], marker_pos[1], size=8)

        # Build SVG document
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{self.canvas_width}"
     height="{self.canvas_height}"
     viewBox="0 0 {self.canvas_width} {self.canvas_height}">
  <path d="{path_data}"
        fill="none"
        stroke="#3D405B"
        stroke-width="2"
        stroke-linejoin="round"/>
  {star_svg}
</svg>'''

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

    def _geometry_to_svg_path(self, geometry: BaseGeometry,
                              transformer: CoordinateTransformer) -> str:
        """Convert Shapely geometry to SVG path data."""
        from shapely.geometry import Polygon, MultiPolygon

        paths = []

        if isinstance(geometry, Polygon):
            paths.append(self._polygon_to_path(geometry, transformer))
        elif isinstance(geometry, MultiPolygon):
            for polygon in geometry.geoms:
                paths.append(self._polygon_to_path(polygon, transformer))

        return " ".join(paths)

    def _polygon_to_path(self, polygon: 'Polygon',
                        transformer: CoordinateTransformer) -> str:
        """Convert a Shapely Polygon to SVG path data."""
        coords = list(polygon.exterior.coords)

        if not coords:
            return ""

        # Start path
        first_x, first_y = transformer.geo_to_pixel(coords[0][0], coords[0][1])
        path_parts = [f"M {first_x:.2f},{first_y:.2f}"]

        # Add line segments
        for lon, lat in coords[1:]:
            x, y = transformer.geo_to_pixel(lon, lat)
            path_parts.append(f"L {x:.2f},{y:.2f}")

        # Close path
        path_parts.append("Z")

        return " ".join(path_parts)

    def _create_star_marker(self, cx: float, cy: float, size: float = 8) -> str:
        """Create a star marker SVG element."""
        # 5-pointed star
        points = []
        for i in range(5):
            # Outer point
            angle_outer = (i * 72 - 90) * 3.14159 / 180
            x_outer = cx + size * 1.0 * (angle_outer ** 0 - angle_outer ** 0 + 1) * \
                      (1 if i == 0 else (-1 if i in [1, 4] else 0)) * \
                      abs((0 if i == 0 else (0.951 if i == 1 else (-0.588 if i == 2 else (-0.588 if i == 3 else 0.951)))))
            y_outer = cy + size * 1.0 * (angle_outer ** 0 - angle_outer ** 0 + 1) * \
                      ((-1 if i == 0 else (0.309 if i in [1, 4] else 0.809)))

            # Simpler approach: use actual trig
            import math
            angle_outer = (i * 72 - 90) * math.pi / 180
            x_outer = cx + size * math.cos(angle_outer)
            y_outer = cy + size * math.sin(angle_outer)
            points.append(f"{x_outer:.2f},{y_outer:.2f}")

            # Inner point
            angle_inner = (i * 72 - 90 + 36) * math.pi / 180
            x_inner = cx + size * 0.4 * math.cos(angle_inner)
            y_inner = cy + size * 0.4 * math.sin(angle_inner)
            points.append(f"{x_inner:.2f},{y_inner:.2f}")

        return f'<polygon points="{" ".join(points)}" fill="#E07A5F" stroke="none"/>'


def render_location_graphic(location_str: str, output_path: Path,
                           canvas_size: Tuple[float, float] = (144, 144),
                           data_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Render a location graphic as SVG.

    Main public API for the module.

    Args:
        location_str: Location string (e.g., "Dayton, Ohio")
        output_path: Path to save SVG file
        canvas_size: (width, height) in pixels (default: 144x144 = 0.5in @ 288 DPI)
        data_dir: Path to Natural Earth data directory (default: ./data/natural_earth)

    Returns:
        Path to generated SVG file, or None if generation failed
    """
    # Default data directory (project root / data / natural_earth)
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent / "data" / "natural_earth"

    try:
        # Parse location
        parser = LocationParser()
        parsed_location = parser.parse(location_str)

        # Geocode
        geocoder = Geocoder()
        geocoded = geocoder.geocode(parsed_location)
        if geocoded is None:
            print(f"Failed to geocode: {location_str}")
            return None

        # Get boundary
        boundary_fetcher = BoundaryFetcher(data_dir)
        boundary = boundary_fetcher.get_boundary(parsed_location)
        if boundary is None:
            print(f"Failed to find boundary for: {location_str}")
            return None

        # Transform coordinates
        transformer = CoordinateTransformer(boundary, canvas_size)
        marker_x, marker_y = transformer.geo_to_pixel(
            geocoded.longitude,
            geocoded.latitude
        )

        # Render SVG
        renderer = SVGRenderer(canvas_size)
        renderer.render(boundary, (marker_x, marker_y), output_path)

        return output_path

    except Exception as e:
        print(f"Failed to render location graphic for '{location_str}': {e}")
        import traceback
        traceback.print_exc()
        return None
