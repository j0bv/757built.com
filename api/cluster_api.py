"""Cluster management API routes for the H100 cluster.

This module provides Flask routes for managing and monitoring the
distributed compute resources in the H100 cluster.
"""

import os
import json
import time
import requests
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

# Import from parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Agent.job_queue import DistributedJobQueue

# Create blueprint
cluster_api = Blueprint('cluster_api', __name__, url_prefix='/api/cluster')

# Initialize job queue on first request
job_queue_instance = None

def get_job_queue():
    """Get or create the distributed job queue instance."""
    global job_queue_instance
    if job_queue_instance is None:
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        job_queue_instance = DistributedJobQueue(redis_url=redis_url)
    return job_queue_instance

@cluster_api.route('/status', methods=['GET'])
def cluster_status():
    """Get status of the compute cluster."""
    job_queue = get_job_queue()
    
    # Get active workers
    active_workers_bytes = job_queue.redis_client.smembers("active_workers")
    active_workers = [w.decode('utf-8') if isinstance(w, bytes) else w for w in active_workers_bytes]
    
    # Get worker details
    worker_details = {}
    for worker_id in active_workers:
        worker_data = job_queue.redis_client.hgetall(f"worker:{worker_id}")
        if worker_data:
            worker_details[worker_id] = {
                k.decode('utf-8') if isinstance(k, bytes) else k: 
                v.decode('utf-8') if isinstance(v, bytes) else v
                for k, v in worker_data.items()
            }
            
            # Parse capabilities if present
            if 'capabilities' in worker_details[worker_id]:
                try:
                    worker_details[worker_id]['capabilities'] = json.loads(worker_details[worker_id]['capabilities'])
                except:
                    pass
                    
            # Calculate last heartbeat age
            if 'last_heartbeat' in worker_details[worker_id]:
                try:
                    last_heartbeat = float(worker_details[worker_id]['last_heartbeat'])
                    worker_details[worker_id]['heartbeat_age_seconds'] = time.time() - last_heartbeat
                except:
                    worker_details[worker_id]['heartbeat_age_seconds'] = -1
    
    # Get storage nodes
    storage_nodes_bytes = job_queue.redis_client.hgetall("storage_nodes")
    storage_nodes = {
        k.decode('utf-8') if isinstance(k, bytes) else k: 
        json.loads(v.decode('utf-8') if isinstance(v, bytes) else v)
        for k, v in storage_nodes_bytes.items()
    }
    
    # Get job queue stats
    queue_length = job_queue.redis_client.llen(job_queue.queue_name)
    pending_jobs = len(job_queue.redis_client.keys("job:*"))
    completed_jobs = len(job_queue.redis_client.hkeys(job_queue.results_key))
    
    # Identify stale workers (no heartbeat in 5 minutes)
    stale_workers = []
    for worker_id, details in worker_details.items():
        if details.get('heartbeat_age_seconds', 0) > 300:  # 5 minutes
            stale_workers.append(worker_id)
    
    return jsonify({
        "active_workers": len(active_workers),
        "storage_nodes": len(storage_nodes),
        "queue_length": queue_length,
        "pending_jobs": pending_jobs,
        "completed_jobs": completed_jobs,
        "stale_workers": stale_workers,
        "worker_details": worker_details,
        "storage_details": storage_nodes
    })

