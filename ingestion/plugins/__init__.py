"""Automatic import of ingestion plugins.

Any module placed in this sub-package that defines a subclass of
`ingestion.SourcePlugin` will be auto-registered at import time.  This file
iterates over the children of the current package and imports them so the
registration side-effects occur without any manual wiring.
"""
from importlib import import_module
import pkgutil

# Import all sibling modules (non-packages) to trigger `SourcePlugin` registry
for mod_info in pkgutil.iter_modules(__path__):
    if mod_info.ispkg:
        # Nested packages can define their own auto-import logic.
        continue
    import_module(f"{__name__}.{mod_info.name}")
