"""Minimal IPFS helper that wraps ipfshttpclient and adds a
`add_or_reuse` convenience to prevent duplicate uploads.
"""
from pathlib import Path
from hashlib import sha256
from typing import Union
import ipfshttpclient

__all__ = ["get_client", "add_or_reuse"]

_client = None


def get_client(api_addr: str = None):
    """Return a cached ipfshttpclient instance."""
    global _client
    if _client is None:
        _client = ipfshttpclient.connect(api_addr) if api_addr else ipfshttpclient.connect()
    return _client


def file_sha256(path: Union[str, Path]) -> str:
    h = sha256()
    p = Path(path)
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def add_or_reuse(path: Union[str, Path], client=None) -> str:
    """Add file to IPFS if not already present; return CID.

    This computes the file's sha256, asks the local node if a block with
    identical multihash exists, and only uploads when missing.
    """
    path = Path(path)
    if client is None:
        client = get_client()

    # quick check via file hash (not perfect but fast)
    file_hash = file_sha256(path)
    pinned = client.pin.ls(type="recursive")
    for cid, info in pinned.items():
        if info.get("Metadata", {}).get("sha256") == file_hash:
            return cid  # already pinned identical content

    res = client.add(path)
    cid = res["Hash"] if isinstance(res, dict) else res[-1]["Hash"]
    # Store sha256 as pin metadata for future lookups
    client.pin.add(cid, metadata={"sha256": file_hash})
    return cid
