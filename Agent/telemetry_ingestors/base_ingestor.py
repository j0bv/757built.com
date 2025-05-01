"""
Base telemetry ingestor class for the 757Built platform.

This module provides the foundation for all telemetry data ingestors,
ensuring consistent data processing, validation, and storage.
"""

import os
import json
import logging
import hashlib
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from urllib.parse import urlparse

from graph_db.schema import (
    NodeType, 
    EdgeType, 
    NODE_VALUE, 
    NODE_UNIT, 
    NODE_SOURCE_URL,
    NODE_LICENSE,
    NODE_LAT,
    NODE_LON
)

logger = logging.getLogger(__name__)

# Hampton Roads boundaries (approximate)
HAMPTON_ROADS_BOUNDS = {
    "min_lat": 36.6,
    "max_lat": 37.3,
    "min_lon": -77.0,
    "max_lon": -75.9
}

# Seven Cities boundaries
SEVEN_CITIES = [
    "CHESAPEAKE", "HAMPTON", "NEWPORT NEWS", "NORFOLK", 
    "PORTSMOUTH", "SUFFOLK", "VIRGINIA BEACH"
]

class BaseTelemetryIngestor(ABC):
    """Base class for all telemetry data ingestors."""
    
    def __init__(self, 
                 graph_client=None, 
                 storage_client=None,
                 metric_type: str = "",
                 unit: str = "",
                 data_license: str = "CC0-1.0",
                 store_in_ipfs: bool = True,
                 local_storage_path: str = None):
        """
        Initialize the telemetry ingestor.
        
        Args:
            graph_client: Graph database client
            storage_client: Storage client (IPFS or local)
            metric_type: Type of metric being measured
            unit: Unit of measurement
            data_license: License of the data (must be open data license)
            store_in_ipfs: Whether to store data in IPFS (True) or local storage (False)
            local_storage_path: Path for local storage if not using IPFS
        """
        self.graph_client = graph_client
        self.storage_client = storage_client
        self.metric_type = metric_type
        self.unit = unit
        self.data_license = self._validate_license(data_license)
        self.store_in_ipfs = store_in_ipfs
        self.local_storage_path = local_storage_path or os.path.join(
            os.environ.get("DATA_DIR", "data"), 
            "telemetry",
            self.__class__.__name__.lower()
        )
        
        # Create local storage directory if it doesn't exist
        if not self.store_in_ipfs and not os.path.exists(self.local_storage_path):
            os.makedirs(self.local_storage_path, exist_ok=True)
    
    def _validate_license(self, license_id: str) -> str:
        """
        Validate that the license is an open data license.
        
        Args:
            license_id: SPDX license identifier
            
        Returns:
            Validated license ID
            
        Raises:
            ValueError: If license is not approved for open data
        """
        # List of approved open data licenses
        # See https://opendefinition.org/licenses/
        OPEN_DATA_LICENSES = [
            "CC0-1.0", "CC-BY-4.0", "ODC-BY-1.0", "ODbL-1.0", 
            "PDDL-1.0", "MIT", "Apache-2.0"
        ]
        
        if license_id not in OPEN_DATA_LICENSES:
            logger.warning(f"License {license_id} is not in approved open data licenses list.")
            # For now, we'll allow it but log a warning
            # In production, you might want to raise an error instead
        
        return license_id
    
    def _is_in_hampton_roads(self, lat: float, lon: float) -> bool:
        """
        Check if the coordinates are within the Hampton Roads region.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if coordinates are in Hampton Roads, False otherwise
        """
        return (HAMPTON_ROADS_BOUNDS["min_lat"] <= lat <= HAMPTON_ROADS_BOUNDS["max_lat"] and
                HAMPTON_ROADS_BOUNDS["min_lon"] <= lon <= HAMPTON_ROADS_BOUNDS["max_lon"])
    
    def _contains_pii(self, data: Union[str, Dict]) -> bool:
        """
        Check if the data contains personally identifiable information.
        
        Args:
            data: Data to check
            
        Returns:
            True if PII is detected, False otherwise
        """
        # Convert to string if it's a dict
        if isinstance(data, dict):
            data = json.dumps(data)
        
        # Simple pattern matching for common PII
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
        ]
        
        import re
        for pattern in pii_patterns:
            if re.search(pattern, data):
                return True
        
        return False
    
    def _store_data(self, data: Dict[str, Any], timestamp: str) -> str:
        """
        Store the data either in IPFS or local storage.
        
        Args:
            data: Data to store
            timestamp: ISO-8601 timestamp
            
        Returns:
            Data hash or file path
        """
        # Create a unique filename based on content and timestamp
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        if self.store_in_ipfs and self.storage_client:
            # Store in IPFS
            from io import BytesIO
            buffer = BytesIO(data_str.encode('utf-8'))
            result = self.storage_client.add(buffer)
            return result['Hash']
        else:
            # Store locally
            date_path = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y/%m/%d')
            full_path = os.path.join(self.local_storage_path, date_path)
            os.makedirs(full_path, exist_ok=True)
            
            file_path = os.path.join(full_path, f"{data_hash}.json")
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return file_path
    
    def process_reading(self, 
                       stream_id: str, 
                       value: float, 
                       timestamp: str,
                       coordinates: Tuple[float, float],
                       locality: str = None,
                       source_url: str = None,
                       additional_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a telemetry reading and store it in the graph database.
        
        Args:
            stream_id: Unique identifier for the telemetry stream
            value: Measurement value
            timestamp: ISO-8601 timestamp
            coordinates: (lat, lon) coordinates
            locality: Name of the locality (e.g., "NORFOLK")
            source_url: URL of the data source
            additional_metadata: Additional metadata for the reading
            
        Returns:
            Dictionary containing the processed data
        """
        lat, lon = coordinates
        
        # Validate coordinates are in Hampton Roads
        if not self._is_in_hampton_roads(lat, lon):
            logger.warning(f"Coordinates ({lat}, {lon}) are outside Hampton Roads region")
            return None
        
        # Create the reading data
        reading_data = {
            "stream_id": stream_id,
            "value": value,
            "timestamp": timestamp,
            "coordinates": {"lat": lat, "lon": lon},
            "metric": self.metric_type,
            "unit": self.unit,
            "license": self.data_license,
        }
        
        # Add locality if provided
        if locality:
            reading_data["locality"] = locality.upper()
        
        # Add source URL if provided
        if source_url:
            parsed_url = urlparse(source_url)
            if not (parsed_url.scheme and parsed_url.netloc):
                logger.warning(f"Invalid source URL: {source_url}")
            else:
                reading_data["source_url"] = source_url
        
        # Add additional metadata
        if additional_metadata:
            if self._contains_pii(additional_metadata):
                logger.warning(f"PII detected in metadata for stream {stream_id}, removing")
                # Filter out PII fields (would need more sophisticated detection in production)
            else:
                reading_data.update(additional_metadata)
        
        # Store the data
        data_location = self._store_data(reading_data, timestamp)
        reading_data["data_location"] = data_location
        
        # Add to graph database if client is provided
        if self.graph_client:
            # Create or get stream node
            stream_node = self.graph_client.get_or_create_node(
                node_type=NodeType.TELEMETRY_STREAM,
                properties={"id": stream_id, "metric": self.metric_type, "unit": self.unit}
            )
            
            # Create reading node
            reading_node = self.graph_client.create_node(
                node_type=NodeType.TELEMETRY_READING,
                properties={
                    "id": f"{stream_id}_{timestamp}",
                    NODE_VALUE: value,
                    NODE_UNIT: self.unit,
                    NODE_LAT: lat,
                    NODE_LON: lon,
                    "timestamp": timestamp,
                    NODE_SOURCE_URL: source_url,
                    NODE_LICENSE: self.data_license,
                    "data_location": data_location
                }
            )
            
            # Link reading to stream
            self.graph_client.create_edge(
                source_id=stream_node["id"],
                target_id=reading_node["id"],
                edge_type=EdgeType.CONTAINS,
                properties={"timestamp": timestamp}
            )
            
            # Link to locality if provided
            if locality:
                locality_node = self.graph_client.get_or_create_node(
                    node_type=NodeType.LOCALITY,
                    properties={"name": locality.upper()}
                )
                
                self.graph_client.create_edge(
                    source_id=reading_node["id"],
                    target_id=locality_node["id"],
                    edge_type=EdgeType.LOCATED_IN,
                    properties={"timestamp": timestamp}
                )
        
        return reading_data
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch telemetry data from the source.
        
        Returns:
            List of dictionaries containing the data
        """
        pass
    
    def run(self) -> int:
        """
        Run the ingestor to fetch and process telemetry data.
        
        Returns:
            Number of readings processed
        """
        try:
            logger.info(f"Running {self.__class__.__name__} ingestor")
            
            readings = self.fetch_data()
            if not readings:
                logger.warning(f"No readings returned from {self.__class__.__name__}")
                return 0
            
            processed_count = 0
            for reading in readings:
                try:
                    result = self.process_reading(**reading)
                    if result:
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing reading: {e}", exc_info=True)
            
            logger.info(f"Processed {processed_count} readings from {self.__class__.__name__}")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error running {self.__class__.__name__} ingestor: {e}", exc_info=True)
            return 0
