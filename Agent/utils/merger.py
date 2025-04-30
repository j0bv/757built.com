"""Merge multiple LLM chunk results into a unified document representation.

Current strategy: start with first result as base, append unseen entities/locations/dates.
Future: weight by confidence.
"""
from typing import List, Dict


def smart_union(chunk_results: List[Dict]) -> Dict:
    if not chunk_results:
        return {}

    merged = chunk_results[0].copy()

    # Deduplicate helper
    def _seen_set(list_items, key):
        return {item.get(key) for item in list_items if item.get(key)}

    # Process remaining results
    for chunk in chunk_results[1:]:
        # Locations
        if 'locations' in chunk:
            merged.setdefault('locations', [])
            seen = _seen_set(merged['locations'], 'name')
            for loc in chunk['locations']:
                if loc.get('name') and loc['name'] not in seen:
                    merged['locations'].append(loc)
                    seen.add(loc['name'])
        # Entities
        if 'entities' in chunk:
            merged.setdefault('entities', {})
            for category in ['people', 'organizations', 'companies']:
                if category in chunk['entities']:
                    merged['entities'].setdefault(category, [])
                    seen = _seen_set(merged['entities'][category], 'name')
                    for ent in chunk['entities'][category]:
                        if ent.get('name') and ent['name'] not in seen:
                            merged['entities'][category].append(ent)
                            seen.add(ent['name'])
        # Dates
        if 'dates' in chunk:
            merged.setdefault('dates', [])
            seen_dates = _seen_set(merged['dates'], 'date')
            for d in chunk['dates']:
                if d.get('date') and d['date'] not in seen_dates:
                    merged['dates'].append(d)
                    seen_dates.add(d['date'])
    return merged
