"""
Shared planner helpers used by both demo and optimized planning flows.

What this file provides:
- Deterministic seed generation (stable_int_seed) so results are reproducible.
- Day-level aggregation (compute_day_totals) for meal nutrition/cost totals.
- Start-date parsing with a sensible default.
- Default macro target derivation from calorie targets.

Why this module exists:
- Avoids duplicating common logic in demo_planner.py and optimizer.py.
- Keeps utility-level behavior simple and easy to unit test.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Optional, Tuple

from .schemas import Meal, Nutrition


def stable_int_seed(*parts: str) -> int:
    """Convert input strings into a deterministic integer seed."""

    joined = "|".join(parts).encode("utf-8")
    digest = hashlib.sha256(joined).hexdigest()
    return int(digest[:8], 16)


def compute_day_totals(meals: list[Meal]) -> Tuple[Nutrition, float]:
    """Sum nutrition and cost fields for one day of meals."""

    calories = sum(meal.nutrition.calories for meal in meals)
    protein = sum(meal.nutrition.protein_g for meal in meals)
    carbs = sum(meal.nutrition.carbs_g for meal in meals)
    fat = sum(meal.nutrition.fat_g for meal in meals)
    cost = round(sum(meal.estimated_cost_usd for meal in meals), 2)

    return (
        Nutrition(
            calories=calories,
            protein_g=protein,
            carbs_g=carbs,
            fat_g=fat,
        ),
        cost,
    )


def parse_start_date(start_date: Optional[str]) -> date:
    """Parse YYYY-MM-DD start date or return today's date if omitted."""

    if not start_date:
        return date.today()

    year, month, day = map(int, start_date.split("-"))
    return date(year, month, day)


def default_daily_macro_targets(calories_per_day: int) -> tuple[float, float, float]:
    """Return default daily macro targets using a 30/40/30 calorie split."""

    protein_g = (calories_per_day * 0.30) / 4.0
    carbs_g = (calories_per_day * 0.40) / 4.0
    fat_g = (calories_per_day * 0.30) / 9.0
    return protein_g, carbs_g, fat_g
