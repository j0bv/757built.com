from __future__ import annotations

"""Ingestion plugin framework.

Any new data-source agent should subclass `SourcePlugin` and set a unique
`name` attribute.  Sub-classes auto-register themselves so orchestration code
can discover and run them dynamically.

Example::

    # my_source.py
    from ingestion import SourcePlugin

    class MySource(SourcePlugin):
        name = "my_source"

        def fetch(self):
            yield {"title": "Example", "content": "..."}

    # orchestrate
    from ingestion import get_plugins
    for plugin_cls in get_plugins():
        for doc in plugin_cls().fetch():
            ...  # send to document processor
"""

from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any, List, Type

__all__ = [
    "SourcePlugin",
    "get_plugins",
    "create_plugin",
]

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_SOURCE_REGISTRY: Dict[str, Type["SourcePlugin"]] = {}


class SourcePlugin(ABC):
    """Abstract base‐class that all ingestion sources must extend."""

    #: Unique identifier (e.g., "arxiv", "uspto", "city_portal")
    name: str = "unnamed"

    def __init_subclass__(cls, **kwargs):  # type: ignore[override]
        super().__init_subclass__(**kwargs)
        # Auto-register subclasses that define a non-empty name
        if cls is not SourcePlugin and getattr(cls, "name", None):
            if cls.name in _SOURCE_REGISTRY:
                raise RuntimeError(f"Duplicate ingestion plugin name: {cls.name}")
            _SOURCE_REGISTRY[cls.name] = cls  # type: ignore[assignment]

    # ---------------------------------------------------------------------
    # Public API that subclasses must implement
    # ---------------------------------------------------------------------
    @abstractmethod
    def fetch(self) -> Iterable[Dict[str, Any]]:
        """Yield documents as dictionaries to be stored/processed.

        Each yielded dict **must** contain at least a unique `id` key and raw
        `content` string (or path/URL).  Additional metadata (e.g., `source`,
        `timestamp`, `coordinates`) is encouraged.
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Auto-discovery of plugins sub-package
# ---------------------------------------------------------------------------

try:
    # Importing this package will trigger auto-registration side-effects for
    # any modules in ``ingestion.plugins`` because that sub-package’s
    # ``__init__`` eagerly imports its children.
    import importlib

    importlib.import_module("ingestion.plugins")
except ModuleNotFoundError:
    # The plugins package is optional; continue silently if missing
    pass


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def get_plugins() -> List[Type[SourcePlugin]]:
    """Return all registered ingestion plugin classes."""
    return list(_SOURCE_REGISTRY.values())


def create_plugin(name: str, **kwargs) -> SourcePlugin:
    """Instantiate a plugin by its registered *name*."""
    try:
        cls = _SOURCE_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown ingestion plugin '{name}'.") from exc
    return cls(**kwargs)  # type: ignore[call-arg]
