"""
Data loading and enrichment layer for recipes, canonical ingredients, and store products.

Primary responsibilities:
1. Read local JSON datasets from backend/data.
2. Build canonical phrase indexes from canonical+alias definitions.
3. Map store products to canonical ingredients and choose cheapest options.
4. Join recipe canonical-coverage data with nutrition rows.
5. Produce enriched RealRecipe objects for optimizer scoring.

Caching strategy:
- Uses lru_cache for expensive dataset loads and lookups.
- Exposes clear_caches() so tests can safely monkeypatch file paths.

Why this layer matters:
- It is the bridge between offline preprocessing outputs
  (recipes-with-canonical, store products, recipes-nutrition)
  and runtime optimization inputs.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from . import data_paths
from .matching import map_text_to_canonical_id, normalize_match_text, parse_price_to_usd
from .store_registry import normalize_store_key


RECIPES_NUTRITION_PATH = data_paths.RECIPES_NUTRITION_PATH
RECIPES_FULL_PATH = data_paths.RECIPES_FULL_PATH
TARGET_PRODUCTS_FLAT_PATH = data_paths.store_products_flat_path(data_paths.TARGET_STORE_KEY)
WALMART_PRODUCTS_FLAT_PATH = data_paths.store_products_flat_path(data_paths.WALMART_STORE_KEY)
BJS_PRODUCTS_FLAT_PATH = data_paths.store_products_flat_path(data_paths.BJS_STORE_KEY)
WHOLE_FOODS_PRODUCTS_FLAT_PATH = data_paths.store_products_flat_path(data_paths.WHOLE_FOODS_STORE_KEY)
RECIPES_WITH_CANONICAL_TARGET_PATH = data_paths.store_recipe_coverage_path(data_paths.TARGET_STORE_KEY)
RECIPES_WITH_CANONICAL_WALMART_PATH = data_paths.store_recipe_coverage_path(data_paths.WALMART_STORE_KEY)
RECIPES_WITH_CANONICAL_BJS_PATH = data_paths.store_recipe_coverage_path(data_paths.BJS_STORE_KEY)
RECIPES_WITH_CANONICAL_WHOLE_FOODS_PATH = data_paths.store_recipe_coverage_path(data_paths.WHOLE_FOODS_STORE_KEY)
# Backward-compatible alias for existing callers/tests that expect Target coverage.
RECIPES_WITH_CANONICAL_PATH = RECIPES_WITH_CANONICAL_TARGET_PATH
CANONICAL_INGREDIENTS_PATH = data_paths.CANONICAL_INGREDIENTS_PATH
CANONICAL_INGREDIENTS_FALLBACK_PATH = data_paths.CANONICAL_INGREDIENTS_FALLBACK_PATH


@dataclass(frozen=True)
class RealRecipe:
    """Nutrition recipe row enriched with store coverage and estimated ingredient cost."""

    id: str
    title: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    estimated_cost_usd: float
    covered_canonical_count: int
    missing_canonical_count: int
    coverage_ratio: float
    image_url: str
    dish_types: tuple[str, ...]
    ingredient_lines: tuple[tuple[str, str], ...]
    instruction_steps: tuple[str, ...]


@dataclass(frozen=True)
class CanonicalProductChoice:
    """Cheapest known store product match for one canonical ingredient id."""

    canonical_id: str
    product_name: str
    price_usd: float
    category: str


@dataclass(frozen=True)
class RecipeCoverageSummary:
    """Coverage summary and estimated cost for one recipe id."""

    covered_canonical: tuple[str, ...]
    missing_canonical: tuple[str, ...]
    estimated_cost_usd: float
    coverage_ratio: float


@dataclass(frozen=True)
class RecipeDetailSummary:
    """Renderable details for one recipe id, pulled from recipes-full.json."""

    image_url: str
    dish_types: tuple[str, ...]
    ingredient_lines: tuple[tuple[str, str], ...]
    instruction_steps: tuple[str, ...]


EMPTY_COVERAGE_SUMMARY = RecipeCoverageSummary(
    covered_canonical=tuple(),
    missing_canonical=tuple(),
    estimated_cost_usd=0.0,
    coverage_ratio=0.0,
)

EMPTY_RECIPE_DETAIL_SUMMARY = RecipeDetailSummary(
    image_url="",
    dish_types=tuple(),
    ingredient_lines=tuple(),
    instruction_steps=tuple(),
)


def canonical_ingredients_file_path() -> Path:
    """Return the canonical ingredient file path, supporting naming variants."""

    if CANONICAL_INGREDIENTS_PATH.exists():
        return CANONICAL_INGREDIENTS_PATH
    return CANONICAL_INGREDIENTS_FALLBACK_PATH


def normalize_store_name(store_name: str) -> str:
    """Normalize incoming store preference to a known store key."""

    return normalize_store_key(store_name, default=data_paths.TARGET_STORE_KEY)


def _read_json_rows(path: Path) -> list[dict[str, Any]]:
    """Read a JSON array from disk; return [] on missing/bad/non-list payloads."""

    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return payload if isinstance(payload, list) else []


def _load_canonical_rows() -> list[dict[str, Any]]:
    """Load canonical ingredient rows from primary/fallback files."""

    return _read_json_rows(canonical_ingredients_file_path())


def _store_recipe_coverage_path(store_name: str) -> Path:
    """Resolve per-store recipes-with-canonical coverage file path."""

    store_key = normalize_store_name(store_name)
    if store_key == data_paths.WALMART_STORE_KEY:
        return RECIPES_WITH_CANONICAL_WALMART_PATH
    if store_key == data_paths.BJS_STORE_KEY:
        return RECIPES_WITH_CANONICAL_BJS_PATH
    if store_key == data_paths.WHOLE_FOODS_STORE_KEY:
        return RECIPES_WITH_CANONICAL_WHOLE_FOODS_PATH
    # Keep using alias so tests that monkeypatch RECIPES_WITH_CANONICAL_PATH keep working.
    return RECIPES_WITH_CANONICAL_PATH


def _store_products_flat_path(store_name: str) -> Path:
    """Resolve per-store products-flat path."""

    store_key = normalize_store_name(store_name)
    if store_key == data_paths.WALMART_STORE_KEY:
        return WALMART_PRODUCTS_FLAT_PATH
    if store_key == data_paths.BJS_STORE_KEY:
        return BJS_PRODUCTS_FLAT_PATH
    if store_key == data_paths.WHOLE_FOODS_STORE_KEY:
        return WHOLE_FOODS_PRODUCTS_FLAT_PATH
    return TARGET_PRODUCTS_FLAT_PATH


def _normalize_amount_value(amount_value: object) -> str:
    """Convert numeric amount values to a clean string for display."""

    if isinstance(amount_value, float):
        amount_text = f"{amount_value:.4f}".rstrip("0").rstrip(".")
        return amount_text or "0"
    return str(amount_value).strip()


def _extract_ingredient_lines(recipe_row: dict) -> tuple[tuple[str, str], ...]:
    """Extract display-ready ingredient lines from one full recipe row."""

    ingredients = recipe_row.get("extendedIngredients", []) or []
    lines: list[tuple[str, str]] = []
    for ingredient in ingredients:
        name = str(ingredient.get("nameClean") or ingredient.get("name") or "").strip()
        if not name:
            continue

        amount = str(ingredient.get("original") or "").strip()
        if not amount:
            amount_value = ingredient.get("amount")
            unit = str(ingredient.get("unit") or "").strip()
            if amount_value is not None and str(amount_value).strip():
                amount = f"{_normalize_amount_value(amount_value)} {unit}".strip()
        if not amount:
            amount = "as needed"

        lines.append((name, amount))

    return tuple(lines)


def _extract_instruction_steps(recipe_row: dict) -> tuple[str, ...]:
    """Extract ordered instruction steps from structured or raw instruction text."""

    analyzed_blocks = recipe_row.get("analyzedInstructions", []) or []
    steps: list[str] = []
    for block in analyzed_blocks:
        for step in block.get("steps", []) or []:
            text = str(step.get("step", "")).strip()
            if text:
                steps.append(text)
    if steps:
        return tuple(steps)

    raw_instructions = str(recipe_row.get("instructions") or "").strip()
    if not raw_instructions:
        return tuple()

    lines = [line.strip() for line in raw_instructions.splitlines() if line.strip()]
    if len(lines) <= 1:
        lines = [part.strip() for part in re.split(r"(?<=[.!?])\s+", raw_instructions) if part.strip()]

    cleaned: list[str] = []
    for line in lines:
        without_number = re.sub(r"^\d+[\).\s-]*", "", line).strip()
        if without_number:
            cleaned.append(without_number)
    return tuple(cleaned)


def _extract_dish_types(recipe_row: dict) -> tuple[str, ...]:
    """Extract normalized dish types (lowercased, de-duplicated)."""

    raw_values = recipe_row.get("dishTypes", []) or []
    seen: set[str] = set()
    dish_types: list[str] = []
    for raw_value in raw_values:
        normalized = str(raw_value).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        dish_types.append(normalized)
    return tuple(dish_types)


@lru_cache(maxsize=1)
def load_canonical_name_by_id() -> dict[str, str]:
    """Load canonical ingredient display names keyed by canonical ID."""

    rows = _load_canonical_rows()
    if not rows:
        return {}

    name_by_id: dict[str, str] = {}
    for item in rows:
        canonical_id = str(item.get("id", "")).strip()
        canonical_name = str(item.get("canonical", "")).strip()
        if not canonical_id:
            continue
        if canonical_name:
            name_by_id[canonical_id] = canonical_name
        else:
            name_by_id[canonical_id] = canonical_id.replace("_", " ")
    return name_by_id


@lru_cache(maxsize=1)
def load_recipe_details_by_id() -> dict[str, RecipeDetailSummary]:
    """Load recipe details (image, ingredients, instructions) keyed by recipe id."""

    rows = _read_json_rows(RECIPES_FULL_PATH)
    if not rows:
        return {}

    details_by_id: dict[str, RecipeDetailSummary] = {}
    for row in rows:
        recipe_id = str(row.get("id", "")).strip()
        if not recipe_id:
            continue

        details_by_id[recipe_id] = RecipeDetailSummary(
            image_url=str(row.get("image") or "").strip(),
            dish_types=_extract_dish_types(row),
            ingredient_lines=_extract_ingredient_lines(row),
            instruction_steps=_extract_instruction_steps(row),
        )

    return details_by_id


@lru_cache(maxsize=1)
def load_canonical_phrase_index() -> list[tuple[str, str]]:
    """Build phrase index as (normalized phrase, canonical_id) for canonical+aliases."""

    rows = _load_canonical_rows()
    if not rows:
        return []

    phrase_index: list[tuple[str, str]] = []
    for item in rows:
        canonical_id = str(item.get("id", "")).strip()
        if not canonical_id:
            continue

        phrases = [item.get("canonical", "")] + (item.get("aliases", []) or [])
        for phrase in phrases:
            normalized = normalize_match_text(str(phrase))
            if normalized:
                phrase_index.append((normalized, canonical_id))

    phrase_index.sort(key=lambda pair: len(pair[0]), reverse=True)
    return phrase_index


@lru_cache(maxsize=1)
def load_cheapest_target_by_canonical_id() -> dict[str, CanonicalProductChoice]:
    """Build lookup: canonical ingredient id -> cheapest matched Target product."""

    return load_cheapest_products_by_store(data_paths.TARGET_STORE_KEY)


def _load_cheapest_products_by_flat_path(flat_path: Path) -> dict[str, CanonicalProductChoice]:
    """Build lookup: canonical id -> cheapest matched product from one flat products file."""

    phrase_index = load_canonical_phrase_index()
    products = _read_json_rows(flat_path)
    if not phrase_index or not products:
        return {}

    cheapest: dict[str, CanonicalProductChoice] = {}
    for product in products:
        product_name = str(product.get("name", "")).strip()
        canonical_id = map_text_to_canonical_id(product_name, phrase_index)
        if not canonical_id:
            continue

        price_usd = parse_price_to_usd(product.get("price"))
        if price_usd is None:
            continue

        existing = cheapest.get(canonical_id)
        if existing is not None and price_usd >= existing.price_usd:
            continue

        cheapest[canonical_id] = CanonicalProductChoice(
            canonical_id=canonical_id,
            product_name=product_name,
            price_usd=price_usd,
            category=str(product.get("category", "")),
        )
    return cheapest


@lru_cache(maxsize=1)
def load_cheapest_walmart_by_canonical_id() -> dict[str, CanonicalProductChoice]:
    """Build lookup: canonical ingredient id -> cheapest matched Walmart product."""

    return load_cheapest_products_by_store(data_paths.WALMART_STORE_KEY)


@lru_cache(maxsize=1)
def load_cheapest_bjs_by_canonical_id() -> dict[str, CanonicalProductChoice]:
    """Build lookup: canonical ingredient id -> cheapest matched BJ's product."""

    return load_cheapest_products_by_store(data_paths.BJS_STORE_KEY)


