"""Storage API routes for the distributed storage system.

This module provides Flask routes for file storage, retrieval, and replication
across the distributed storage network.
"""

import os
import json
import time
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

# Import from parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ipfs_storage.distributed_storage import DistributedStorage

# Create blueprint
storage_api = Blueprint('storage_api', __name__, url_prefix='/api/storage')

# Initialize storage on first request
storage_instance = None

def get_storage():
    """Get or create the distributed storage instance."""
    global storage_instance
    if storage_instance is None:
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        storage_path = current_app.config.get('STORAGE_PATH', './temp_storage')
        replication = current_app.config.get('REPLICATION_FACTOR', 2)
        capacity = current_app.config.get('STORAGE_CAPACITY_GB', 50.0)
        
        storage_instance = DistributedStorage(
            redis_url=redis_url,
            local_storage_path=storage_path,
            replication_factor=replication,
            local_storage_capacity_gb=capacity
        )
    return storage_instance

@storage_api.route('/status', methods=['GET'])
def storage_status():
    """Get status of the local storage node."""
    storage = get_storage()
    
    # Get node info from Redis
    node_info = json.loads(storage.redis_client.hget(
        storage.storage_nodes_key, 
        storage.node_id
    ))
    
    # Count files stored on this node
    all_files = storage.redis_client.hgetall("files")
    local_files = 0
    for _, file_info_json in all_files.items():
        file_info_json = file_info_json.decode('utf-8') if isinstance(file_info_json, bytes) else file_info_json
        try:
            file_info = json.loads(file_info_json)
            if any(node["node_id"] == storage.node_id for node in file_info.get("storage_nodes", [])):
                local_files += 1
        except:
            pass
    
    # Get active workers
    active_workers = storage.redis_client.smembers("active_workers")
    active_workers = [w.decode('utf-8') if isinstance(w, bytes) else w for w in active_workers]
    
    # Get storage nodes
    storage_nodes = storage.redis_client.hgetall(storage.storage_nodes_key)
    storage_nodes = {
        k.decode('utf-8') if isinstance(k, bytes) else k: 
        json.loads(v.decode('utf-8') if isinstance(v, bytes) else v)
        for k, v in storage_nodes.items()
    }
    
    return jsonify({
        "node_id": storage.node_id,
        "capacity_gb": node_info["capacity_gb"],
        "used_gb": node_info["used_gb"],
        "free_gb": node_info["capacity_gb"] - node_info["used_gb"],
        "storage_path": node_info["path"],
        "local_files": local_files,
        "active_workers": len(active_workers),
        "storage_nodes": len(storage_nodes),
    })

@storage_api.route('/store', methods=['POST'])
def store_file():
    """Store a file in the distributed storage system."""
    storage = get_storage()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
        
    # Get optional parameters
    file_id = request.form.get('file_id')
    replicate = request.form.get('replicate', 'true').lower() == 'true'
    metadata = request.form.get('metadata')
    if metadata:
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {"description": metadata}
    else:
        metadata = {}
        
    # Save the file temporarily
    filename = secure_filename(file.filename)
    temp_dir = Path(current_app.config.get('TEMP_DIR', '/tmp'))
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / f"{int(time.time())}_{filename}"
    
    file.save(temp_path)
    
    try:
        # Store in distributed storage
        result = storage.store_file(temp_path, metadata, replicate)
        
        # If explicit file_id was provided, record the mapping
        if file_id and file_id != result["file_id"]:
            storage.redis_client.hset("file_id_mapping", file_id, result["file_id"])
            
        return jsonify({
            "status": "success",
            "file_id": result["file_id"],
            "original_name": result["original_name"],
            "size_bytes": result["size_bytes"],
            "path": next((node["path"] for node in result["storage_nodes"] 
                         if node["node_id"] == storage.node_id), None),
            "ipfs_hash": result.get("ipfs_hash"),
            "ipfs_status": result.get("ipfs_status")
        })
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()

