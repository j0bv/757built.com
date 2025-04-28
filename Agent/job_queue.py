#!/usr/bin/env python3
"""Simple Redis-backed job queue helper for document processing.

This decouples crawlers (producers) from analysis workers (consumers).
Each job is a JSON string with at least a "path" field (absolute or
relative path to the downloaded document). Additional metadata (e.g.
URL, content hash) can be included for future enrichment.

Environment variables:
  REDIS_URL         Redis connection string, default redis://localhost:6379/0
  DOC_QUEUE_KEY     Redis list key for document jobs, default doc_queue
"""
import os
import json
import logging
from typing import Optional, Dict, Any

import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("DOC_QUEUE_KEY", "doc_queue")

logger = logging.getLogger("job_queue")

_redis = redis.Redis.from_url(REDIS_URL)


def enqueue_document(path: str, meta: Optional[Dict[str, Any]] = None) -> bool:
    """Push a document-processing job onto the queue."""
    try:
        job = {"path": path}
        if meta:
            job.update(meta)
        _redis.lpush(QUEUE_KEY, json.dumps(job))
        logger.info("Enqueued job for %s", path)
        return True
    except Exception as exc:
        logger.error("Failed to enqueue job: %s", exc)
        return False


def dequeue_document(block: bool = True, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Pop the next job from the queue. Returns None if queue empty."""
    try:
        if block:
            item = _redis.brpop(QUEUE_KEY, timeout=timeout)
            if item is None:
                return None
            _, data = item
        else:
            data = _redis.rpop(QUEUE_KEY)
            if data is None:
                return None
        return json.loads(data)
    except Exception as exc:
        logger.error("Failed to dequeue job: %s", exc)
        return None