@cluster_api.route('/workers', methods=['GET'])
def list_workers():
    """List all workers in the cluster."""
    job_queue = get_job_queue()
    
    # Get active workers
    active_workers_bytes = job_queue.redis_client.smembers("active_workers")
    active_workers = [w.decode('utf-8') if isinstance(w, bytes) else w for w in active_workers_bytes]
    
    # Get worker details
    workers = []
    for worker_id in active_workers:
        worker_data = job_queue.redis_client.hgetall(f"worker:{worker_id}")
        if worker_data:
            worker_info = {
                "worker_id": worker_id,
                "last_heartbeat": None,
                "heartbeat_age_seconds": -1,
                "capabilities": {},
                "status": "unknown"
            }
            
            # Process worker data
            for k, v in worker_data.items():
                k = k.decode('utf-8') if isinstance(k, bytes) else k
                v = v.decode('utf-8') if isinstance(v, bytes) else v
                
                if k == 'last_heartbeat':
                    try:
                        last_heartbeat = float(v)
                        worker_info['last_heartbeat'] = datetime.fromtimestamp(last_heartbeat).isoformat()
                        worker_info['heartbeat_age_seconds'] = time.time() - last_heartbeat
                        
                        # Determine status based on heartbeat
                        if worker_info['heartbeat_age_seconds'] < 60:  # 1 minute
                            worker_info['status'] = "active"
                        elif worker_info['heartbeat_age_seconds'] < 300:  # 5 minutes
                            worker_info['status'] = "idle"
                        else:
                            worker_info['status'] = "stale"
                    except:
                        pass
                elif k == 'capabilities':
                    try:
                        worker_info['capabilities'] = json.loads(v)
                    except:
                        pass
            
            workers.append(worker_info)
    
    # Sort by status (active first, then idle, then stale)
    status_order = {"active": 0, "idle": 1, "stale": 2, "unknown": 3}
    workers.sort(key=lambda w: status_order.get(w["status"], 4))
    
    return jsonify(workers)

@cluster_api.route('/jobs', methods=['GET'])
def list_jobs():
    """List jobs in the distributed queue."""
    job_queue = get_job_queue()
    
    # Get filtering parameters
    status = request.args.get('status')
    worker_id = request.args.get('worker_id')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Get all job keys
    job_keys = job_queue.redis_client.keys("job:*")
    
    # Process and filter jobs
    jobs = []
    for job_key in job_keys:
        job_key = job_key.decode('utf-8') if isinstance(job_key, bytes) else job_key
        job_id = job_key.split(':', 1)[1] if ':' in job_key else job_key
        
        job_data = job_queue.redis_client.hgetall(job_key)
        if job_data:
            job_info = {
                "job_id": job_id,
                "status": "unknown",
                "document_path": None,
                "submitted_at": None,
                "submitted_by": None,
                "worker": None,
                "processing_started": None,
                "completed_at": None,
                "failed_at": None
            }
            
            # Process job data
            for k, v in job_data.items():
                k = k.decode('utf-8') if isinstance(k, bytes) else k
                v = v.decode('utf-8') if isinstance(v, bytes) else v
                
                if k in ["submitted_at", "processing_started", "completed_at", "failed_at", "retried_at"]:
                    try:
                        timestamp = float(v)
                        job_info[k] = datetime.fromtimestamp(timestamp).isoformat()
                    except:
                        job_info[k] = v
                else:
                    job_info[k] = v
            
            # Apply filters
            if status and job_info.get("status") != status:
                continue
                
            if worker_id and job_info.get("worker") != worker_id:
                continue
                
            jobs.append(job_info)
    
    # Sort by most recent activity (completed, failed, started, or submitted)
    def get_latest_timestamp(job):
        timestamps = []
        for field in ["completed_at", "failed_at", "processing_started", "submitted_at"]:
            if job.get(field):
                try:
                    timestamps.append(datetime.fromisoformat(job[field]))
                except:
                    pass
        return max(timestamps) if timestamps else datetime.min
        
    jobs.sort(key=get_latest_timestamp, reverse=True)
    
    # Apply pagination
    paginated = jobs[offset:offset+limit]
    
    return jsonify({
        "total": len(jobs),
        "offset": offset,
        "limit": limit,
        "jobs": paginated
    })

@cluster_api.route('/jobs', methods=['POST'])
def create_job():
    """Create a new job in the distributed queue."""
    job_queue = get_job_queue()
    
    # Get job parameters
    document_path = request.json.get('document_path')
    metadata = request.json.get('metadata', {})
    
    if not document_path:
        return jsonify({"error": "document_path is required"}), 400
        
    # Create the job
    job_id = job_queue.add_job(document_path, metadata)
    
    return jsonify({
        "status": "success",
        "job_id": job_id,
        "message": f"Job created for {document_path}"
    })