@storage_api.route('/fetch/<file_id>', methods=['GET'])
def fetch_file(file_id):
    """Fetch a file from the distributed storage system."""
    storage = get_storage()
    
    # Check if this is a mapped ID
    mapped_id = storage.redis_client.hget("file_id_mapping", file_id)
    if mapped_id:
        file_id = mapped_id.decode('utf-8') if isinstance(mapped_id, bytes) else mapped_id
    
    # Try to get the file
    file_path = storage.get_file(file_id)
    if not file_path:
        return jsonify({"error": f"File {file_id} not found"}), 404
        
    # Get the file info for the original filename
    file_info = json.loads(storage.redis_client.hget("files", file_id))
    original_name = file_info.get("original_name", file_id)
    
    # Send the file
    return send_file(
        file_path,
        as_attachment=True,
        download_name=original_name,
    )

@storage_api.route('/info/<file_id>', methods=['GET'])
def file_info(file_id):
    """Get information about a file in the distributed storage system."""
    storage = get_storage()
    
    # Check if this is a mapped ID
    mapped_id = storage.redis_client.hget("file_id_mapping", file_id)
    if mapped_id:
        file_id = mapped_id.decode('utf-8') if isinstance(mapped_id, bytes) else mapped_id
    
    # Get the file info
    file_info_json = storage.redis_client.hget("files", file_id)
    if not file_info_json:
        return jsonify({"error": f"File {file_id} not found"}), 404
        
    file_info = json.loads(file_info_json)
    
    # Remove internal paths for security
    for node in file_info.get("storage_nodes", []):
        if "path" in node:
            del node["path"]
            
    return jsonify(file_info)

@storage_api.route('/list', methods=['GET'])
def list_files():
    """List files in the distributed storage system."""
    storage = get_storage()
    
    # Get filtering parameters
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    node_id = request.args.get('node_id')
    ipfs_status = request.args.get('ipfs_status')
    
    # Get all files
    all_files = storage.redis_client.hgetall("files")
    
    # Process and filter files
    files = []
    for file_id, file_info_json in all_files.items():
        file_id = file_id.decode('utf-8') if isinstance(file_id, bytes) else file_id
        file_info_json = file_info_json.decode('utf-8') if isinstance(file_info_json, bytes) else file_info_json
        
        try:
            file_info = json.loads(file_info_json)
            
            # Apply filters
            if node_id and not any(node["node_id"] == node_id for node in file_info.get("storage_nodes", [])):
                continue
                
            if ipfs_status and file_info.get("ipfs_status") != ipfs_status:
                continue
                
            # Add to results (without internal paths)
            file_data = {
                "file_id": file_id,
                "original_name": file_info.get("original_name"),
                "size_bytes": file_info.get("size_bytes"),
                "created_at": file_info.get("created_at"),
                "ipfs_status": file_info.get("ipfs_status"),
                "ipfs_hash": file_info.get("ipfs_hash"),
                "storage_node_count": len(file_info.get("storage_nodes", []))
            }
            files.append(file_data)
        except:
            pass
            
    # Sort by creation time (newest first)
    files.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    
    # Apply pagination
    paginated = files[offset:offset+limit]
    
    return jsonify({
        "total": len(files),
        "offset": offset,
        "limit": limit,
        "files": paginated
    })

@storage_api.route('/retry', methods=['POST'])
def retry_ipfs():
    """Retry uploading pending files to IPFS."""
    storage = get_storage()
    
    # Get limit parameter
    limit = int(request.args.get('limit', 20))
    
    # Retry uploads
    storage.retry_ipfs_uploads(limit=limit)
    
    return jsonify({
        "status": "success",
        "message": f"Retried up to {limit} IPFS uploads"
    })

@storage_api.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up old files that have been successfully stored in IPFS."""
    storage = get_storage()
    
    # Get max age parameter
    max_age_days = int(request.args.get('max_age_days', 30))
    
    # Run cleanup
    storage.cleanup_old_files(max_age_days=max_age_days)
    
    return jsonify({
        "status": "success",
        "message": f"Cleaned up files older than {max_age_days} days"
    }) 