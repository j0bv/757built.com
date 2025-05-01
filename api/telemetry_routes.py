"""
API routes for the 757Built telemetry data visualization.

This module provides the API endpoints for accessing telemetry data
collected from various sources in the Hampton Roads region.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for telemetry routes
telemetry_bp = Blueprint('telemetry', __name__, url_prefix='/api/telemetry')

# Helper to access graph database
def get_graph_client():
    """Get the graph database client from the Flask app context."""
    if hasattr(current_app, 'graph_client'):
        return current_app.graph_client
    return None

# Helper to access storage client
def get_storage_client():
    """Get the storage client from the Flask app context."""
    if hasattr(current_app, 'storage_client'):
        return current_app.storage_client
    return None

@telemetry_bp.route('/streams', methods=['GET'])
def list_streams():
    """
    Get a list of all available telemetry streams.
    
    Query parameters:
    - type: Filter by metric type (e.g., traffic, weather)
    - locality: Filter by locality (e.g., NORFOLK)
    
    Returns:
        JSON response with list of available streams
    """
    graph_client = get_graph_client()
    if not graph_client:
        return jsonify({
            'error': 'Graph database client not available',
            'status': 'error'
        }), 500
    
    # Get filter parameters
    metric_type = request.args.get('type')
    locality = request.args.get('locality')
    
    # Build query filters
    filters = {
        'node_type': 'telemetry_stream'
    }
    
    if metric_type:
        filters['metric'] = metric_type
    
    # Query the database
    try:
        streams = graph_client.get_nodes(filters)
        
        # If locality filter is provided, we need to filter streams
        # based on their relationship to localities
        if locality and streams:
            locality = locality.upper()
            filtered_streams = []
            
            for stream in streams:
                # Check if this stream has readings in the specified locality
                # This is a simplified approach - in production, you would use
                # a more efficient graph query
                readings = graph_client.get_edges(
                    source_id=stream['id'],
                    edge_type='contains'
                )
                
                for reading_edge in readings:
                    reading_id = reading_edge['target_id']
                    reading = graph_client.get_node(reading_id)
                    
                    # Check if reading is connected to the requested locality
                    if reading:
                        locality_edges = graph_client.get_edges(
                            source_id=reading_id,
                            edge_type='located_in'
                        )
                        
                        for locality_edge in locality_edges:
                            locality_node = graph_client.get_node(locality_edge['target_id'])
                            if locality_node and locality_node.get('name') == locality:
                                filtered_streams.append(stream)
                                break
            
            streams = filtered_streams
        
        # Format the response
        result = {
            'streams': streams,
            'count': len(streams),
            'status': 'success'
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving telemetry streams: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Error retrieving telemetry streams: {str(e)}",
            'status': 'error'
        }), 500

@telemetry_bp.route('/<stream_id>', methods=['GET'])
def get_stream_data(stream_id):
    """
    Get telemetry data for a specific stream.
    
    Query parameters:
    - from: Start time (ISO format or relative like -7d, -24h)
    - to: End time (ISO format, default: now)
    - resolution: Data resolution (raw, hourly, daily)
    
    Returns:
        JSON response with time series data
    """
    graph_client = get_graph_client()
    storage_client = get_storage_client()
    
    if not graph_client:
        return jsonify({
            'error': 'Graph database client not available',
            'status': 'error'
        }), 500
    
    # Process time parameters
    from_time_str = request.args.get('from', '-24h')
    to_time_str = request.args.get('to')
    resolution = request.args.get('resolution', 'raw')
    
    # Parse the from_time
    from_time = None
    if from_time_str.startswith('-'):
        # Relative time
        if from_time_str.endswith('d'):
            days = int(from_time_str[1:-1])
            from_time = datetime.now() - timedelta(days=days)
        elif from_time_str.endswith('h'):
            hours = int(from_time_str[1:-1])
            from_time = datetime.now() - timedelta(hours=hours)
        elif from_time_str.endswith('m'):
            minutes = int(from_time_str[1:-1])
            from_time = datetime.now() - timedelta(minutes=minutes)
    else:
        # Absolute time
        try:
            from_time = datetime.fromisoformat(from_time_str.replace('Z', '+00:00'))
        except ValueError:
            # Default to last 24 hours if parsing fails
            from_time = datetime.now() - timedelta(hours=24)
    
    # Parse the to_time
    to_time = None
    if to_time_str:
        try:
            to_time = datetime.fromisoformat(to_time_str.replace('Z', '+00:00'))
        except ValueError:
            to_time = datetime.now()
    else:
        to_time = datetime.now()
    
    # Format times for comparison
    from_time_str = from_time.isoformat()
    to_time_str = to_time.isoformat()
    
    try:
        # Get the stream
        stream = graph_client.get_node(stream_id, node_type='telemetry_stream')
        if not stream:
            return jsonify({
                'error': f"Stream not found: {stream_id}",
                'status': 'error'
            }), 404
        
        # Get readings for this stream
        reading_edges = graph_client.get_edges(
            source_id=stream_id,
            edge_type='contains'
        )
        
        readings = []
        
        for edge in reading_edges:
            reading_id = edge['target_id']
            reading = graph_client.get_node(reading_id)
            
            if reading and 'timestamp' in reading:
                reading_time = reading['timestamp']
                
                # Check if reading is within the requested time range
                if from_time_str <= reading_time <= to_time_str:
                    # Load full data if available
                    data_location = reading.get('data_location')
                    if data_location:
                        if data_location.startswith('Qm'):  # IPFS hash
                            if storage_client:
                                try:
                                    data = storage_client.get(data_location)
                                    reading['full_data'] = data
                                except Exception as e:
                                    logger.warning(f"Could not retrieve IPFS data for {data_location}: {e}")
                        else:  # Local file path
                            try:
                                with open(data_location, 'r') as f:
                                    reading['full_data'] = json.load(f)
                            except Exception as e:
                                logger.warning(f"Could not read local file {data_location}: {e}")
                    
                    readings.append(reading)
        
        # Sort readings by timestamp
        readings.sort(key=lambda r: r.get('timestamp', ''))
        
        # Apply resolution (downsampling)
        if resolution != 'raw':
            readings = self._apply_resolution(readings, resolution)
        
        # Format the response
        result = {
            'stream_id': stream_id,
            'metric': stream.get('metric'),
            'unit': stream.get('unit'),
            'readings': readings,
            'count': len(readings),
            'from': from_time_str,
            'to': to_time_str,
            'resolution': resolution,
            'status': 'success'
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving telemetry data: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Error retrieving telemetry data: {str(e)}",
            'status': 'error'
        }), 500

def _apply_resolution(readings, resolution):
    """
    Downsample readings to the requested resolution.
    
    Args:
        readings: List of reading objects
        resolution: Target resolution (hourly, daily)
        
    Returns:
        Downsampled list of readings
    """
    if not readings:
        return []
    
    # Group readings by time bucket
    buckets = {}
    
    for reading in readings:
        timestamp = reading.get('timestamp')
        if not timestamp:
            continue
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Create bucket key based on resolution
            if resolution == 'hourly':
                bucket_key = dt.strftime('%Y-%m-%d %H:00:00')
            elif resolution == 'daily':
                bucket_key = dt.strftime('%Y-%m-%d 00:00:00')
            else:
                # Unknown resolution, return as is
                return readings
            
            # Add to bucket
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            
            buckets[bucket_key].append(reading)
        
        except ValueError:
            # Skip readings with invalid timestamps
            continue
    
    # Aggregate each bucket
    result = []
    
    for bucket_key, bucket_readings in buckets.items():
        # Average the values
        total_value = sum(r.get('value', 0) for r in bucket_readings)
        average_value = total_value / len(bucket_readings)
        
        # Create aggregated reading
        aggregated = {
            'timestamp': bucket_key,
            'value': average_value,
            'count': len(bucket_readings),
            'min': min(r.get('value', 0) for r in bucket_readings),
            'max': max(r.get('value', 0) for r in bucket_readings),
            # Copy other attributes from the first reading
            'unit': bucket_readings[0].get('unit'),
            'coordinates': bucket_readings[0].get('coordinates')
        }
        
        result.append(aggregated)
    
    # Sort by timestamp
    result.sort(key=lambda r: r.get('timestamp', ''))
    
    return result

@telemetry_bp.route('/map-data', methods=['GET'])
def get_map_data():
    """
    Get telemetry data formatted for map visualization.
    
    Query parameters:
    - type: Filter by metric type (e.g., traffic, weather)
    - locality: Filter by locality (e.g., NORFOLK)
    
    Returns:
        GeoJSON response with telemetry points
    """
    graph_client = get_graph_client()
    if not graph_client:
        return jsonify({
            'error': 'Graph database client not available',
            'status': 'error'
        }), 500
    
    # Get filter parameters
    metric_type = request.args.get('type')
    locality = request.args.get('locality')
    
    try:
        # Build query for telemetry readings
        filters = {
            'node_type': 'telemetry_reading'
        }
        
        # Query the database for readings
        readings = graph_client.get_nodes(filters)
        
        # Filter by metric type and locality if provided
        if metric_type or locality:
            filtered_readings = []
            
            for reading in readings:
                # Check metric type
                if metric_type:
                    # Get parent stream
                    stream_edges = graph_client.get_edges(
                        target_id=reading['id'],
                        edge_type='contains'
                    )
                    
                    if not stream_edges:
                        continue
                    
                    stream_id = stream_edges[0]['source_id']
                    stream = graph_client.get_node(stream_id)
                    
                    if not stream or stream.get('metric') != metric_type:
                        continue
                
                # Check locality
                if locality:
                    locality = locality.upper()
                    
                    # Check if reading is connected to the requested locality
                    locality_edges = graph_client.get_edges(
                        source_id=reading['id'],
                        edge_type='located_in'
                    )
                    
                    if not locality_edges:
                        continue
                    
                    locality_node = graph_client.get_node(locality_edges[0]['target_id'])
                    if not locality_node or locality_node.get('name') != locality:
                        continue
                
                filtered_readings.append(reading)
            
            readings = filtered_readings
        
        # Convert to GeoJSON
        features = []
        
        for reading in readings:
            # Check for coordinates
            lat = reading.get('lat')
            lon = reading.get('lng')
            
            if lat is None or lon is None:
                continue
            
            # Create GeoJSON feature
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lon, lat]  # GeoJSON uses [lon, lat]
                },
                'properties': {
                    'id': reading.get('id'),
                    'value': reading.get('value'),
                    'unit': reading.get('unit'),
                    'timestamp': reading.get('timestamp'),
                    'stream_id': reading.get('stream_id')
                }
            }
            
            features.append(feature)
        
        # Create GeoJSON response
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return jsonify(geojson)
    
    except Exception as e:
        logger.error(f"Error retrieving map data: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Error retrieving map data: {str(e)}",
            'status': 'error'
        }), 500

def init_app(app):
    """
    Initialize the telemetry blueprint with a Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(telemetry_bp)
