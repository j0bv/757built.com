"""Wrapper for vector DB (Qdrant) operations and Jina v3 embedding calls."""
from __future__ import annotations

import os
import hashlib
import json
from typing import List, Dict, Any, Optional

import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

# env vars
VECTOR_URL = os.getenv("VECTOR_URL", "http://localhost:6333")
COLLECTION = os.getenv("VECTOR_COLLECTION", "docs")
EMBED_URL = os.getenv("EMBED_ENDPOINT", "http://localhost:8081/embed")

# lazy singleton
_client: Optional[QdrantClient] = None

def _client_or_init() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=VECTOR_URL)
        # ensure collection exists (simple 1536-dim float vector for Jina v3)
        if COLLECTION not in [c.name for c in _client.get_collections().collections]:
            _client.recreate_collection(
                collection_name=COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=1536, distance=qmodels.Distance.COSINE
                ),
            )
    return _client


def _embed(text: str) -> List[float]:
    """Call the external Jina v3 embedding service."""
    resp = requests.post(EMBED_URL, json={"text": text})
    resp.raise_for_status()
    return resp.json()["embedding"]


def _doc_id(processed: Dict[str, Any]) -> str:
    # stable identifier: CID if present else sha256 of title+date
    if processed.get("metadata_cid"):
        return processed["metadata_cid"]
    title = processed.get("project", {}).get("title") or processed.get("patent", {}).get("title") or processed.get("research", {}).get("title") or ""
    return hashlib.sha256(title.encode()).hexdigest()


def upsert_document(processed: Dict[str, Any], raw_text: str):
    vec = _embed(raw_text)
    client = _client_or_init()
    payload = {
        "document_type": processed.get("document_type"),
        "title": processed.get("project", {}).get("title") or processed.get("patent", {}).get("title") or processed.get("research", {}).get("title"),
        "metadata_cid": processed.get("metadata_cid"),
    }
    client.upsert(
        collection_name=COLLECTION,
        points=[qmodels.PointStruct(id=_doc_id(processed), vector=vec, payload=payload)],
    )


def similar_docs(query_text: str, k: int = 5) -> List[str]:
    vec = _embed(query_text)
    client = _client_or_init()
    hits = client.search(COLLECTION, vec, limit=k)
    return [hit.payload.get("metadata_cid") for hit in hits if hit.payload.get("metadata_cid")]