@lru_cache(maxsize=1)
def load_cheapest_whole_foods_by_canonical_id() -> dict[str, CanonicalProductChoice]:
    """Build lookup: canonical ingredient id -> cheapest matched Whole Foods product."""

    return load_cheapest_products_by_store(data_paths.WHOLE_FOODS_STORE_KEY)


@lru_cache(maxsize=len(data_paths.SUPPORTED_STORE_KEYS))
def load_cheapest_products_by_store(store_name: str) -> dict[str, CanonicalProductChoice]:
    """Build lookup for one store: canonical ingredient id -> cheapest matched product."""

    return _load_cheapest_products_by_flat_path(_store_products_flat_path(store_name))


@lru_cache(maxsize=len(data_paths.SUPPORTED_STORE_KEYS))
def load_recipe_coverage_by_store(store_name: str) -> dict[str, RecipeCoverageSummary]:
    """Build coverage map for one store: recipe id -> coverage summary and estimated ingredient cost."""

    recipe_rows = _read_json_rows(_store_recipe_coverage_path(store_name))
    cheapest_lookup = load_cheapest_products_by_store(store_name)
    if not recipe_rows:
        return {}

    coverage_by_id: dict[str, RecipeCoverageSummary] = {}
    for row in recipe_rows:
        recipe_id = str(row.get("id", "")).strip()
        if not recipe_id:
            continue

        canonical_unique = _dedupe_canonical_ids(row.get("canonical_ingredients", []) or [])

        covered: list[str] = []
        missing: list[str] = []
        estimated_cost = 0.0
        for canonical_id in canonical_unique:
            choice = cheapest_lookup.get(canonical_id)
            if choice is None:
                missing.append(canonical_id)
                continue
            covered.append(canonical_id)
            estimated_cost += choice.price_usd

        coverage_ratio = (len(covered) / len(canonical_unique)) if canonical_unique else 0.0
        coverage_by_id[recipe_id] = RecipeCoverageSummary(
            covered_canonical=tuple(covered),
            missing_canonical=tuple(missing),
            estimated_cost_usd=round(estimated_cost, 2),
            coverage_ratio=coverage_ratio,
        )

    return coverage_by_id


