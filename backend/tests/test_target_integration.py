"""Unit tests for Target data integration and optimizer enrichment."""

from __future__ import annotations

import json
import tempfile
import unittest
import asyncio
from pathlib import Path

#from backend.app import data_access
#from backend.app import main as api_main
#from backend.app.matching import parse_price_to_usd


from app import data_access
from app import main as api_main
from app.matching import parse_price_to_usd


def _write_json(path: Path, payload: object) -> None:
    """Write JSON payload to disk with readable indentation."""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class TestTargetIntegration(unittest.TestCase):
    """Tests for price parsing, cheapest-product lookup, and recipe enrichment."""

    def setUp(self) -> None:
        """Create temporary test datasets and point planner paths to them."""
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp.name)

        self.canonical_path = self.tmp_dir / "canonical_ingredients.json"
        self.fallback_canonical_path = self.tmp_dir / "canconical_ingredients.json"
        self.target_flat_path = self.tmp_dir / "target_products_flat.json"
        self.recipes_with_canonical_path = self.tmp_dir / "recipes-with-canonical-target.json"
        self.recipes_nutrition_path = self.tmp_dir / "recipes-nutrition.json"
        self.recipes_full_path = self.tmp_dir / "recipes-full.json"

        _write_json(
            self.canonical_path,
            [
                {
                    "id": "olive_oil",
                    "canonical": "olive oil",
                    "category": "other",
                    "aliases": ["extra virgin olive oil"],
                },
                {
                    "id": "chicken_breast",
                    "canonical": "chicken breast",
                    "category": "chicken",
                    "aliases": ["boneless skinless chicken breast"],
                },
                {
                    "id": "rice",
                    "canonical": "rice",
                    "category": "pasta_rice_grains",
                    "aliases": ["white rice"],
                },
                {
                    "id": "salmon",
                    "canonical": "salmon",
                    "category": "fish and seafood",
                    "aliases": [],
                },
            ],
        )

        _write_json(
            self.target_flat_path,
            [
                {
                    "category": "other",
                    "source_file": "oils.json",
                    "name": "Extra Virgin Olive Oil 16oz",
                    "price": "$9.99",
                    "unit_price": "$0.62/oz",
                },
                {
                    "category": "other",
                    "source_file": "oils.json",
                    "name": "Target Olive Oil Blend",
                    "price": "$7.49 - $12.99",
                    "unit_price": "$0.47/oz",
                },
                {
                    "category": "chicken",
                    "source_file": "chicken.json",
                    "name": "Boneless Skinless Chicken Breast",
                    "price": "$8.99",
                    "unit_price": "$0.56/oz",
                },
                {
                    "category": "pasta_rice_grains",
                    "source_file": "rice.json",
                    "name": "Long Grain White Rice",
                    "price": "$3.49",
                    "unit_price": "$0.07/oz",
                },
                {
                    "category": "fish and seafood",
                    "source_file": "fish.json",
                    "name": "Atlantic Salmon Fillet",
                    "price": "$11.99",
                    "unit_price": "$0.75/oz",
                },
            ],
        )

        _write_json(
            self.recipes_with_canonical_path,
            [
                {
                    "id": 101,
                    "title": "Oatmeal Bowl",
                    "canonical_ingredients": ["rice", "olive_oil"],
                    "covered_canonical": ["rice", "olive_oil"],
                    "missing_canonical": [],
                    "ignored_pantry_items": [],
                    "raw_ingredients_sample": ["rice", "olive oil"],
                },
                {
                    "id": 102,
                    "title": "Chicken Rice Bowl",
                    "canonical_ingredients": ["chicken_breast", "rice", "olive_oil"],
                    "covered_canonical": ["chicken_breast", "rice", "olive_oil"],
                    "missing_canonical": [],
                    "ignored_pantry_items": [],
                    "raw_ingredients_sample": ["chicken breast", "rice", "olive oil"],
                },
                {
                    "id": 103,
                    "title": "Salmon Dinner",
                    "canonical_ingredients": ["salmon", "rice"],
                    "covered_canonical": ["salmon", "rice"],
                    "missing_canonical": [],
                    "ignored_pantry_items": [],
                    "raw_ingredients_sample": ["salmon", "rice"],
                },
            ],
        )

        _write_json(
            self.recipes_nutrition_path,
            [
                {"id": 101, "title": "Oatmeal Bowl", "nutrition": {"calories": 650, "protein": 24, "carbs": 80, "fat": 20}},
                {"id": 102, "title": "Chicken Rice Bowl", "nutrition": {"calories": 780, "protein": 55, "carbs": 65, "fat": 22}},
                {"id": 103, "title": "Salmon Dinner", "nutrition": {"calories": 820, "protein": 48, "carbs": 45, "fat": 35}},
            ],
        )

        _write_json(
            self.recipes_full_path,
            [
                {
                    "id": 101,
                    "title": "Oatmeal Bowl",
                    "image": "https://example.com/oatmeal.jpg",
                    "dishTypes": ["breakfast", "morning meal"],
                    "extendedIngredients": [
                        {"name": "rice", "original": "1 cup rice"},
                        {"name": "olive oil", "original": "1 tbsp olive oil"},
                    ],
                    "analyzedInstructions": [
                        {"steps": [{"number": 1, "step": "Cook the rice."}, {"number": 2, "step": "Drizzle olive oil on top."}]}
                    ],
                    "instructions": "",
                },
                {
                    "id": 102,
                    "title": "Chicken Rice Bowl",
                    "image": "https://example.com/chicken-rice.jpg",
                    "dishTypes": ["lunch", "main course", "main dish", "dinner"],
                    "extendedIngredients": [
                        {"name": "chicken breast", "original": "8 oz chicken breast"},
                        {"name": "rice", "original": "1 cup rice"},
                    ],
                    "analyzedInstructions": [
                        {"steps": [{"number": 1, "step": "Season and cook the chicken."}, {"number": 2, "step": "Serve over rice."}]}
                    ],
                    "instructions": "",
                },
                {
                    "id": 103,
                    "title": "Salmon Dinner",
                    "image": "https://example.com/salmon.jpg",
                    "dishTypes": ["main course", "main dish", "dinner"],
                    "extendedIngredients": [
                        {"name": "salmon", "original": "2 salmon fillets"},
                        {"name": "rice", "original": "1 cup rice"},
                    ],
                    "analyzedInstructions": [
                        {"steps": [{"number": 1, "step": "Bake the salmon."}, {"number": 2, "step": "Plate with rice."}]}
                    ],
                    "instructions": "",
                },
            ],
        )

        self._original_paths = {
            "CANONICAL_INGREDIENTS_PATH": data_access.CANONICAL_INGREDIENTS_PATH,
            "CANONICAL_INGREDIENTS_FALLBACK_PATH": data_access.CANONICAL_INGREDIENTS_FALLBACK_PATH,
            "TARGET_PRODUCTS_FLAT_PATH": data_access.TARGET_PRODUCTS_FLAT_PATH,
            "RECIPES_WITH_CANONICAL_PATH": data_access.RECIPES_WITH_CANONICAL_PATH,
            "RECIPES_NUTRITION_PATH": data_access.RECIPES_NUTRITION_PATH,
            "RECIPES_FULL_PATH": data_access.RECIPES_FULL_PATH,
        }

        data_access.CANONICAL_INGREDIENTS_PATH = self.canonical_path
        data_access.CANONICAL_INGREDIENTS_FALLBACK_PATH = self.fallback_canonical_path
        data_access.TARGET_PRODUCTS_FLAT_PATH = self.target_flat_path
        data_access.RECIPES_WITH_CANONICAL_PATH = self.recipes_with_canonical_path
        data_access.RECIPES_NUTRITION_PATH = self.recipes_nutrition_path
        data_access.RECIPES_FULL_PATH = self.recipes_full_path

        self._clear_cached_loaders()

    def tearDown(self) -> None:
        """Restore global planner paths and clear caches between tests."""
        data_access.CANONICAL_INGREDIENTS_PATH = self._original_paths["CANONICAL_INGREDIENTS_PATH"]
        data_access.CANONICAL_INGREDIENTS_FALLBACK_PATH = self._original_paths["CANONICAL_INGREDIENTS_FALLBACK_PATH"]
        data_access.TARGET_PRODUCTS_FLAT_PATH = self._original_paths["TARGET_PRODUCTS_FLAT_PATH"]
        data_access.RECIPES_WITH_CANONICAL_PATH = self._original_paths["RECIPES_WITH_CANONICAL_PATH"]
        data_access.RECIPES_NUTRITION_PATH = self._original_paths["RECIPES_NUTRITION_PATH"]
        data_access.RECIPES_FULL_PATH = self._original_paths["RECIPES_FULL_PATH"]

        self._clear_cached_loaders()
        self.tmp.cleanup()

    def _clear_cached_loaders(self) -> None:
        """Clear all relevant in-process caches after path changes."""
        data_access.clear_caches()

    def test_parse_price_to_usd_handles_common_formats(self) -> None:
        """Price parser should handle plain, range, and numeric-with-text formats."""
        self.assertEqual(parse_price_to_usd("$7.99"), 7.99)
        self.assertEqual(parse_price_to_usd("$7.49 - $12.99"), 7.49)
        self.assertEqual(parse_price_to_usd("$13.99 max price"), 13.99)
        self.assertIsNone(parse_price_to_usd("N/A"))

    def test_cheapest_lookup_picks_lowest_matching_product(self) -> None:
        """Cheapest lookup should map canonical IDs and choose minimum parsed price."""
        lookup = data_access.load_cheapest_target_by_canonical_id()
        self.assertIn("olive_oil", lookup)
        self.assertIn("rice", lookup)
        self.assertAlmostEqual(lookup["olive_oil"].price_usd, 7.49, places=2)
        self.assertIn("olive oil", lookup["olive_oil"].product_name.lower())

    def test_recipe_coverage_join_builds_estimated_cost(self) -> None:
        """Coverage join should compute coverage ratio and recipe-level estimated cost."""
        coverage = data_access.load_recipe_coverage_by_id()
        row = coverage["102"]
        self.assertEqual(len(row.missing_canonical), 0)
        self.assertEqual(len(row.covered_canonical), 3)
        self.assertGreater(row.estimated_cost_usd, 0.0)
        self.assertAlmostEqual(row.coverage_ratio, 1.0, places=5)

    def test_optimizer_uses_enriched_recipes_and_returns_non_zero_costs(self) -> None:
        """Optimizer output should include non-zero meal costs from Target integration."""
        plan = asyncio.run(api_main.optimized_meal_plan(
            budget=90,
            calories=2200,
            diet="none",
            start_date="2026-03-07",
            zip_code=None,
            store_preference="Target",
            protein_target_g=None,
            carbs_target_g=None,
            fat_target_g=None,
        ))

        self.assertEqual(len(plan.days), 7)
        self.assertEqual(plan.inputs["target_lookup_size"], 4)
        self.assertEqual(plan.inputs["recipe_coverage_rows"], 3)
        self.assertGreater(plan.week_total_cost_usd, 0.0)
        self.assertTrue(all(meal.estimated_cost_usd > 0 for meal in plan.days[0].meals))
        self.assertIsNotNone(plan.shopping_list)
        self.assertGreater(plan.shopping_list.total_estimated_cost_usd, 0.0)
        self.assertGreater(len(plan.shopping_list.items), 0)
        self.assertGreater(len(plan.days[0].meals[0].ingredients), 0)
        self.assertGreater(len(plan.days[0].meals[0].instructions), 0)

    def test_optimizer_prefers_breakfast_dish_types_for_breakfast_slot(self) -> None:
        """Breakfast slot should favor recipes tagged as breakfast/morning meal."""
        plan = asyncio.run(api_main.optimized_meal_plan(
            budget=90,
            calories=2200,
            diet="none",
            start_date="2026-03-07",
            zip_code=None,
            store_preference="Target",
            protein_target_g=None,
            carbs_target_g=None,
            fat_target_g=None,
        ))

        breakfast_names = [meal.name for day in plan.days for meal in day.meals if meal.meal_type == "breakfast"]
        self.assertEqual(len(breakfast_names), 7)
        self.assertTrue(all(name == "Oatmeal Bowl" for name in breakfast_names))


if __name__ == "__main__":
    unittest.main()
