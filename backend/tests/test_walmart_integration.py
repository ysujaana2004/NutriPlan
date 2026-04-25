"""Unit tests for Walmart data integration and optimizer enrichment."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from app import data_access
from app import main as api_main


def _write_json(path: Path, payload: object) -> None:
    """Write JSON payload to disk with readable indentation."""

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class TestWalmartIntegration(unittest.TestCase):
    """Tests for Walmart cheapest lookup, coverage, and optimizer usage."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp.name)

        self.canonical_path = self.tmp_dir / "canonical_ingredients.json"
        self.fallback_canonical_path = self.tmp_dir / "canconical_ingredients.json"
        self.walmart_flat_path = self.tmp_dir / "walmart_products_flat.json"
        self.recipes_with_canonical_walmart_path = self.tmp_dir / "recipes-with-canonical-walmart.json"
        self.recipes_nutrition_path = self.tmp_dir / "recipes-nutrition.json"
        self.recipes_full_path = self.tmp_dir / "recipes-full.json"

        _write_json(
            self.canonical_path,
            [
                {"id": "olive_oil", "canonical": "olive oil", "aliases": ["extra virgin olive oil"]},
                {"id": "chicken_breast", "canonical": "chicken breast", "aliases": ["boneless skinless chicken breast"]},
                {"id": "rice", "canonical": "rice", "aliases": ["white rice"]},
            ],
        )

        _write_json(
            self.walmart_flat_path,
            [
                {"category": "oils", "name": "Great Value Extra Virgin Olive Oil", "price": "$7.49", "unit_price": "$0.47/oz"},
                {"category": "oils", "name": "Premium Olive Oil", "price": "$9.99", "unit_price": "$0.62/oz"},
                {"category": "chicken", "name": "Boneless Skinless Chicken Breast Family Pack", "price": "$8.99", "unit_price": "$0.56/oz"},
                {"category": "rice", "name": "Great Value Long Grain White Rice", "price": "$3.49", "unit_price": "$0.07/oz"},
            ],
        )

        _write_json(
            self.recipes_with_canonical_walmart_path,
            [
                {
                    "id": 201,
                    "title": "Rice Bowl",
                    "canonical_ingredients": ["rice", "olive_oil"],
                    "covered_canonical": ["rice", "olive_oil"],
                    "missing_canonical": [],
                    "ignored_pantry_items": [],
                    "raw_ingredients_sample": ["rice", "olive oil"],
                },
                {
                    "id": 202,
                    "title": "Chicken Rice Bowl",
                    "canonical_ingredients": ["chicken_breast", "rice", "olive_oil"],
                    "covered_canonical": ["chicken_breast", "rice", "olive_oil"],
                    "missing_canonical": [],
                    "ignored_pantry_items": [],
                    "raw_ingredients_sample": ["chicken breast", "rice", "olive oil"],
                },
                {
                    "id": 203,
                    "title": "Chicken Olive Rice Dinner",
                    "canonical_ingredients": ["chicken_breast", "rice", "olive_oil"],
                    "covered_canonical": ["chicken_breast", "rice", "olive_oil"],
                    "missing_canonical": [],
                    "ignored_pantry_items": [],
                    "raw_ingredients_sample": ["chicken breast", "rice", "olive oil"],
                },
            ],
        )

        _write_json(
            self.recipes_nutrition_path,
            [
                {"id": 201, "title": "Rice Bowl", "nutrition": {"calories": 640, "protein": 18, "carbs": 92, "fat": 20}},
                {"id": 202, "title": "Chicken Rice Bowl", "nutrition": {"calories": 790, "protein": 55, "carbs": 65, "fat": 24}},
                {"id": 203, "title": "Chicken Olive Rice Dinner", "nutrition": {"calories": 820, "protein": 52, "carbs": 66, "fat": 27}},
            ],
        )

        _write_json(
            self.recipes_full_path,
            [
                {
                    "id": 201,
                    "title": "Rice Bowl",
                    "image": "https://example.com/rice-bowl.jpg",
                    "dishTypes": ["breakfast", "lunch"],
                    "extendedIngredients": [
                        {"name": "rice", "original": "1 cup rice"},
                        {"name": "olive oil", "original": "1 tbsp olive oil"},
                    ],
                    "analyzedInstructions": [
                        {"steps": [{"number": 1, "step": "Cook rice."}, {"number": 2, "step": "Drizzle olive oil."}]}
                    ],
                    "instructions": "",
                },
                {
                    "id": 202,
                    "title": "Chicken Rice Bowl",
                    "image": "https://example.com/chicken-rice.jpg",
                    "dishTypes": ["lunch", "main course", "main dish", "dinner"],
                    "extendedIngredients": [
                        {"name": "chicken breast", "original": "8 oz chicken breast"},
                        {"name": "rice", "original": "1 cup rice"},
                    ],
                    "analyzedInstructions": [
                        {"steps": [{"number": 1, "step": "Cook chicken."}, {"number": 2, "step": "Serve with rice."}]}
                    ],
                    "instructions": "",
                },
                {
                    "id": 203,
                    "title": "Chicken Olive Rice Dinner",
                    "image": "https://example.com/chicken-olive-rice.jpg",
                    "dishTypes": ["dinner", "main course", "main dish"],
                    "extendedIngredients": [
                        {"name": "chicken breast", "original": "8 oz chicken breast"},
                        {"name": "rice", "original": "1 cup rice"},
                        {"name": "olive oil", "original": "1 tbsp olive oil"},
                    ],
                    "analyzedInstructions": [
                        {"steps": [{"number": 1, "step": "Cook chicken."}, {"number": 2, "step": "Combine with rice and olive oil."}]}
                    ],
                    "instructions": "",
                },
            ],
        )

        self._original_paths = {
            "CANONICAL_INGREDIENTS_PATH": data_access.CANONICAL_INGREDIENTS_PATH,
            "CANONICAL_INGREDIENTS_FALLBACK_PATH": data_access.CANONICAL_INGREDIENTS_FALLBACK_PATH,
            "WALMART_PRODUCTS_FLAT_PATH": data_access.WALMART_PRODUCTS_FLAT_PATH,
            "RECIPES_WITH_CANONICAL_WALMART_PATH": data_access.RECIPES_WITH_CANONICAL_WALMART_PATH,
            "RECIPES_NUTRITION_PATH": data_access.RECIPES_NUTRITION_PATH,
            "RECIPES_FULL_PATH": data_access.RECIPES_FULL_PATH,
        }

        data_access.CANONICAL_INGREDIENTS_PATH = self.canonical_path
        data_access.CANONICAL_INGREDIENTS_FALLBACK_PATH = self.fallback_canonical_path
        data_access.WALMART_PRODUCTS_FLAT_PATH = self.walmart_flat_path
        data_access.RECIPES_WITH_CANONICAL_WALMART_PATH = self.recipes_with_canonical_walmart_path
        data_access.RECIPES_NUTRITION_PATH = self.recipes_nutrition_path
        data_access.RECIPES_FULL_PATH = self.recipes_full_path
        data_access.clear_caches()

    def tearDown(self) -> None:
        data_access.CANONICAL_INGREDIENTS_PATH = self._original_paths["CANONICAL_INGREDIENTS_PATH"]
        data_access.CANONICAL_INGREDIENTS_FALLBACK_PATH = self._original_paths["CANONICAL_INGREDIENTS_FALLBACK_PATH"]
        data_access.WALMART_PRODUCTS_FLAT_PATH = self._original_paths["WALMART_PRODUCTS_FLAT_PATH"]
        data_access.RECIPES_WITH_CANONICAL_WALMART_PATH = self._original_paths["RECIPES_WITH_CANONICAL_WALMART_PATH"]
        data_access.RECIPES_NUTRITION_PATH = self._original_paths["RECIPES_NUTRITION_PATH"]
        data_access.RECIPES_FULL_PATH = self._original_paths["RECIPES_FULL_PATH"]
        data_access.clear_caches()
        self.tmp.cleanup()

    def test_cheapest_walmart_lookup_picks_lowest_matching_product(self) -> None:
        lookup = data_access.load_cheapest_walmart_by_canonical_id()
        self.assertIn("olive_oil", lookup)
        self.assertIn("rice", lookup)
        self.assertAlmostEqual(lookup["olive_oil"].price_usd, 7.49, places=2)

    def test_walmart_coverage_join_builds_estimated_cost(self) -> None:
        coverage = data_access.load_recipe_coverage_walmart_by_id()
        row = coverage["202"]
        self.assertEqual(len(row.missing_canonical), 0)
        self.assertEqual(len(row.covered_canonical), 3)
        self.assertGreater(row.estimated_cost_usd, 0.0)
        self.assertAlmostEqual(row.coverage_ratio, 1.0, places=5)

    def test_optimizer_uses_walmart_store_data(self) -> None:
        plan = asyncio.run(
            api_main.optimized_meal_plan(
                budget=100,
                calories=2200,
                diet="none",
                start_date="2026-03-07",
                zip_code=None,
                store_preference="Walmart",
                protein_target_g=None,
                carbs_target_g=None,
                fat_target_g=None,
            )
        )

        self.assertEqual(len(plan.days), 7)
        self.assertEqual(plan.inputs["recipe_coverage_rows"], 3)
        self.assertEqual(plan.inputs["target_lookup_size"], 3)
        self.assertGreater(plan.week_total_cost_usd, 0.0)
        self.assertIsNotNone(plan.shopping_list)
        assert plan.shopping_list is not None
        self.assertGreater(plan.shopping_list.total_estimated_cost_usd, 0.0)
        self.assertGreater(len(plan.shopping_list.items), 0)
        self.assertTrue(any("Great Value" in item.product_name for item in plan.shopping_list.items))


if __name__ == "__main__":
    unittest.main()
