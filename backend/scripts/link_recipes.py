"""
link_recipes.py

Generic recipe-to-store coverage linker.

Usage:
  python backend/scripts/link_recipes.py --store target
  python backend/scripts/link_recipes.py --store walmart
  python backend/scripts/link_recipes.py --store bjs
  python backend/scripts/link_recipes.py --store whole_foods
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DATA_DIR = BACKEND_DIR / "data"

RECIPES_PATH = DATA_DIR / "recipes" / "recipes-full.json"
CANONICAL_PATH = DATA_DIR / "recipes" / "canonical_ingredients.json"
CANONICAL_FALLBACK_PATH = DATA_DIR / "recipes" / "canconical_ingredients.json"

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

STORE_ALIASES = {
    "bj": "bjs",
    "bj_s": "bjs",
    "bj's": "bjs",
    "wholefoods": "whole_foods",
}


def normalize_store_key(raw: str) -> str:
    """Normalize user input into a canonical store key."""

    token = re.sub(r"[^a-z0-9]+", "_", str(raw).strip().lower()).strip("_")
    return STORE_ALIASES.get(token, token)


def norm_text(text: str) -> str:
    """Normalize text for simple substring matching."""

    value = str(text or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s'-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def load_json(path: Path) -> Any:
    """Load JSON from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def build_canonical_index(canonical_list: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str]]]:
    """Build canonical lookup maps used by recipe/product matching."""

    id_to_obj: dict[str, dict[str, Any]] = {}
    phrase_index: list[tuple[str, str]] = []

    for item in canonical_list:
        canonical_id = str(item["id"])
        id_to_obj[canonical_id] = item

        phrases = [item.get("canonical", "")] + (item.get("aliases", []) or [])
        for phrase in phrases:
            normalized = norm_text(phrase)
            if normalized:
                phrase_index.append((normalized, canonical_id))

    phrase_index.sort(key=lambda pair: len(pair[0]), reverse=True)
    return id_to_obj, phrase_index


def map_text_to_canonical(text: str, phrase_index: list[tuple[str, str]]) -> Optional[str]:
    """Return matched canonical id via simple phrase-in-text strategy."""

    normalized_text = norm_text(text)
    if not normalized_text:
        return None

    for phrase, canonical_id in phrase_index:
        if phrase and phrase in normalized_text:
            return canonical_id
    return None


def is_pantry_ignored_item(text: str) -> bool:
    """Return True for pantry/seasoning terms ignored in coverage."""

    normalized = norm_text(text)
    if not normalized:
        return False
    normalized = re.sub(r"\b(to taste|as needed)\b", "", normalized).strip(" ,")
    return normalized in PANTRY_IGNORE_TERMS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Link recipes to one store's catalog via canonical ingredients.")
    parser.add_argument("--store", required=True, help="Store key/name (e.g. target, walmart, bjs, whole_foods).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    store_key = normalize_store_key(args.store)

    products_flat_path = DATA_DIR / "stores" / store_key / "products_flat.json"
    out_path = DATA_DIR / "stores" / store_key / "recipes-with-canonical.json"
    canonical_path = CANONICAL_PATH if CANONICAL_PATH.exists() else CANONICAL_FALLBACK_PATH

    for path in (RECIPES_PATH, products_flat_path, canonical_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")

    recipes = load_json(RECIPES_PATH)
    products = load_json(products_flat_path)
    canonical_list = load_json(canonical_path)

    id_to_obj, phrase_index = build_canonical_index(canonical_list)

    # 1) Product coverage universe for the selected store.
    store_coverage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unmapped_products = 0
    for product in products:
        canonical_id = map_text_to_canonical(str(product.get("name", "")), phrase_index)
        if canonical_id:
            store_coverage[canonical_id].append(product)
        else:
            unmapped_products += 1

    # 2) Recipe ingredient mapping + store coverage summary.
    out: list[dict[str, Any]] = []
    unmapped_recipe_ings: Counter[str] = Counter()
    mapped_recipe_ings: Counter[str] = Counter()
    ignored_pantry_ings: Counter[str] = Counter()
    fully_covered = 0

    for recipe in recipes:
        canonical_ids: list[str] = []
        raw_ings: list[str] = []
        pantry_ignored_for_recipe: list[str] = []

        for ingredient in recipe.get("extendedIngredients", []) or []:
            raw = str(
                ingredient.get("nameClean")
                or ingredient.get("name")
                or ingredient.get("originalName")
                or ""
            ).strip()
            if not raw:
                continue

            raw_ings.append(raw)
            if is_pantry_ignored_item(raw):
                pantry_norm = norm_text(raw)
                ignored_pantry_ings[pantry_norm] += 1
                pantry_ignored_for_recipe.append(pantry_norm)
                continue

            canonical_id = map_text_to_canonical(raw, phrase_index)
            if canonical_id:
                canonical_ids.append(canonical_id)
                mapped_recipe_ings[canonical_id] += 1
            else:
                unmapped_recipe_ings[norm_text(raw)] += 1

        canonical_ids_unique = sorted(set(canonical_ids))
        covered = [cid for cid in canonical_ids_unique if cid in store_coverage and store_coverage[cid]]
        missing = [cid for cid in canonical_ids_unique if cid not in store_coverage or not store_coverage[cid]]

        if canonical_ids_unique and not missing:
            fully_covered += 1

        out.append(
            {
                "id": recipe.get("id"),
                "title": recipe.get("title"),
                "canonical_ingredients": canonical_ids_unique,
                "covered_canonical": covered,
                "missing_canonical": missing,
                "ignored_pantry_items": sorted(set(pantry_ignored_for_recipe)),
                "raw_ingredients_sample": raw_ings[:20],
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"Store: {store_key}")
    print(f"Recipes analyzed: {len(recipes)}")
    print(f"Canonical items defined: {len(canonical_list)}")
    print(f"Store products total: {len(products)}")
    print(f"Store products unmapped (expected early): {unmapped_products}")
    print(f"Recipes fully covered (within canonical set AND purchasable): {fully_covered}/{len(recipes)}")
    print(f"Pantry/seasoning ingredient mentions ignored: {sum(ignored_pantry_ings.values())}")
    print(f"Saved: {out_path}")

    print("\nTop unmapped recipe ingredient strings (add aliases for these):")
    for text, count in unmapped_recipe_ings.most_common(20):
        print(f"- {text} ({count}x)")

    print("\nTop pantry/seasoning items ignored:")
    for text, count in ignored_pantry_ings.most_common(20):
        print(f"- {text} ({count}x)")

    missing_store_for_canonical: list[tuple[str, int]] = []
    for canonical_id, count in mapped_recipe_ings.most_common():
        if canonical_id not in store_coverage or not store_coverage[canonical_id]:
            missing_store_for_canonical.append((canonical_id, count))

    if missing_store_for_canonical:
        print(f"\nCanonical items used by recipes but missing {store_key} coverage:")
        for canonical_id, count in missing_store_for_canonical[:20]:
            print(f"- {canonical_id} ({id_to_obj[canonical_id]['canonical']}) used {count}x")


if __name__ == "__main__":
    main()