def _dedupe_canonical_ids(canonical_ids: list[object]) -> list[str]:
    """Return canonical IDs in input order, removing blanks/duplicates."""

    seen: set[str] = set()
    canonical_unique: list[str] = []
    for canonical_id in canonical_ids:
        normalized_id = str(canonical_id).strip()
        if not normalized_id or normalized_id in seen:
            continue
        seen.add(normalized_id)
        canonical_unique.append(normalized_id)
    return canonical_unique


@lru_cache(maxsize=1)
def load_recipe_coverage_by_id() -> dict[str, RecipeCoverageSummary]:
    """Backward-compatible helper returning Target recipe coverage."""

    return load_recipe_coverage_by_store("Target")


@lru_cache(maxsize=1)
def load_recipe_coverage_walmart_by_id() -> dict[str, RecipeCoverageSummary]:
    """Convenience helper returning Walmart recipe coverage."""

    return load_recipe_coverage_by_store("Walmart")


@lru_cache(maxsize=1)
def load_recipe_coverage_bjs_by_id() -> dict[str, RecipeCoverageSummary]:
    """Convenience helper returning BJ's recipe coverage."""

    return load_recipe_coverage_by_store("BJs")


@lru_cache(maxsize=1)
def load_recipe_coverage_whole_foods_by_id() -> dict[str, RecipeCoverageSummary]:
    """Convenience helper returning Whole Foods recipe coverage."""

    return load_recipe_coverage_by_store("Whole Foods")


