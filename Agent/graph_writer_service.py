"""Background service that consumes processed-document events from Redis Stream
and writes them into the graph DB.
Run with:
    python Agent/graph_writer_service.py
Environment variables:
    REDIS_URL   – redis connection url (default redis://localhost:6379/0)
"""
import json
import logging
import os
import sys
import time
from typing import Any, Dict

import redis

# Re-use existing graph helpers from main processor
from enhanced_document_processor import add_document_to_graph, save_graph

logger = logging.getLogger('graph_writer')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

STREAM_NAME = 'graph_updates'
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
GROUP_NAME = 'graph_writers'
CONSUMER_NAME = os.getenv('HOSTNAME', 'writer')


def connect_redis() -> redis.Redis:
    return redis.from_url(REDIS_URL, decode_responses=True)


def ensure_group(r: redis.Redis):
    try:
        r.xgroup_create(STREAM_NAME, GROUP_NAME, id='0', mkstream=True)
    except redis.exceptions.ResponseError as e:
        # Group already exists
        if 'BUSYGROUP' in str(e):
            return
        raise


def handle_message(msg_id: str, fields: Dict[str, Any]):
    try:
        document_path = fields['path']
        processed_json = json.loads(fields['data'])
        G = add_document_to_graph(document_path, processed_json)
        # Similar edges
        for cid in processed_json.get("similar_docs", []):
            G.add_edge(processed_json.get("metadata_cid"), cid, key="SIMILAR_TO", weight=0.5)
        save_graph(G)
        logger.info("Graph updated for %s", document_path)
    except Exception as e:
        logger.exception("Error handling message %s: %s", msg_id, e)


def main():
    r = connect_redis()
    ensure_group(r)
    while True:
        try:
            entries = r.xreadgroup(GROUP_NAME, CONSUMER_NAME, {STREAM_NAME: '>'}, count=10, block=5000)
            if not entries:
                continue
            for stream, msgs in entries:
                for msg_id, fields in msgs:
                    handle_message(msg_id, fields)
                    r.xack(STREAM_NAME, GROUP_NAME, msg_id)
        except Exception:
            logger.exception("Redis read error; sleeping before retry")
            time.sleep(5)


if __name__ == '__main__':
    main()
