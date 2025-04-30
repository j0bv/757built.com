"""Distributed temporary storage pool for 757Built documents.

This system manages document storage across multiple nodes, ensuring files
are stored redundantly while waiting for IPFS confirmation.
"""

import os
import json
import shutil
import logging
import time
import redis
import ipfshttpclient
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DistributedStorage:
    def __init__(self, redis_url: str = "redis://localhost:6379/0", 
                 local_storage_path: str = "./temp_storage",
                 replication_factor: int = 2,
                 storage_nodes_key: str = "storage_nodes",
                 local_storage_capacity_gb: float = 50.0):
        """Initialize distributed storage manager.
        
        Args:
            redis_url: Redis connection string
            local_storage_path: Local path for temporary storage
            replication_factor: Number of copies to maintain across nodes
            storage_nodes_key: Redis key for storage node registry
            local_storage_capacity_gb: Storage capacity in GB for this node
        """
        self.redis_client = redis.from_url(redis_url)
        self.storage_path = Path(local_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.replication_factor = replication_factor
        self.storage_nodes_key = storage_nodes_key
        self.capacity_gb = local_storage_capacity_gb
        
        # Setup IPFS client
        try:
            self.ipfs_client = ipfshttpclient.connect()
            logger.info("Connected to local IPFS daemon")
        except Exception as e:
            logger.warning(f"Could not connect to IPFS daemon: {e}")
            self.ipfs_client = None
            
        # Register this node as a storage provider
        self._register_storage_node()
        
    def _register_storage_node(self):
        """Register this node as a storage provider in Redis."""
        import socket
        node_id = f"{socket.gethostname()}_{os.getpid()}"
        
        node_info = {
            "path": str(self.storage_path),
            "capacity_gb": self.capacity_gb,
            "used_gb": self._get_local_usage(),
            "last_updated": time.time(),
            "endpoint": self._get_node_endpoint()
        }
        
        self.redis_client.hset(self.storage_nodes_key, node_id, json.dumps(node_info))
        self.node_id = node_id
        logger.info(f"Registered storage node {node_id}")
        
    def _get_node_endpoint(self):
        """Get network endpoint for this node."""
        import socket
        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
            return f"http://{ip}:5000/storage"
        except:
            return None
        
    def _get_local_usage(self):
        """Get storage usage in GB."""
        total, used, free = shutil.disk_usage(self.storage_path)
        return used / (1024 * 1024 * 1024)  # Convert to GB
        
    def _update_usage(self):
        """Update storage usage information in Redis."""
        if not self.redis_client.hexists(self.storage_nodes_key, self.node_id):
            self._register_storage_node()
            return
            
        node_info = json.loads(self.redis_client.hget(self.storage_nodes_key, self.node_id))
        node_info["used_gb"] = self._get_local_usage()
        node_info["last_updated"] = time.time()
        
        self.redis_client.hset(self.storage_nodes_key, self.node_id, json.dumps(node_info))
        
    def store_file(self, file_path: Union[str, Path], metadata: Optional[Dict] = None, 
                   replicate: bool = True) -> Dict:
        """Store a file in the distributed storage pool.
        
        Args:
            file_path: Path to the file to store
            metadata: Additional metadata to store with the file
            replicate: Whether to replicate across nodes
            
        Returns:
            Dict with storage information including file_id
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
            
        # Calculate file hash as ID
        file_hash = self._hash_file(file_path)
        file_id = f"file_{file_hash}"
        file_size = file_path.stat().st_size / (1024 * 1024 * 1024)  # Size in GB
        
        # Prepare storage record
        if metadata is None:
            metadata = {}
            
        storage_info = {
            "file_id": file_id,
            "original_name": file_path.name,
            "size_bytes": file_path.stat().st_size,
            "created_at": time.time(),
            "metadata": metadata,
            "storage_nodes": [],
            "ipfs_status": "pending",
            "ipfs_hash": None
        }
        
        # Store locally
        local_path = self.storage_path / file_id
        shutil.copy2(file_path, local_path)
        storage_info["storage_nodes"].append({
            "node_id": self.node_id,
            "path": str(local_path)
        })
        
        # Update local storage usage
        self._update_usage()
        
        # Store record in Redis
        self.redis_client.hset("files", file_id, json.dumps(storage_info))
        
        # If replication is requested, find other nodes and replicate
        if replicate and self.replication_factor > 1:
            self._replicate_file(file_id, file_path, self.replication_factor - 1)
            
        # Attempt IPFS storage if client available
        if self.ipfs_client:
            try:
                ipfs_hash = self.ipfs_client.add(str(local_path))["Hash"]
                storage_info["ipfs_hash"] = ipfs_hash
                storage_info["ipfs_status"] = "stored"
                self.redis_client.hset("files", file_id, json.dumps(storage_info))
                logger.info(f"Stored {file_id} on IPFS with hash {ipfs_hash}")
            except Exception as e:
                logger.error(f"Failed to store {file_id} on IPFS: {e}")
                # Queue for later retry
                self.redis_client.lpush("ipfs_retry_queue", file_id)
                
        return storage_info
    
    def _replicate_file(self, file_id: str, local_file: Path, copies: int):
        """Replicate a file to other storage nodes.
        
        Args:
            file_id: ID of the file to replicate
            local_file: Path to the local copy of the file
            copies: Number of additional copies to create
        """
        # Get all available storage nodes
        all_nodes = self.redis_client.hgetall(self.storage_nodes_key)
        if not all_nodes:
            logger.warning(f"No storage nodes available for replication of {file_id}")
            return
            
        # Filter out this node and nodes without enough space
        file_size_gb = local_file.stat().st_size / (1024 * 1024 * 1024)
        candidate_nodes = []
        
        for node_id, node_info_json in all_nodes.items():
            node_id = node_id.decode('utf-8') if isinstance(node_id, bytes) else node_id
            if node_id == self.node_id:
                continue
                
            node_info_json = node_info_json.decode('utf-8') if isinstance(node_info_json, bytes) else node_info_json
                
            try:
                node_info = json.loads(node_info_json)
                free_space = node_info["capacity_gb"] - node_info["used_gb"]
                
                if free_space >= file_size_gb and node_info.get("endpoint"):
                    candidate_nodes.append((node_id, node_info))
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing node info for {node_id}: {e}")
                
        if not candidate_nodes:
            logger.warning(f"No suitable nodes for replication of {file_id}")
            return
            
        # Randomly select nodes for replication
        selected_nodes = random.sample(candidate_nodes, min(copies, len(candidate_nodes)))
        
        # Get the current storage info
        storage_info = json.loads(self.redis_client.hget("files", file_id))
        
        # Replicate to each selected node
        import requests
        for node_id, node_info in selected_nodes:
            endpoint = node_info["endpoint"]
            if not endpoint:
                continue
                
            try:
                # Send file to the remote node
                with open(local_file, 'rb') as f:
                    response = requests.post(
                        f"{endpoint}/store",
                        files={'file': f},
                        data={'file_id': file_id, 'replicate': 'false'},
                        timeout=60
                    )
                    
                if response.status_code == 200:
                    result = response.json()
                    storage_info["storage_nodes"].append({
                        "node_id": node_id,
                        "path": result.get("path")
                    })
                    logger.info(f"Replicated {file_id} to node {node_id}")
                else:
                    logger.error(f"Failed to replicate to {node_id}: {response.text}")
            except Exception as e:
                logger.error(f"Error replicating to {node_id}: {e}")
                
        # Update storage record with new replicas
        self.redis_client.hset("files", file_id, json.dumps(storage_info))
    
    def retry_ipfs_uploads(self, limit: int = 10):
        """Retry uploading files to IPFS that failed earlier."""
        for _ in range(limit):
            file_id = self.redis_client.lpop("ipfs_retry_queue")
            if not file_id:
                break
                
            file_id = file_id.decode('utf-8') if isinstance(file_id, bytes) else file_id
            storage_info = json.loads(self.redis_client.hget("files", file_id))
            
            # Check if we have a local copy
            local_node = next((node for node in storage_info["storage_nodes"] 
                              if node["node_id"] == self.node_id), None)
                              
            if not local_node or not self.ipfs_client:
                # Put it back in the queue
                self.redis_client.rpush("ipfs_retry_queue", file_id)
                continue
                
            try:
                ipfs_hash = self.ipfs_client.add(local_node["path"])["Hash"]
                storage_info["ipfs_hash"] = ipfs_hash
                storage_info["ipfs_status"] = "stored"
                self.redis_client.hset("files", file_id, json.dumps(storage_info))
                logger.info(f"Retry successful: stored {file_id} on IPFS with hash {ipfs_hash}")
            except Exception as e:
                logger.error(f"Retry failed for {file_id}: {e}")
                # Put it back at the end of the queue
                self.redis_client.rpush("ipfs_retry_queue", file_id)
    
    def get_file(self, file_id: str) -> Optional[Path]:
        """Get a file from the distributed storage pool.
        
        Args:
            file_id: ID of the file to retrieve
            
        Returns:
            Path to the local copy of the file, or None if not found
        """
        if not self.redis_client.hexists("files", file_id):
            return None
            
        storage_info = json.loads(self.redis_client.hget("files", file_id))
        
        # Check if we have a local copy
        local_node = next((node for node in storage_info["storage_nodes"] 
                          if node["node_id"] == self.node_id), None)
                          
        if local_node:
            local_path = Path(local_node["path"])
            if local_path.exists():
                return local_path
                
        # Try to get from another node
        for node in storage_info["storage_nodes"]:
            if node["node_id"] == self.node_id:
                continue
                
            # Get node info to find its endpoint
            node_info_json = self.redis_client.hget(self.storage_nodes_key, node["node_id"])
            if not node_info_json:
                continue
                
            node_info_json = node_info_json.decode('utf-8') if isinstance(node_info_json, bytes) else node_info_json
            
            try:
                node_info = json.loads(node_info_json)
                endpoint = node_info.get("endpoint")
                
                if endpoint:
                    local_path = self._fetch_from_remote_node(file_id, endpoint)
                    if local_path:
                        return local_path
            except (json.JSONDecodeError, KeyError):
                continue
                
        # If IPFS hash exists, try to get from IPFS
        ipfs_hash = storage_info.get("ipfs_hash")
        if ipfs_hash and self.ipfs_client:
            try:
                local_path = self.storage_path / file_id
                self.ipfs_client.get(ipfs_hash, str(self.storage_path))
                
                # The file might be downloaded as the hash, so rename if needed
                ipfs_path = self.storage_path / ipfs_hash
                if ipfs_path.exists() and not local_path.exists():
                    ipfs_path.rename(local_path)
                    
                if local_path.exists():
                    # Update storage info to include this local copy
                    storage_info["storage_nodes"].append({
                        "node_id": self.node_id,
                        "path": str(local_path)
                    })
                    self.redis_client.hset("files", file_id, json.dumps(storage_info))
                    return local_path
            except Exception as e:
                logger.error(f"Failed to get {file_id} from IPFS: {e}")
                
        return None
        
    def _fetch_from_remote_node(self, file_id: str, endpoint: str) -> Optional[Path]:
        """Fetch a file from a remote storage node.
        
        Args:
            file_id: ID of the file to fetch
            endpoint: API endpoint of the remote node
            
        Returns:
            Path to the local copy if successful, None otherwise
        """
        import requests
        try:
            response = requests.get(
                f"{endpoint}/fetch/{file_id}",
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                local_path = self.storage_path / file_id
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                logger.info(f"Fetched {file_id} from remote node")
                
                # Update storage info to include this local copy
                storage_info = json.loads(self.redis_client.hget("files", file_id))
                storage_info["storage_nodes"].append({
                    "node_id": self.node_id,
                    "path": str(local_path)
                })
                self.redis_client.hset("files", file_id, json.dumps(storage_info))
                
                return local_path
        except Exception as e:
            logger.error(f"Error fetching {file_id} from remote: {e}")
            
        return None
        
    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
        
    def cleanup_old_files(self, max_age_days: int = 30):
        """Clean up files that have been successfully stored in IPFS.
        
        Args:
            max_age_days: Maximum age of files to keep locally
        """
        all_files = self.redis_client.hgetall("files")
        for file_id, storage_info_json in all_files.items():
            file_id = file_id.decode('utf-8') if isinstance(file_id, bytes) else file_id
            storage_info_json = storage_info_json.decode('utf-8') if isinstance(storage_info_json, bytes) else storage_info_json
            
            try:
                storage_info = json.loads(storage_info_json)
                
                # Skip files not successfully stored in IPFS
                if storage_info.get("ipfs_status") != "stored" or not storage_info.get("ipfs_hash"):
                    continue
                    
                # Check if file is old enough to delete
                age_days = (time.time() - storage_info.get("created_at", 0)) / (24 * 3600)
                if age_days < max_age_days:
                    continue
                    
                # Check if we have a local copy
                local_nodes = [node for node in storage_info["storage_nodes"] 
                              if node["node_id"] == self.node_id]
                              
                for local_node in local_nodes:
                    local_path = Path(local_node["path"])
                    if local_path.exists():
                        local_path.unlink()
                        logger.info(f"Cleaned up old file {file_id}")
                        
                # Update storage info to remove this node
                storage_info["storage_nodes"] = [node for node in storage_info["storage_nodes"] 
                                               if node["node_id"] != self.node_id]
                                               
                self.redis_client.hset("files", file_id, json.dumps(storage_info))
                
                # Update local storage usage
                self._update_usage()
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error processing file {file_id}: {e}") 