@lru_cache(maxsize=len(data_paths.SUPPORTED_STORE_KEYS))
def load_real_recipes(store_name: str = "Target") -> list[RealRecipe]:
    """Load nutrition recipes and enrich them with store coverage and estimated costs."""

    rows = _read_json_rows(RECIPES_NUTRITION_PATH)
    if not rows:
        return []

    coverage_by_id = load_recipe_coverage_by_store(store_name)
    details_by_id = load_recipe_details_by_id()
    recipes: list[RealRecipe] = []
    for item in rows:
        recipe_id = str(item.get("id", "")).strip()
        if not recipe_id:
            continue

        nutrition_tuple = _parse_recipe_nutrition(item.get("nutrition", {}))
        if nutrition_tuple is None:
            continue
        calories, protein, carbs, fat = nutrition_tuple
        if calories <= 0:
            continue

        coverage = coverage_by_id.get(recipe_id, EMPTY_COVERAGE_SUMMARY)
        details = details_by_id.get(recipe_id, EMPTY_RECIPE_DETAIL_SUMMARY)

        recipes.append(
            RealRecipe(
                id=recipe_id,
                title=(item.get("title") or "Untitled Recipe").strip(),
                calories=calories,
                protein_g=protein,
                carbs_g=carbs,
                fat_g=fat,
                estimated_cost_usd=coverage.estimated_cost_usd,
                covered_canonical_count=len(coverage.covered_canonical),
                missing_canonical_count=len(coverage.missing_canonical),
                coverage_ratio=coverage.coverage_ratio,
                image_url=details.image_url,
                dish_types=details.dish_types,
                ingredient_lines=details.ingredient_lines,
                instruction_steps=details.instruction_steps,
            )
        )

    return recipes


