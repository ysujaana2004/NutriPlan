"""
link_recipes_to_walmart.py

Milestone 2.3 + 2.4:
- Loads recipes (Spoonacular full)
- Loads Walmart product index (flat)
- Loads canonical ingredient definitions
- Maps each recipe ingredient -> canonical id (best-effort)
- Maps each Walmart product -> canonical id (best-effort)
- Computes coverage: which canonical ingredients in a recipe are purchasable in Walmart datasets
- Saves data/recipes-with-canonical-walmart.json + prints report

This is intentionally rule-based first. You will expand aliases over time.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

# Resolve paths from this script location, not from current working directory.
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DATA_DIR = BACKEND_DIR / "data"

RECIPES_PATH = DATA_DIR / "recipes-full.json"
WALMART_FLAT_PATH = DATA_DIR / "walmart_products_flat.json"
CANONICAL_PATH = DATA_DIR / "canonical_ingredients.json"
CANONICAL_FALLBACK_PATH = DATA_DIR / "canconical_ingredients.json"
OUT_PATH = DATA_DIR / "recipes-with-canonical-walmart.json"

# Items commonly treated as pantry staples/seasonings for MVP shopping logic.
# These are ignored in recipe->canonical matching coverage.
PANTRY_IGNORE_TERMS = {
    "salt",
    "sea salt",
    "kosher salt",
    "pepper",
    "black pepper",
    "salt and pepper",
    "water",
    "sugar",
    "granulated sugar",
    "brown sugar",
    "powdered sugar",
    "baking powder",
    "baking soda",
}


def norm_text(s: str) -> str:
    """Normalize text for matching."""
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9\s'-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_json(path: Path) -> Any:
    with open(path, "r") as f:
        return json.load(f)


def build_canonical_index(canonical_list: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Returns:
      - id_to_obj: canonical_id -> canonical object
      - phrase_index: list of (phrase, canonical_id) where phrase includes canonical + aliases
    """
    id_to_obj: Dict[str, Dict[str, Any]] = {}
    phrase_index: List[Tuple[str, str]] = []

    for item in canonical_list:
        cid = item["id"]
        id_to_obj[cid] = item

        phrases = [item.get("canonical", "")] + item.get("aliases", [])
        for p in phrases:
            p = norm_text(p)
            if p:
                phrase_index.append((p, cid))

    # Prefer longer phrases first (more specific)
    phrase_index.sort(key=lambda x: len(x[0]), reverse=True)
    return id_to_obj, phrase_index


def map_text_to_canonical(text: str, phrase_index: List[Tuple[str, str]]) -> Optional[str]:
    """
    Very simple matcher:
    - normalize text
    - if a canonical/alias phrase appears as a substring, return that canonical id
    """
    t = norm_text(text)
    if not t:
        return None

    for phrase, cid in phrase_index:
        if phrase and phrase in t:
            return cid

    return None


def is_pantry_ignored_item(text: str) -> bool:
    """Return True if ingredient text matches a pantry/seasoning ignore term."""
    t = norm_text(text)
    if not t:
        return False

    # Strip common suffix qualifiers so "salt to taste" still maps to "salt".
    t = re.sub(r"\b(to taste|as needed)\b", "", t).strip(" ,")
    return t in PANTRY_IGNORE_TERMS


def main():
    canonical_path = CANONICAL_PATH if CANONICAL_PATH.exists() else CANONICAL_FALLBACK_PATH
    walmart_flat_path = WALMART_FLAT_PATH

    for p in [RECIPES_PATH, walmart_flat_path, canonical_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing required file: {p}")

    recipes = load_json(RECIPES_PATH)
    walmart_products = load_json(walmart_flat_path)
    canonical_list = load_json(canonical_path)

    id_to_obj, phrase_index = build_canonical_index(canonical_list)

    # 1) Map Walmart products -> canonical ids (coverage universe)
    walmart_coverage: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    unmapped_products = 0

    for prod in walmart_products:
        cid = map_text_to_canonical(prod.get("name", ""), phrase_index)
        if cid:
            walmart_coverage[cid].append(prod)
        else:
            unmapped_products += 1

    # 2) Map recipe ingredients -> canonical ids, then compute coverage
    out: List[Dict[str, Any]] = []
    unmapped_recipe_ings = Counter()
    mapped_recipe_ings = Counter()
    ignored_pantry_ings = Counter()

    fully_covered = 0

    for r in recipes:
        rid = r.get("id")
        title = r.get("title")

        canonical_ids = []
        raw_ings = []
        pantry_ignored_for_recipe = []

        for ing in r.get("extendedIngredients", []):
            raw = ing.get("nameClean") or ing.get("name") or ing.get("originalName") or ""
            raw = raw.strip()
            if not raw:
                continue

            raw_ings.append(raw)
            if is_pantry_ignored_item(raw):
                pantry_norm = norm_text(raw)
                ignored_pantry_ings[pantry_norm] += 1
                pantry_ignored_for_recipe.append(pantry_norm)
                continue

            cid = map_text_to_canonical(raw, phrase_index)
            if cid:
                canonical_ids.append(cid)
                mapped_recipe_ings[cid] += 1
            else:
                unmapped_recipe_ings[norm_text(raw)] += 1

        # unique canonical ids per recipe
        canonical_ids_unique = sorted(set(canonical_ids))

        covered = []
        missing = []

        for cid in canonical_ids_unique:
            if cid in walmart_coverage and len(walmart_coverage[cid]) > 0:
                covered.append(cid)
            else:
                missing.append(cid)

        if canonical_ids_unique and len(missing) == 0:
            fully_covered += 1

        out.append({
            "id": rid,
            "title": title,
            "canonical_ingredients": canonical_ids_unique,
            "covered_canonical": covered,
            "missing_canonical": missing,
            "ignored_pantry_items": sorted(set(pantry_ignored_for_recipe)),
            # helpful for debugging mapping early on:
            "raw_ingredients_sample": raw_ings[:20],
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    # -------- Report --------
    total_recipes = len(recipes)
    print(f"Recipes analyzed: {total_recipes}")
    print(f"Canonical items defined: {len(canonical_list)}")
    print(f"Walmart products total: {len(walmart_products)}")
    print(f"Walmart products unmapped (expected early): {unmapped_products}")
    print(f"Recipes fully covered (within canonical set AND purchasable): {fully_covered}/{total_recipes}")
    print(f"Pantry/seasoning ingredient mentions ignored: {sum(ignored_pantry_ings.values())}")
    print(f"Saved: {OUT_PATH}")

    # Show most common unmapped recipe ingredient strings (so you can add aliases)
    print("\nTop unmapped recipe ingredient strings (add aliases for these):")
    for s, c in unmapped_recipe_ings.most_common(20):
        print(f"- {s} ({c}x)")

    print("\nTop pantry/seasoning items ignored:")
    for s, c in ignored_pantry_ings.most_common(20):
        print(f"- {s} ({c}x)")

    # Show which canonical items are common in recipes but have zero Walmart matches
    missing_walmart_for_canonical = []
    for cid, cnt in mapped_recipe_ings.most_common():
        if cid not in walmart_coverage or len(walmart_coverage[cid]) == 0:
            missing_walmart_for_canonical.append((cid, cnt))

    if missing_walmart_for_canonical:
        print("\nCanonical items used by recipes but missing Walmart coverage:")
        for cid, cnt in missing_walmart_for_canonical[:20]:
            print(f"- {cid} ({id_to_obj[cid]['canonical']}) used {cnt}x")


if __name__ == "__main__":
    main()
