#!/usr/bin/env python3
"""Simple orchestrator that executes all registered ingestion plugins.

Usage::

    python -m ingestion.orchestrator --out /path/to/save/documents

The orchestrator instantiates each plugin class and calls its ``fetch``
method. Documents yielded are saved to *out* directory and queued for
processing (via :pymod:`Agent.job_queue`).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

# Ensure project root is on PYTHONPATH so `ingestion` can import correctly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion import get_plugins  # noqa isort:skip
from Agent.job_queue import enqueue_document  # noqa isort:skip

load_dotenv()

logger = logging.getLogger("ingestion.orchestrator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def save_document(content: str, meta: Dict[str, Any], out_dir: Path) -> Path:
    """Persist document content to disk. Returns file path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # Use timestamp + plugin name + hashed snippet as filename
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    snippet = abs(hash(content)) % 10_000_000  # not cryptographic
    plugin = meta.get("source", "unknown")
    filename = f"{ts}_{plugin}_{snippet}.txt"
    path = out_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(out: Path) -> None:
    plugins = get_plugins()
    if not plugins:
        logger.warning("No ingestion plugins registered. Exiting.")
        return

    logger.info("Running %d ingestion plugins", len(plugins))
    for plugin_cls in plugins:
        plugin = plugin_cls()
        logger.info("Fetching documents from %s", plugin_cls.name)
        for doc in plugin.fetch():
            content = doc.get("content")
            if not content:
                logger.debug("Skipped item without content: %s", doc)
                continue
            path = save_document(content, doc, out)
            enqueue_document(str(path), meta={"source": plugin_cls.name})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run all registered ingestion plugins.")
    parser.add_argument("--out", type=Path, default=Path("data/raw"), help="Output directory for documents")
    args = parser.parse_args()

    run(args.out)