def _parse_recipe_nutrition(nutrition: dict[str, Any]) -> Optional[tuple[float, float, float, float]]:
    """Parse recipe nutrition payload into calories/protein/carbs/fat floats."""

    try:
        return (
            float(nutrition.get("calories")),
            float(nutrition.get("protein")),
            float(nutrition.get("carbs")),
            float(nutrition.get("fat")),
        )
    except (TypeError, ValueError):
        return None


def clear_caches() -> None:
    """Clear all data-access caches, useful for tests after path monkeypatching."""

    load_canonical_name_by_id.cache_clear()
    load_recipe_details_by_id.cache_clear()
    load_canonical_phrase_index.cache_clear()
    load_cheapest_target_by_canonical_id.cache_clear()
    load_cheapest_walmart_by_canonical_id.cache_clear()
    load_cheapest_bjs_by_canonical_id.cache_clear()
    load_cheapest_whole_foods_by_canonical_id.cache_clear()
    load_cheapest_products_by_store.cache_clear()
    load_recipe_coverage_by_store.cache_clear()
    load_recipe_coverage_by_id.cache_clear()
    load_recipe_coverage_walmart_by_id.cache_clear()
    load_recipe_coverage_bjs_by_id.cache_clear()
    load_recipe_coverage_whole_foods_by_id.cache_clear()
    load_real_recipes.cache_clear()
