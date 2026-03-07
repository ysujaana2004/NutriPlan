"""
Low-level matching/parsing helpers used by the data integration layer.

What this file does:
- Normalizes free-form product/ingredient text into a comparable form.
- Maps text to canonical ingredient IDs using phrase-index matching.
- Parses raw Target price fields into numeric USD values.

Why this is separated:
- These utilities are pure functions with no file I/O.
- Keeping them isolated makes behavior easier to test and reuse.
- Data loaders can focus on reading/merging datasets, not string parsing.

Typical consumers:
- app/data_access.py (canonical mapping and cheapest-product selection).
"""

from __future__ import annotations

import re
from typing import Optional


def normalize_match_text(text: str) -> str:
    """Normalize free text so phrase matching is more reliable."""

    cleaned = (text or "").lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s'-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def map_text_to_canonical_id(
    text: str,
    phrase_index: list[tuple[str, str]],
) -> Optional[str]:
    """Map text to canonical ingredient id using phrase substring matching."""

    normalized = normalize_match_text(text)
    if not normalized:
        return None

    for phrase, canonical_id in phrase_index:
        if phrase and phrase in normalized:
            return canonical_id
    return None


def parse_price_to_usd(price_value: object) -> Optional[float]:
    """Parse a raw price field into USD float when possible."""

    if isinstance(price_value, (int, float)):
        parsed = float(price_value)
        return parsed if parsed > 0 else None

    if not isinstance(price_value, str):
        return None

    numbers = re.findall(r"\d+(?:\.\d+)?", price_value)
    if not numbers:
        return None

    values = [float(number) for number in numbers]
    parsed = min(values)
    return parsed if parsed > 0 else None
