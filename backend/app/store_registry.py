"""Store keys, aliases, and helper lookups used across backend services."""

from __future__ import annotations

import re


# Canonical runtime keys.
TARGET = "target"
WALMART = "walmart"
BJS = "bjs"
WHOLE_FOODS = "whole_foods"

SUPPORTED_STORE_KEYS: tuple[str, ...] = (TARGET, WALMART, BJS, WHOLE_FOODS)

# Aliases accepted from API callers / UI text.
STORE_ALIASES: dict[str, str] = {
    "target": TARGET,
    "walmart": WALMART,
    "bjs": BJS,
    "bj": BJS,
    "bj_s": BJS,
    "bj's": BJS,
    "wh foods": WHOLE_FOODS,
    "wholefoods": WHOLE_FOODS,
    "whole_foods": WHOLE_FOODS,
    "whole foods": WHOLE_FOODS,
}

# Friendly labels for API responses and location query text.
STORE_DISPLAY_NAMES: dict[str, str] = {
    TARGET: "Target",
    WALMART: "Walmart",
    BJS: "BJs",
    WHOLE_FOODS: "Whole Foods",
}

STORE_LOCATION_QUERY_NAMES: dict[str, str] = {
    TARGET: "Target",
    WALMART: "Walmart",
    BJS: "BJ's Wholesale Club",
    WHOLE_FOODS: "Whole Foods Market",
}


def normalize_store_key(value: str | None, default: str = TARGET) -> str:
    """Convert arbitrary caller text into a supported store key."""

    token = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    if not token:
        return default
    return STORE_ALIASES.get(token, default)


def display_name_for_store_key(store_key: str) -> str:
    """Return human-facing name for a store key."""

    return STORE_DISPLAY_NAMES.get(store_key, STORE_DISPLAY_NAMES[TARGET])


def location_query_name_for_store_key(store_key: str) -> str:
    """Return best search text for Google Places query."""

    return STORE_LOCATION_QUERY_NAMES.get(store_key, STORE_LOCATION_QUERY_NAMES[TARGET])
