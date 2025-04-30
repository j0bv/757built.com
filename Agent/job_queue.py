#!/usr/bin/env python3
"""Enhanced job queue system with support for distributed storage and compute resources.
Uses Redis for coordination between nodes in the processing cluster.
"""
import os
import json
import logging
import time
import redis
import uuid
import socket
import shutil
from typing import Optional, Dict, Any
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("DOC_QUEUE_KEY", "doc_queue")

logger = logging.getLogger("job_queue")

_redis = redis.Redis.from_url(REDIS_URL)


class DistributedJobQueue:
    def __init__(self, redis_url="redis://localhost:6379/0", queue_name="document_queue", 
                 results_key="processing_results", worker_set="active_workers",
                 storage_nodes_key="storage_nodes"):
        """Initialize a distributed job queue using Redis.
        
        Args:
            redis_url: Redis connection string
            queue_name: Name of the processing queue
            results_key: Hash key for storing processing results
            worker_set: Set containing active worker IDs
            storage_nodes_key: Hash mapping storage node IDs to their capacity/usage info
        """
        self.redis_client = redis.from_url(redis_url)
        self.queue_name = queue_name
        self.results_key = results_key
        self.worker_set = worker_set
        self.storage_nodes_key = storage_nodes_key
        self.hostname = socket.gethostname()
        self.node_id = f"{self.hostname}_{uuid.uuid4().hex[:8]}"
    
    def register_worker(self, worker_id=None, capabilities=None):
        """Register this node as an active worker with optional capabilities info."""
        if worker_id is None:
            worker_id = self.node_id
            
        if capabilities is None:
            capabilities = {
                "cpu_count": os.cpu_count(),
                "gpu_available": self._check_gpu_available(),
                "registered_at": datetime.now().isoformat()
            }
            
        self.redis_client.sadd(self.worker_set, worker_id)
        self.redis_client.hset(f"worker:{worker_id}", mapping={
            "last_heartbeat": time.time(),
            "capabilities": json.dumps(capabilities)
        })
        return worker_id
        
    def register_storage_node(self, storage_path, capacity_gb, node_id=None):
        """Register this node as a storage provider."""
        if node_id is None:
            node_id = self.node_id
            
        node_info = {
            "path": storage_path,
            "capacity_gb": capacity_gb,
            "used_gb": self._get_used_storage(storage_path),
            "last_updated": time.time()
        }
        
        self.redis_client.hset(self.storage_nodes_key, node_id, json.dumps(node_info))
        return node_id
        
    def update_storage_usage(self, storage_path, node_id=None):
        """Update storage usage information."""
        if node_id is None:
            node_id = self.node_id
            
        if not self.redis_client.hexists(self.storage_nodes_key, node_id):
            raise ValueError(f"Storage node {node_id} not registered")
            
        node_info = json.loads(self.redis_client.hget(self.storage_nodes_key, node_id))
        node_info["used_gb"] = self._get_used_storage(storage_path)
        node_info["last_updated"] = time.time()
        
        self.redis_client.hset(self.storage_nodes_key, node_id, json.dumps(node_info))
        
    def add_job(self, document_path, metadata=None):
        """Add a document processing job to the queue."""
        if metadata is None:
            metadata = {}
            
        job_data = {
            "document_path": document_path,
            "submitted_at": time.time(),
            "submitted_by": self.node_id,
            "status": "pending",
            "metadata": metadata
        }
        
        job_id = f"job_{uuid.uuid4().hex}"
        self.redis_client.hset(f"job:{job_id}", mapping=job_data)
        self.redis_client.lpush(self.queue_name, job_id)
        return job_id
        
    def get_job(self, timeout=0):
        """Get the next job from the queue with optional timeout."""
        result = self.redis_client.brpop(self.queue_name, timeout)
        if result is None:
            return None
            
        _, job_id = result
        job_id = job_id.decode('utf-8') if isinstance(job_id, bytes) else job_id
        
        job_data = self.redis_client.hgetall(f"job:{job_id}")
        if not job_data:
            return None
            
        # Convert byte keys/values to strings
        job_data = {k.decode('utf-8') if isinstance(k, bytes) else k: 
                   v.decode('utf-8') if isinstance(v, bytes) else v 
                   for k, v in job_data.items()}
        
        # Update job status
        self.redis_client.hset(f"job:{job_id}", "status", "processing")
        self.redis_client.hset(f"job:{job_id}", "worker", self.node_id)
        self.redis_client.hset(f"job:{job_id}", "processing_started", time.time())
        
        job_data.update({"job_id": job_id})
        return job_data
        
    def complete_job(self, job_id, result):
        """Mark a job as completed with its results."""
        self.redis_client.hset(f"job:{job_id}", "status", "completed")
        self.redis_client.hset(f"job:{job_id}", "completed_at", time.time())
        self.redis_client.hset(f"job:{job_id}", "result", json.dumps(result))
        
        # Also store in results collection for quick access
        self.redis_client.hset(self.results_key, job_id, json.dumps(result))
        
    def fail_job(self, job_id, error_message):
        """Mark a job as failed with error message."""
        self.redis_client.hset(f"job:{job_id}", "status", "failed")
        self.redis_client.hset(f"job:{job_id}", "failed_at", time.time())
        self.redis_client.hset(f"job:{job_id}", "error", error_message)
    
    def requeue_job(self, job_id):
        """Put a job back into the queue (for retries)."""
        self.redis_client.hset(f"job:{job_id}", "status", "pending")
        self.redis_client.hset(f"job:{job_id}", "retried_at", time.time())
        self.redis_client.lpush(self.queue_name, job_id)
        
    def get_best_storage_node(self, required_space_gb=1.0):
        """Find the best storage node with sufficient space."""
        all_nodes = self.redis_client.hgetall(self.storage_nodes_key)
        
        best_node = None
        best_free_space = -1
        
        for node_id, node_info_json in all_nodes.items():
            node_id = node_id.decode('utf-8') if isinstance(node_id, bytes) else node_id
            node_info_json = node_info_json.decode('utf-8') if isinstance(node_info_json, bytes) else node_info_json
            
            try:
                node_info = json.loads(node_info_json)
                free_space = node_info["capacity_gb"] - node_info["used_gb"]
                
                if free_space >= required_space_gb and free_space > best_free_space:
                    best_node = node_id
                    best_free_space = free_space
            except (json.JSONDecodeError, KeyError):
                continue
                
        if best_node:
            node_info = json.loads(self.redis_client.hget(self.storage_nodes_key, best_node))
            return {
                "node_id": best_node,
                "path": node_info["path"],
                "free_space_gb": best_free_space
            }
        return None
    
    def heartbeat(self):
        """Update the worker's heartbeat timestamp."""
        self.redis_client.hset(f"worker:{self.node_id}", "last_heartbeat", time.time())
        
    def _check_gpu_available(self):
        """Check if GPU is available on this node."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
            
    def _get_used_storage(self, path):
        """Get used storage in GB for the given path."""
        try:
            total, used, free = shutil.disk_usage(path)
            return used / (1024 * 1024 * 1024)  # Convert to GB
        except:
            return 0

# For backward compatibility
JobQueue = DistributedJobQueue
