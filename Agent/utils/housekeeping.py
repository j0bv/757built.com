"""Housekeeping utilities: remove stale failed docs & unreferenced IPFS pins"""
import os
import json
import time
from pathlib import Path
import ipfshttpclient
import logging

logger = logging.getLogger(__name__)

FAILED_DIR = Path('data/failed')
PROCESSED_DIR = Path('data/processed')
PIN_LIFETIME_DAYS = int(os.getenv('PIN_LIFETIME_DAYS', '30'))
STALENESS_DAYS = int(os.getenv('FAILED_DOC_STALENESS_DAYS', '7'))


def _cleanup_failed():
    now = time.time()
    threshold = STALENESS_DAYS * 86400
    removed = 0
    for path in FAILED_DIR.glob('*'):
        if not path.is_file():
            continue
        if now - path.stat().st_mtime > threshold:
            try:
                path.unlink()
                removed += 1
            except Exception as e:
                logger.error("Failed to delete %s: %s", path, e)
    logger.info("Removed %s stale failed docs", removed)


def _cleanup_pins():
    client = None
    try:
        client = ipfshttpclient.connect()
    except Exception as e:
        logger.error("Cannot connect to IPFS: %s", e)
        return

    # collect referenced CIDs in processed files
    referenced = set()
    for path in PROCESSED_DIR.glob('*.json'):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                cid = data.get('metadata_cid')
                if cid:
                    referenced.add(cid)
        except Exception:
            continue

    # query pin ls
    pins = client.pin.ls(type='recursive')
    now = time.time()
    removed = 0
    for cid, info in pins.get('Keys', {}).items():
        if cid in referenced:
            continue
        ts = info.get('Timestamp')
        if ts is None:
            continue
        # timestamp looks like "2025-04-22T22:30:05.505184225Z"
        try:
            pin_time = time.strptime(ts.split('T')[0], "%Y-%m-%d")
            age_days = (now - time.mktime(pin_time)) / 86400
        except Exception:
            age_days = PIN_LIFETIME_DAYS + 1  # force removal if parsing fails
        if age_days > PIN_LIFETIME_DAYS:
            try:
                client.pin.rm(cid)
                removed += 1
            except Exception as e:
                logger.error("Failed to remove pin %s: %s", cid, e)
    logger.info("Removed %s unreferenced pins", removed)


def run_cleanup():
    _cleanup_failed()
    _cleanup_pins()
