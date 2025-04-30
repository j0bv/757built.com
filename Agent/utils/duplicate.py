"""Helpers to detect potential duplicate processed documents."""
import hashlib
from pathlib import Path
import json
from typing import Dict

PROCESSED_DIR = Path('data/processed')


def title_signature(processed: Dict) -> str:
    title = ''
    if processed.get('document_type') == 'project':
        title = processed.get('project', {}).get('title', '')
    elif processed.get('document_type') == 'patent':
        title = processed.get('patent', {}).get('title', '')
    elif processed.get('document_type') == 'research':
        title = processed.get('research', {}).get('title', '')
    if not title:
        return ''
    return hashlib.sha256(title.lower().encode()).hexdigest()


def detect_duplicates(processed: Dict) -> bool:
    """Return True if a doc with same title hash already exists in processed dir."""
    sig = title_signature(processed)
    if not sig:
        return False

    for path in PROCESSED_DIR.glob('*.json'):
        try:
            with open(path, 'r') as fh:
                data = json.load(fh)
            if title_signature(data) == sig:
                return True
        except Exception:
            continue
    return False
