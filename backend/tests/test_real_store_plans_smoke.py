"""Optimizer-style real-data checks for all integrated store plan generation."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _assert_optimizer_success_shape(data: dict, budget: int, calories: int) -> None:
    """Match the same core assertions used in test_optimizer_api success checks."""

    assert "week_totals" in data
    assert "days" in data
    assert len(data["days"]) == 7

    assert data["inputs"]["budget"] == budget
    assert data["inputs"]["calories"] == calories

    assert "week_total_cost_usd" in data
    assert data["week_total_cost_usd"] > 0

    day_1 = data["days"][0]
    assert len(day_1["meals"]) == 3
    for meal in day_1["meals"]:
        assert meal["meal_type"] in ["breakfast", "lunch", "dinner"]
        assert "nutrition" in meal
        assert meal["nutrition"]["calories"] > 0


class TestRealStorePlansSmoke(unittest.TestCase):
    """Equivalent checks to test_optimizer_api, but for all stores with real data."""

    STORES = ("Target", "Walmart", "BJs", "Whole Foods")

    def test_real_data_optimize_success_for_all_stores(self):
        budget = 150
        calories = 2000
        for store in self.STORES:
            response = client.get(
                f"/optimize/meal-plan?budget={budget}&calories={calories}&diet=none&store_preference={store}"
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            _assert_optimizer_success_shape(data, budget=budget, calories=calories)

    def test_real_data_optimize_respects_calorie_target_for_all_stores(self):
        target_daily_calories = 2000
        for store in self.STORES:
            response = client.get(
                f"/optimize/meal-plan?budget=150&calories={target_daily_calories}&diet=none&store_preference={store}"
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()

            total_week_calories = data["week_totals"]["calories"]
            average_daily_calories = total_week_calories / 7
            lower_bound = target_daily_calories * 0.85
            upper_bound = target_daily_calories * 1.15
            self.assertTrue(lower_bound <= average_daily_calories <= upper_bound)


if __name__ == "__main__":
    unittest.main()
