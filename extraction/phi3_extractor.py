"""Lightweight wrapper around existing Phi-3 utilities.

The goal is to provide a clean, import-friendly API:
    from extraction.phi3_extractor import extract_metadata

so other modules (validation, enrichment, etc.) never import the big
monolithic enhanced_document_processor directly.
"""
from typing import Dict, Any, Optional

from phi3_wrapper import Phi3Processor  # existing implementation
from enhanced_document_processor import extract_text_from_document  # reuse util

# Singleton cache so we don’t reload the model every call
_model: Optional[Phi3Processor] = None


def get_model(model_path: str = "/models/phi3.gguf", **kwargs) -> Phi3Processor:
    """Return a cached Phi-3 model instance (lazy-loaded)."""
    global _model
    if _model is None:
        _model = Phi3Processor(model_path=model_path, **kwargs)
    return _model


def extract_metadata(document_path: str) -> Dict[str, Any]:
    """Extract structured metadata from a document path.

    Returns a dict like::
        {
            "project": {...},
            "funding": {...},
            "classifications": {...},
            ...
        }
    """
    text = extract_text_from_document(document_path)
    model = get_model()
    return model.process_document_text(text)
