"""Stub for future enrichment / validation logic.

Expose a simple API so other modules can call::

    from validation.validator import validate_record

and get back a (possibly) modified record plus a list of issues.
"""
from typing import Tuple, Dict, Any, List


class ValidationIssue(str):
    """Marker subclass for future expansion (severity, code, etc.)."""


def validate_record(record: Dict[str, Any]) -> Tuple[Dict[str, Any], List[ValidationIssue]]:
    """Placeholder that currently performs no changes.

    Returns (possibly_modified_record, [issues]).  Initially just echoes
    the input so that pipelines can integrate without altering
    behaviour.  Future versions can check required fields, look up
    external sources, etc.
    """
    issues: List[ValidationIssue] = []

    # Example: warn if no "funding" key
    if "funding" not in record:
        issues.append(ValidationIssue("missing_funding"))

    return record, issues