@cluster_api.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get details for a specific job."""
    job_queue = get_job_queue()
    
    # Get job data
    job_data = job_queue.redis_client.hgetall(f"job:{job_id}")
    if not job_data:
        return jsonify({"error": f"Job {job_id} not found"}), 404
        
    # Process job data
    job_info = {
        "job_id": job_id
    }
    
    for k, v in job_data.items():
        k = k.decode('utf-8') if isinstance(k, bytes) else k
        v = v.decode('utf-8') if isinstance(v, bytes) else v
        
        if k in ["submitted_at", "processing_started", "completed_at", "failed_at", "retried_at"]:
            try:
                timestamp = float(v)
                job_info[k] = datetime.fromtimestamp(timestamp).isoformat()
            except:
                job_info[k] = v
        elif k == "result":
            try:
                job_info[k] = json.loads(v)
            except:
                job_info[k] = v
        else:
            job_info[k] = v
    
    # Get result if job is completed
    if job_info.get("status") == "completed":
        result_data = job_queue.redis_client.hget(job_queue.results_key, job_id)
        if result_data:
            result_data = result_data.decode('utf-8') if isinstance(result_data, bytes) else result_data
            try:
                job_info["result"] = json.loads(result_data)
            except:
                job_info["result"] = result_data
    
    return jsonify(job_info)

@cluster_api.route('/jobs/<job_id>/retry', methods=['POST'])
def retry_job(job_id):
    """Retry a failed job."""
    job_queue = get_job_queue()
    
    # Check if job exists
    job_data = job_queue.redis_client.hgetall(f"job:{job_id}")
    if not job_data:
        return jsonify({"error": f"Job {job_id} not found"}), 404
        
    # Requeue the job
    job_queue.requeue_job(job_id)
    
    return jsonify({
        "status": "success",
        "message": f"Job {job_id} requeued for processing"
    })

@cluster_api.route('/prune', methods=['POST'])
def prune_stale_workers():
    """Remove stale workers from the active workers set."""
    job_queue = get_job_queue()
    
    # Get stale threshold in seconds (default: 10 minutes)
    stale_threshold = int(request.json.get('stale_threshold_seconds', 600))
    
    # Get active workers
    active_workers_bytes = job_queue.redis_client.smembers("active_workers")
    active_workers = [w.decode('utf-8') if isinstance(w, bytes) else w for w in active_workers_bytes]
    
    # Find and remove stale workers
    pruned_workers = []
    for worker_id in active_workers:
        worker_data = job_queue.redis_client.hgetall(f"worker:{worker_id}")
        if worker_data and b'last_heartbeat' in worker_data:
            try:
                last_heartbeat = float(worker_data[b'last_heartbeat'])
                heartbeat_age = time.time() - last_heartbeat
                
                if heartbeat_age > stale_threshold:
                    # Remove from active workers
                    job_queue.redis_client.srem("active_workers", worker_id)
                    pruned_workers.append({
                        "worker_id": worker_id,
                        "heartbeat_age_seconds": heartbeat_age
                    })
                    
                    # Find any jobs being processed by this worker and requeue them
                    requeued_jobs = []
                    for job_key in job_queue.redis_client.keys("job:*"):
                        job_key = job_key.decode('utf-8') if isinstance(job_key, bytes) else job_key
                        job_id = job_key.split(':', 1)[1] if ':' in job_key else job_key
                        
                        job_data = job_queue.redis_client.hgetall(job_key)
                        job_worker = job_data.get(b'worker', b'').decode('utf-8') if isinstance(job_data.get(b'worker', b''), bytes) else job_data.get(b'worker', '')
                        job_status = job_data.get(b'status', b'').decode('utf-8') if isinstance(job_data.get(b'status', b''), bytes) else job_data.get(b'status', '')
                        
                        if job_worker == worker_id and job_status == "processing":
                            job_queue.requeue_job(job_id)
                            requeued_jobs.append(job_id)
                            
                    if requeued_jobs:
                        pruned_workers[-1]["requeued_jobs"] = requeued_jobs
            except:
                pass
    
    return jsonify({
        "status": "success",
        "pruned_workers_count": len(pruned_workers),
        "pruned_workers": pruned_workers
    })