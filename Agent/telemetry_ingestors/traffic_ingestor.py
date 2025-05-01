"""
Traffic data ingestor for the 757Built platform.

This module fetches traffic data from the Virginia Department of Transportation's
public API and converts it to a format compatible with D3.js visualizations.
"""

import json
import logging
import requests
import datetime
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin

from .base_ingestor import BaseTelemetryIngestor, SEVEN_CITIES

logger = logging.getLogger(__name__)

# VDOT traffic API endpoint
VDOT_API_BASE = "https://www.511virginia.org/data/geojson/"
TRAFFIC_ENDPOINTS = {
    "incidents": "incidents.geojson",
    "cameras": "cameras.geojson",
    "signs": "signs.geojson",
    "counters": "counters.geojson",
}

class TrafficDataIngestor(BaseTelemetryIngestor):
    """Ingestor for Virginia DOT traffic data."""
    
    def __init__(self, 
                 graph_client=None, 
                 storage_client=None,
                 endpoints=None,
                 store_in_ipfs=True,
                 local_storage_path=None,
                 refresh_interval_minutes=15):
        """
        Initialize the traffic data ingestor.
        
        Args:
            graph_client: Graph database client
            storage_client: Storage client (IPFS or local)
            endpoints: List of endpoint names to fetch (defaults to all)
            store_in_ipfs: Whether to store data in IPFS
            local_storage_path: Path for local storage if not using IPFS
            refresh_interval_minutes: How often to fetch new data
        """
        super().__init__(
            graph_client=graph_client,
            storage_client=storage_client,
            metric_type="traffic",
            unit="count",
            data_license="CC-BY-4.0",  # VDOT typically uses CC-BY
            store_in_ipfs=store_in_ipfs,
            local_storage_path=local_storage_path
        )
        
        self.endpoints = endpoints or list(TRAFFIC_ENDPOINTS.keys())
        self.refresh_interval = datetime.timedelta(minutes=refresh_interval_minutes)
        self.last_fetch = {}  # Track last fetch time for each endpoint
    
    def _fetch_endpoint(self, endpoint: str) -> Optional[Dict]:
        """
        Fetch data from a specific VDOT endpoint.
        
        Args:
            endpoint: Name of the endpoint to fetch
            
        Returns:
            GeoJSON data or None if fetch failed
        """
        if endpoint not in TRAFFIC_ENDPOINTS:
            logger.error(f"Unknown endpoint: {endpoint}")
            return None
        
        url = urljoin(VDOT_API_BASE, TRAFFIC_ENDPOINTS[endpoint])
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None
    
    def _filter_by_hampton_roads(self, data: Dict) -> List[Dict]:
        """
        Filter GeoJSON features to only include those in the Hampton Roads region.
        
        Args:
            data: GeoJSON data
            
        Returns:
            List of features in Hampton Roads
        """
        if not data or 'features' not in data:
            return []
        
        hampton_roads_features = []
        
        for feature in data['features']:
            # Extract coordinates
            if feature.get('geometry') and feature['geometry'].get('coordinates'):
                coords = feature['geometry']['coordinates']
                
                # Handle different geometry types
                if feature['geometry']['type'] == 'Point':
                    # Point features (lon, lat order in GeoJSON)
                    lon, lat = coords
                    if self._is_in_hampton_roads(lat, lon):
                        # Determine locality based on coordinates
                        # This is a simplified approach - in production, you would use
                        # reverse geocoding or point-in-polygon with the Hampton Roads boundaries
                        feature['properties']['locality'] = self._get_nearest_locality(lat, lon)
                        hampton_roads_features.append(feature)
                
                # Add support for LineString and Polygon types if needed
        
        return hampton_roads_features
    
    def _get_nearest_locality(self, lat: float, lon: float) -> str:
        """
        Get the nearest Hampton Roads locality to the given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Name of the nearest locality
        """
        # In a real implementation, this would use a spatial database or polygon contains check
        # For this demo, we'll use a very simplified approach based on lat/lon ranges
        
        # This is a rough approximation - real implementation would use proper geo boundaries
        locality_centers = {
            "NORFOLK": (36.8508, -76.2859),
            "VIRGINIA BEACH": (36.8529, -75.9780),
            "CHESAPEAKE": (36.7682, -76.2875),
            "PORTSMOUTH": (36.8354, -76.2982),
            "SUFFOLK": (36.7282, -76.5836),
            "HAMPTON": (37.0299, -76.3452),
            "NEWPORT NEWS": (37.0871, -76.4343)
        }
        
        # Find the closest locality center
        min_distance = float('inf')
        nearest_locality = "NORFOLK"  # Default
        
        for locality, (loc_lat, loc_lon) in locality_centers.items():
            # Simple Euclidean distance (sufficient for small areas)
            distance = ((lat - loc_lat) ** 2 + (lon - loc_lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_locality = locality
        
        return nearest_locality
    
    def _extract_traffic_count(self, feature: Dict) -> Optional[int]:
        """
        Extract traffic count from a feature.
        
        Args:
            feature: GeoJSON feature
            
        Returns:
            Traffic count or None if not available
        """
        properties = feature.get('properties', {})
        
        # Different endpoints have different property names for counts
        count_fields = ['count', 'volume', 'vehicleCount', 'dailyCount', 'flowRate']
        
        for field in count_fields:
            if field in properties:
                try:
                    return int(properties[field])
                except (ValueError, TypeError):
                    pass
        
        # For incidents, we don't have a count, so return 1 (presence)
        if 'type' in properties and properties['type'] == 'incident':
            return 1
        
        # If no count is found, estimate based on congestion level
        if 'congestionLevel' in properties:
            congestion_level = properties['congestionLevel']
            if isinstance(congestion_level, str):
                if congestion_level.lower() == 'high':
                    return 100
                elif congestion_level.lower() == 'medium':
                    return 50
                elif congestion_level.lower() == 'low':
                    return 20
        
        return None
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch traffic data from all configured endpoints.
        
        Returns:
            List of dictionaries containing the data
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        
        readings = []
        
        for endpoint in self.endpoints:
            # Check if we need to fetch (respect refresh interval)
            last_fetch_time = self.last_fetch.get(endpoint)
            if last_fetch_time and now - last_fetch_time < self.refresh_interval:
                logger.debug(f"Skipping fetch for {endpoint}, last fetch was {now - last_fetch_time} ago")
                continue
            
            # Fetch and process data
            raw_data = self._fetch_endpoint(endpoint)
            if not raw_data:
                continue
            
            # Filter to Hampton Roads region
            hr_features = self._filter_by_hampton_roads(raw_data)
            logger.info(f"Found {len(hr_features)} {endpoint} features in Hampton Roads")
            
            # Process each feature
            for feature in hr_features:
                try:
                    # Extract coordinates (GeoJSON uses [lon, lat])
                    lon, lat = feature['geometry']['coordinates']
                    
                    # Get properties
                    properties = feature.get('properties', {})
                    
                    # Extract identifier
                    feature_id = properties.get('id')
                    if not feature_id:
                        # Generate an ID if none exists
                        feature_id = f"{endpoint}_{lon}_{lat}"
                    
                    # Get traffic count
                    count = self._extract_traffic_count(feature)
                    if count is None:
                        continue
                    
                    # Get locality
                    locality = properties.get('locality')
                    
                    # Prepare metadata (retain useful properties, exclude potentially PII)
                    safe_metadata = {}
                    for key, value in properties.items():
                        if key.lower() not in ['person', 'contact', 'phone', 'email', 'license_plate']:
                            safe_metadata[key] = value
                    
                    # Create reading object
                    reading = {
                        "stream_id": f"traffic_{endpoint}_{feature_id}",
                        "value": count,
                        "timestamp": now_iso,
                        "coordinates": (lat, lon),  # Convert to (lat, lon) for our system
                        "locality": locality,
                        "source_url": urljoin(VDOT_API_BASE, TRAFFIC_ENDPOINTS[endpoint]),
                        "additional_metadata": {
                            "endpoint": endpoint,
                            "type": properties.get('type', endpoint),
                            "description": properties.get('description', ''),
                            **safe_metadata
                        }
                    }
                    
                    readings.append(reading)
                
                except Exception as e:
                    logger.error(f"Error processing feature: {e}", exc_info=True)
            
            # Update last fetch time
            self.last_fetch[endpoint] = now
        
        return readings
