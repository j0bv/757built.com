"""
Weather data ingestor for the 757Built platform.

This module fetches weather data from the National Weather Service API
and converts it to a format compatible with D3.js visualizations.
The data is specifically filtered to locations within the Hampton Roads region.
"""

import json
import logging
import requests
import datetime
from typing import Dict, Any, List, Optional, Tuple

from .base_ingestor import BaseTelemetryIngestor, SEVEN_CITIES, HAMPTON_ROADS_BOUNDS

logger = logging.getLogger(__name__)

# NWS API endpoints
NWS_API_BASE = "https://api.weather.gov/"
NWS_HEADERS = {
    "User-Agent": "757Built/1.0 (https://757built.com; info@757built.com)",
    "Accept": "application/geo+json"
}

class WeatherDataIngestor(BaseTelemetryIngestor):
    """Ingestor for National Weather Service weather data."""
    
    def __init__(self, 
                 graph_client=None, 
                 storage_client=None,
                 weather_types=None,
                 store_in_ipfs=True,
                 local_storage_path=None,
                 refresh_interval_minutes=60):
        """
        Initialize the weather data ingestor.
        
        Args:
            graph_client: Graph database client
            storage_client: Storage client (IPFS or local)
            weather_types: List of weather data types to fetch (temperature, precipitation, etc.)
            store_in_ipfs: Whether to store data in IPFS
            local_storage_path: Path for local storage if not using IPFS
            refresh_interval_minutes: How often to fetch new data
        """
        super().__init__(
            graph_client=graph_client,
            storage_client=storage_client,
            metric_type="weather",
            unit="variable",  # Will be set per reading
            data_license="CC0-1.0",  # NWS data is public domain
            store_in_ipfs=store_in_ipfs,
            local_storage_path=local_storage_path
        )
        
        self.weather_types = weather_types or ["temperature", "precipitation", "wind", "humidity"]
        self.refresh_interval = datetime.timedelta(minutes=refresh_interval_minutes)
        self.last_fetch = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        
        # Pre-define Hampton Roads NWS grid points to avoid API limits
        # These are the NWS grid points that cover the Seven Cities
        self.hampton_roads_points = [
            # Format: (office, grid_x, grid_y, city)
            ("AKQ", 70, 32, "NORFOLK"),
            ("AKQ", 71, 32, "VIRGINIA BEACH"),
            ("AKQ", 69, 31, "CHESAPEAKE"),
            ("AKQ", 68, 32, "PORTSMOUTH"),
            ("AKQ", 66, 33, "SUFFOLK"),
            ("AKQ", 67, 35, "HAMPTON"),
            ("AKQ", 66, 35, "NEWPORT NEWS")
        ]
    
    def _fetch_weather_data(self, office: str, grid_x: int, grid_y: int) -> Optional[Dict]:
        """
        Fetch weather data for a specific NWS grid point.
        
        Args:
            office: NWS office code (e.g., AKQ for Wakefield, VA)
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate
            
        Returns:
            Weather data or None if fetch failed
        """
        url = f"{NWS_API_BASE}gridpoints/{office}/{grid_x},{grid_y}"
        
        try:
            response = requests.get(url, headers=NWS_HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None
    
    def _extract_weather_value(self, data: Dict, weather_type: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract a specific weather value from NWS data.
        
        Args:
            data: NWS API response data
            weather_type: Type of weather data to extract
            
        Returns:
            Tuple of (value, unit) or (None, None) if not available
        """
        if not data or 'properties' not in data:
            return None, None
        
        properties = data['properties']
        
        # Map weather type to NWS API property
        type_to_property = {
            "temperature": "temperature",
            "precipitation": "quantitativePrecipitation",
            "wind": "windSpeed",
            "humidity": "relativeHumidity"
        }
        
        property_name = type_to_property.get(weather_type)
        if not property_name or property_name not in properties:
            return None, None
        
        property_data = properties[property_name]
        
        # Extract the current value
        if 'values' in property_data:
            # Find the most recent value
            now = datetime.datetime.now(datetime.timezone.utc)
            closest_value = None
            closest_time_diff = datetime.timedelta.max
            
            for entry in property_data['values']:
                if 'validTime' in entry and 'value' in entry:
                    # Parse the time range
                    time_str = entry['validTime'].split('/')[0]
                    try:
                        entry_time = datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        time_diff = abs(now - entry_time)
                        
                        if time_diff < closest_time_diff:
                            closest_time_diff = time_diff
                            closest_value = entry['value']
                    except (ValueError, TypeError):
                        continue
            
            if closest_value is not None:
                return closest_value, property_data.get('uom', '')
        
        return None, None
    
    def _get_coordinates_for_grid(self, office: str, grid_x: int, grid_y: int) -> Tuple[Optional[float], Optional[float]]:
        """
        Get the coordinates for a NWS grid point.
        
        Args:
            office: NWS office code
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate
            
        Returns:
            Tuple of (lat, lon) or (None, None) if not available
        """
        # This is a simplified approach - in production you would query the NWS API
        # to get the exact coordinates for each grid point
        
        # Rough mapping for AKQ (Wakefield, VA) office grid
        if office == "AKQ":
            # These are approximate values - real implementation would use NWS API
            base_lat = 36.5
            base_lon = -77.5
            lat_step = 0.025
            lon_step = 0.025
            
            lat = base_lat + (grid_y * lat_step)
            lon = base_lon + (grid_x * lon_step)
            
            return lat, lon
        
        return None, None
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch weather data for the Hampton Roads region.
        
        Returns:
            List of dictionaries containing the data
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        
        # Check if we need to fetch (respect refresh interval)
        if now - self.last_fetch < self.refresh_interval:
            logger.debug(f"Skipping fetch, last fetch was {now - self.last_fetch} ago")
            return []
        
        readings = []
        
        # Fetch data for each pre-defined Hampton Roads point
        for office, grid_x, grid_y, locality in self.hampton_roads_points:
            try:
                weather_data = self._fetch_weather_data(office, grid_x, grid_y)
                if not weather_data:
                    continue
                
                # Get coordinates for this grid point
                lat, lon = self._get_coordinates_for_grid(office, grid_x, grid_y)
                if lat is None or lon is None:
                    # Try to extract from weather data
                    if 'geometry' in weather_data and 'coordinates' in weather_data['geometry']:
                        # GeoJSON is [lon, lat]
                        lon, lat = weather_data['geometry']['coordinates']
                
                if lat is None or lon is None:
                    logger.warning(f"Could not determine coordinates for grid {office}/{grid_x},{grid_y}")
                    continue
                
                # Process each weather type
                for weather_type in self.weather_types:
                    value, unit = self._extract_weather_value(weather_data, weather_type)
                    if value is None:
                        continue
                    
                    # Create reading object
                    stream_id = f"weather_{weather_type}_{locality}"
                    reading = {
                        "stream_id": stream_id,
                        "value": value,
                        "timestamp": now_iso,
                        "coordinates": (lat, lon),
                        "locality": locality,
                        "source_url": f"{NWS_API_BASE}gridpoints/{office}/{grid_x},{grid_y}",
                        "additional_metadata": {
                            "weather_type": weather_type,
                            "unit": unit,
                            "office": office,
                            "grid_x": grid_x,
                            "grid_y": grid_y
                        }
                    }
                    
                    # Update unit for this specific reading
                    self.unit = unit
                    
                    readings.append(reading)
            
            except Exception as e:
                logger.error(f"Error processing weather data for {locality}: {e}", exc_info=True)
        
        # Update last fetch time
        self.last_fetch = now
        
        return readings
