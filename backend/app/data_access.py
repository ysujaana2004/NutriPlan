"""
Data loading and enrichment layer for recipes, canonical ingredients, and Target products.

Primary responsibilities:
1. Read local JSON datasets from backend/data.
2. Build canonical phrase indexes from canonical+alias definitions.
3. Map Target products to canonical ingredients and choose cheapest options.
4. Join recipe canonical-coverage data with nutrition rows.
5. Produce enriched RealRecipe objects for optimizer scoring.

Caching strategy:
- Uses lru_cache for expensive dataset loads and lookups.
- Exposes clear_caches() so tests can safely monkeypatch file paths.

Why this layer matters:
- It is the bridge between offline preprocessing outputs
  (recipes-with-canonical, target_products_flat, recipes-nutrition)
  and runtime optimization inputs.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .matching import map_text_to_canonical_id, normalize_match_text, parse_price_to_usd


RECIPES_NUTRITION_PATH = Path(__file__).resolve().parent.parent / "data" / "recipes-nutrition.json"
RECIPES_RANDOM_FULL_PATH = Path(__file__).resolve().parent.parent / "data" / "recipes-random-full.json"
TARGET_PRODUCTS_FLAT_PATH = Path(__file__).resolve().parent.parent / "data" / "target_products_flat.json"
RECIPES_WITH_CANONICAL_PATH = Path(__file__).resolve().parent.parent / "data" / "recipes-with-canonical.json"
CANONICAL_INGREDIENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "canonical_ingredients.json"
CANONICAL_INGREDIENTS_FALLBACK_PATH = Path(__file__).resolve().parent.parent / "data" / "canconical_ingredients.json"


@dataclass(frozen=True)
class RealRecipe:
    """Nutrition recipe row enriched with Target coverage and estimated ingredient cost."""

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
    """Cheapest known Target product match for one canonical ingredient id."""

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
    """Renderable details for one recipe id, pulled from recipes-random-full.json."""

    image_url: str
    dish_types: tuple[str, ...]
    ingredient_lines: tuple[tuple[str, str], ...]
    instruction_steps: tuple[str, ...]


def canonical_ingredients_file_path() -> Path:
    """Return the canonical ingredient file path, supporting naming variants."""

    if CANONICAL_INGREDIENTS_PATH.exists():
        return CANONICAL_INGREDIENTS_PATH
    return CANONICAL_INGREDIENTS_FALLBACK_PATH


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

    canonical_path = canonical_ingredients_file_path()
    if not canonical_path.exists():
        return {}

    try:
        rows = json.loads(canonical_path.read_text(encoding="utf-8"))
    except Exception:
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

    if not RECIPES_RANDOM_FULL_PATH.exists():
        return {}

    try:
        rows = json.loads(RECIPES_RANDOM_FULL_PATH.read_text(encoding="utf-8"))
    except Exception:
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

    canonical_path = canonical_ingredients_file_path()
    if not canonical_path.exists():
        return []

    try:
        rows = json.loads(canonical_path.read_text(encoding="utf-8"))
    except Exception:
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

    if not TARGET_PRODUCTS_FLAT_PATH.exists():
        return {}

    phrase_index = load_canonical_phrase_index()
    if not phrase_index:
        return {}

    try:
        products = json.loads(TARGET_PRODUCTS_FLAT_PATH.read_text(encoding="utf-8"))
    except Exception:
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

        candidate = CanonicalProductChoice(
            canonical_id=canonical_id,
            product_name=product_name,
            price_usd=price_usd,
            category=str(product.get("category", "")),
        )
        existing = cheapest.get(canonical_id)
        if existing is None or candidate.price_usd < existing.price_usd:
            cheapest[canonical_id] = candidate

    return cheapest


@lru_cache(maxsize=1)
def load_recipe_coverage_by_id() -> dict[str, RecipeCoverageSummary]:
    """Build coverage map: recipe id -> coverage summary and estimated ingredient cost."""

    if not RECIPES_WITH_CANONICAL_PATH.exists():
        return {}

    cheapest_lookup = load_cheapest_target_by_canonical_id()
    try:
        recipe_rows = json.loads(RECIPES_WITH_CANONICAL_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

    coverage_by_id: dict[str, RecipeCoverageSummary] = {}
    for row in recipe_rows:
        recipe_id = str(row.get("id", "")).strip()
        if not recipe_id:
            continue

        canonical_ids = row.get("canonical_ingredients", []) or []
        seen: set[str] = set()
        canonical_unique: list[str] = []
        for canonical_id in canonical_ids:
            normalized_id = str(canonical_id).strip()
            if not normalized_id or normalized_id in seen:
                continue
            seen.add(normalized_id)
            canonical_unique.append(normalized_id)

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


@lru_cache(maxsize=1)
def load_real_recipes() -> list[RealRecipe]:
    """Load nutrition recipes and enrich them with Target coverage and estimated costs."""

    if not RECIPES_NUTRITION_PATH.exists():
        return []

    try:
        rows = json.loads(RECIPES_NUTRITION_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

    coverage_by_id = load_recipe_coverage_by_id()
    details_by_id = load_recipe_details_by_id()
    recipes: list[RealRecipe] = []
    for item in rows:
        recipe_id = str(item.get("id", "")).strip()
        if not recipe_id:
            continue

        nutrition = item.get("nutrition", {})
        try:
            calories = float(nutrition.get("calories"))
            protein = float(nutrition.get("protein"))
            carbs = float(nutrition.get("carbs"))
            fat = float(nutrition.get("fat"))
        except (TypeError, ValueError):
            continue
        if calories <= 0:
            continue

        coverage = coverage_by_id.get(
            recipe_id,
            RecipeCoverageSummary(
                covered_canonical=tuple(),
                missing_canonical=tuple(),
                estimated_cost_usd=0.0,
                coverage_ratio=0.0,
            ),
        )
        details = details_by_id.get(
            recipe_id,
            RecipeDetailSummary(
                image_url="",
                dish_types=tuple(),
                ingredient_lines=tuple(),
                instruction_steps=tuple(),
            ),
        )

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


def clear_caches() -> None:
    """Clear all data-access caches, useful for tests after path monkeypatching."""

    load_canonical_name_by_id.cache_clear()
    load_recipe_details_by_id.cache_clear()
    load_canonical_phrase_index.cache_clear()
    load_cheapest_target_by_canonical_id.cache_clear()
    load_recipe_coverage_by_id.cache_clear()
    load_real_recipes.cache_clear()
