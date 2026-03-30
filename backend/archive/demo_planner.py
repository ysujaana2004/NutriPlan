"""
Deterministic fake-data planner used by the /demo/meal-plan endpoint.

What this module does:
- Defines small hardcoded meal template catalogs.
- Chooses templates deterministically based on input seed and day index.
- Produces realistic-looking nutrition and cost totals for UI/demo use.

Why it still exists:
- Preserves a stable fallback/demo path while real optimizer evolves.
- Lets frontend integration continue even if real data pipelines are unavailable.

What it does NOT do:
- It does not use real recipe nutrition datasets.
- It does not use Target pricing or canonical ingredient mapping.
- It does not enforce strict budget/calorie optimization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal, Optional

from ..app.planner_utils import compute_day_totals, parse_start_date, stable_int_seed
from ..app.schemas import DayPlan, Diet, Meal, Nutrition, WeeklyPlan


@dataclass(frozen=True)
class MealTemplate:
    """Simple demo recipe template used to generate fake meal entries."""

    name: str
    base_calories: int
    protein_ratio: float
    carbs_ratio: float
    fat_ratio: float


BREAKFAST_CATALOG: list[MealTemplate] = [
    MealTemplate("Greek Yogurt Bowl", 450, 0.055, 0.075, 0.020),
    MealTemplate("Oatmeal + Banana", 500, 0.040, 0.095, 0.020),
    MealTemplate("Egg + Avocado Toast", 550, 0.050, 0.050, 0.035),
    MealTemplate("Protein Smoothie", 600, 0.070, 0.070, 0.020),
    MealTemplate("Cottage Cheese + Fruit", 430, 0.060, 0.060, 0.020),
]

LUNCH_CATALOG: list[MealTemplate] = [
    MealTemplate("Chicken Rice Bowl", 750, 0.060, 0.080, 0.020),
    MealTemplate("Turkey Sandwich + Salad", 700, 0.055, 0.070, 0.025),
    MealTemplate("Tuna Wrap", 650, 0.060, 0.060, 0.025),
    MealTemplate("Lentil Curry + Rice", 780, 0.040, 0.095, 0.020),
    MealTemplate("Beef Stir Fry + Noodles", 820, 0.055, 0.075, 0.030),
]

DINNER_CATALOG: list[MealTemplate] = [
    MealTemplate("Salmon + Veggies", 800, 0.050, 0.035, 0.040),
    MealTemplate("Chicken Pasta", 900, 0.055, 0.090, 0.025),
    MealTemplate("Steak + Potatoes", 950, 0.055, 0.060, 0.040),
    MealTemplate("Tofu Stir Fry", 780, 0.045, 0.070, 0.030),
    MealTemplate("Shrimp Tacos", 850, 0.050, 0.080, 0.025),
]


def calorie_bucket(calories_per_day: int) -> str:
    """Bucket calorie targets to diversify deterministic template picks."""

    if calories_per_day < 1800:
        return "low"
    if calories_per_day < 2500:
        return "mid"
    return "high"


def pick_template(
    catalog: list[MealTemplate],
    seed: int,
    day_index: int,
    meal_index: int,
    bucket: str,
) -> MealTemplate:
    """Deterministically choose one template from a catalog."""

    bucket_offset = {"low": 0, "mid": 1, "high": 2}[bucket]
    idx = (seed + day_index * 7 + meal_index * 13 + bucket_offset) % len(catalog)
    return catalog[idx]


def build_meal_from_template(
    meal_type: Literal["breakfast", "lunch", "dinner"],
    template: MealTemplate,
    target_meal_calories: int,
    estimated_cost_usd: float,
) -> Meal:
    """Convert a template into a response-ready `Meal` object."""

    protein = int(round(template.protein_ratio * target_meal_calories))
    carbs = int(round(template.carbs_ratio * target_meal_calories))
    fat = int(round(template.fat_ratio * target_meal_calories))
    safe_name = template.name.lower().replace(" ", "_").replace("+", "plus").replace("/", "_")

    return Meal(
        recipe_id=f"demo_{meal_type}_{safe_name}",
        meal_type=meal_type,
        name=template.name,
        servings=1,
        nutrition=Nutrition(
            calories=target_meal_calories,
            protein_g=protein,
            carbs_g=carbs,
            fat_g=fat,
        ),
        estimated_cost_usd=round(estimated_cost_usd, 2),
    )


def build_demo_weekly_plan(
    budget: float,
    calories: int,
    diet: Diet,
    start_date: Optional[str],
) -> WeeklyPlan:
    """Generate the existing deterministic fake weekly plan used by the demo endpoint."""

    start = parse_start_date(start_date)
    breakfast_cals = int(calories * 0.30)
    lunch_cals = int(calories * 0.35)
    dinner_cals = calories - breakfast_cals - lunch_cals

    daily_budget = max(budget / 7.0, 1.0)
    seed = stable_int_seed(str(start), str(budget), str(calories), str(diet))
    bucket = calorie_bucket(calories)

    days: list[DayPlan] = []
    for day_index in range(7):
        day_date = start + timedelta(days=day_index)
        breakfast_t = pick_template(BREAKFAST_CATALOG, seed, day_index, 0, bucket)
        lunch_t = pick_template(LUNCH_CATALOG, seed, day_index, 1, bucket)
        dinner_t = pick_template(DINNER_CATALOG, seed, day_index, 2, bucket)

        breakfast_cost = min(daily_budget * 0.25, 5.00)
        lunch_cost = min(daily_budget * 0.35, 8.00)
        dinner_cost = min(daily_budget * 0.40, 12.00)

        meals = [
            build_meal_from_template("breakfast", breakfast_t, breakfast_cals, breakfast_cost),
            build_meal_from_template("lunch", lunch_t, lunch_cals, lunch_cost),
            build_meal_from_template("dinner", dinner_t, dinner_cals, dinner_cost),
        ]

        totals, total_cost = compute_day_totals(meals)
        days.append(
            DayPlan(
                date=day_date.isoformat(),
                meals=meals,
                totals=totals,
                total_cost_usd=total_cost,
            )
        )

    week_totals = Nutrition(
        calories=sum(day.totals.calories for day in days),
        protein_g=sum(day.totals.protein_g for day in days),
        carbs_g=sum(day.totals.carbs_g for day in days),
        fat_g=sum(day.totals.fat_g for day in days),
    )
    week_total_cost = round(sum(day.total_cost_usd for day in days), 2)

    return WeeklyPlan(
        inputs={
            "budget": budget,
            "calories": calories,
            "diet": diet,
            "start_date": start_date,
        },
        days=days,
        week_totals=week_totals,
        week_total_cost_usd=week_total_cost,
    )
