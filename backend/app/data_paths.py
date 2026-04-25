"""Centralized filesystem paths for recipe and store datasets."""

from __future__ import annotations

from pathlib import Path

from .store_registry import BJS, SUPPORTED_STORE_KEYS, TARGET, WALMART, WHOLE_FOODS


APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
DATA_DIR = BACKEND_DIR / "data"

RECIPES_DIR = DATA_DIR / "recipes"
STORES_DIR = DATA_DIR / "stores"

RECIPES_PATH = RECIPES_DIR / "recipes.json"
RECIPES_FULL_PATH = RECIPES_DIR / "recipes-full.json"
RECIPES_NUTRITION_PATH = RECIPES_DIR / "recipes-nutrition.json"
INGREDIENTS_FROM_RECIPES_PATH = RECIPES_DIR / "ingredients-from-recipes.json"

CANONICAL_INGREDIENTS_PATH = RECIPES_DIR / "canonical_ingredients.json"
CANONICAL_INGREDIENTS_FALLBACK_PATH = RECIPES_DIR / "canconical_ingredients.json"

# Backward-compatible key names used by existing modules/tests.
TARGET_STORE_KEY = TARGET
WALMART_STORE_KEY = WALMART
BJS_STORE_KEY = BJS
WHOLE_FOODS_STORE_KEY = WHOLE_FOODS


def store_dir(store_key: str) -> Path:
    """Return store subdirectory path for a normalized store key."""

    return STORES_DIR / store_key


def store_products_flat_path(store_key: str) -> Path:
    """Return products-flat path for a normalized store key."""

    return store_dir(store_key) / "products_flat.json"


def store_products_by_category_path(store_key: str) -> Path:
    """Return products-by-category path for a normalized store key."""

    return store_dir(store_key) / "products_by_category.json"


def store_recipe_coverage_path(store_key: str) -> Path:
    """Return recipe-coverage path for a normalized store key."""

    return store_dir(store_key) / "recipes-with-canonical.json"
