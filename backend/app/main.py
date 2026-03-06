"""
Meal Planner Demo API (Week 1)

Purpose of this file:
- Provide a *clickable end-to-end demo* for the frontend in Week 1.
- We intentionally return FAKE (hardcoded) meal plan data.
- The frontend can rely on a stable JSON shape ("API contract").

What this is NOT (yet):
- Not a real meal planner algorithm
- Not real grocery pricing
- Not real USDA nutrition aggregation

What this IS:
- A reliable endpoint the frontend can call:
    GET /demo/meal-plan?budget=70&calories=2200&diet=none

What it returns:
- A weekly plan (7 days)
- Each day has 3 meals (breakfast/lunch/dinner)
- Each meal includes simple nutrition + an estimated cost
- Each day includes totals (nutrition + cost)
- The week includes totals (nutrition + cost)

Why this matters:
- The team can build UI immediately without waiting for real logic.
- Later weeks can “swap in” real logic behind the same response schema.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from functools import lru_cache

from datetime import date, timedelta
from pathlib import Path
from typing import List, Literal, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ------------------------------------------------------------------------------
# 1) FastAPI app setup
# ------------------------------------------------------------------------------

app = FastAPI(
    title="Meal Planner Demo API",
    description="Week 1: Fake-data endpoint for an end-to-end clickable demo.",
    version="0.1.0",
)

# CORS (Cross-Origin Resource Sharing) allows your frontend (often on another port)
# to call your backend in the browser.
#
# In Week 1, we keep this permissive for speed. Later, you should restrict
# allow_origins to your real frontend domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO later: replace with ["http://localhost:3000", ...]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# 2) Types + Response Models (this is your "API Contract")
# ------------------------------------------------------------------------------

# A small set of accepted diet values. Frontend can send these.
# In Week 1 we don't deeply use them, but we keep the parameter so the UI is real.
Diet = Literal["none", "vegetarian", "high_protein", "low_carb"]


class Nutrition(BaseModel):
    """
    Nutrition summary for a meal/day/week.

    Why these fields?
    - They are common, easy for UI to display, and simple for Week 1.
    - Later you can add fiber, sugar, sodium, etc. if needed.
    """
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int


class Meal(BaseModel):
    """
    Represents a single meal in a day plan.

    Fields:
    - meal_type: breakfast/lunch/dinner (keeps UI consistent)
    - name: human-friendly name shown in UI
    - servings: integer number of servings
    - nutrition: Nutrition totals for this meal
    - estimated_cost_usd: fake cost for Week 1 demo (float for easy UI display)
    """
    meal_type: Literal["breakfast", "lunch", "dinner"]
    name: str
    servings: int
    nutrition: Nutrition
    estimated_cost_usd: float


class DayPlan(BaseModel):
    """
    Represents one day in the weekly plan.

    Fields:
    - date: ISO string "YYYY-MM-DD" (easy to parse/display)
    - meals: list of Meal objects
    - totals: nutrition total for the day (sum of meals)
    - total_cost_usd: total cost for the day (sum of meal costs)
    """
    date: str
    meals: List[Meal]
    totals: Nutrition
    total_cost_usd: float


class WeeklyPlan(BaseModel):
    """
    Represents the full weekly plan returned by the API.

    Fields:
    - inputs: what the user requested (useful for debugging + UI confirmation)
    - days: list of 7 DayPlan objects
    - week_totals: nutrition totals across all 7 days
    - week_total_cost_usd: total cost across all 7 days
    """
    inputs: dict
    days: List[DayPlan]
    week_totals: Nutrition
    week_total_cost_usd: float



# ------------------------------------------------------------------------------
# 3A) "recipe catalog" for Week 2 demo diversity
# ------------------------------------------------------------------------------

@dataclass(frozen=True)
class MealTemplate:
    """
    A simple fake recipe template used ONLY for the demo.
    Later, replace these with real recipes + USDA nutrition.
    """
    name: str
    # A "base" calorie amount for this meal template (for selection purposes)
    base_calories: int
    # Rough macro ratios per calorie (very fake, but plausible-looking)
    protein_ratio: float  # grams protein per calorie
    carbs_ratio: float    # grams carbs per calorie
    fat_ratio: float      # grams fat per calorie


# Small catalogs per meal type.
# Keep them modest (8-12 total per meal type is plenty for a demo).
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

RECIPES_NUTRITION_PATH = Path(__file__).resolve().parent.parent / "data" / "recipes-nutrition.json"
MEAL_SPLITS: dict[Literal["breakfast", "lunch", "dinner"], float] = {
    "breakfast": 0.30,
    "lunch": 0.35,
    "dinner": 0.35,
}

BREAKFAST_HINTS = {
    "breakfast",
    "oat",
    "smoothie",
    "pancake",
    "omelet",
    "toast",
    "yogurt",
    "muffin",
    "egg",
}
DINNER_HINTS = {
    "steak",
    "salmon",
    "chicken",
    "pasta",
    "curry",
    "stir",
    "taco",
    "soup",
    "burger",
    "rice",
}
SWEET_HINTS = {
    "cake",
    "pie",
    "cookie",
    "brownie",
    "chocolate",
    "cupcake",
    "frosting",
    "treat",
}


@dataclass(frozen=True)
class RealRecipe:
    id: str
    title: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


@lru_cache(maxsize=1)
def _load_real_recipes() -> list[RealRecipe]:
    """
    Load nutrition-ready recipes from backend/data/recipes-nutrition.json.
    Cached in-process because this dataset is static during normal development runs.
    """
    if not RECIPES_NUTRITION_PATH.exists():
        return []

    try:
        raw_items = json.loads(RECIPES_NUTRITION_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

    recipes: list[RealRecipe] = []
    for item in raw_items:
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

        recipes.append(
            RealRecipe(
                id=str(item.get("id", "")),
                title=(item.get("title") or "Untitled Recipe").strip(),
                calories=calories,
                protein_g=protein,
                carbs_g=carbs,
                fat_g=fat,
            )
        )

    return recipes


def _stable_int_seed(*parts: str) -> int:
    """
    Convert arbitrary strings into a stable integer seed.
    This makes meal selection deterministic across runs (same inputs -> same plan).
    """
    joined = "|".join(parts).encode("utf-8")
    digest = hashlib.sha256(joined).hexdigest()
    # Use a chunk of the hash as an integer seed
    return int(digest[:8], 16)


def _calorie_bucket(calories_per_day: int) -> str:
    """
    Bucket daily calories so that changing calories often changes meal choices.
    Adjust thresholds however you want for your demo.
    """
    if calories_per_day < 1800:
        return "low"
    if calories_per_day < 2500:
        return "mid"
    return "high"


def _pick_template(
    catalog: list[MealTemplate],
    seed: int,
    day_index: int,
    meal_index: int,
    bucket: str,
) -> MealTemplate:
    """
    Deterministically pick an item from a catalog.

    Why day_index + meal_index?
    - Ensures variety across days and meal slots (breakfast/lunch/dinner)
    """
    # Bucket shifts the index so different calorie targets often pick different meals
    bucket_offset = {"low": 0, "mid": 1, "high": 2}[bucket]

    idx = (seed + day_index * 7 + meal_index * 13 + bucket_offset) % len(catalog)
    return catalog[idx]


def _build_meal_from_template(
    meal_type: Literal["breakfast", "lunch", "dinner"],
    template: MealTemplate,
    target_meal_calories: int,
    estimated_cost_usd: float,
) -> Meal:
    """
    Turn a MealTemplate into your existing Meal response object.

    We *scale* macros based on target calories (still fake but consistent),
    so the UI sees realistic variation day-to-day.
    """
    # Scale macros from ratios * calories
    protein = int(round(template.protein_ratio * target_meal_calories))
    carbs = int(round(template.carbs_ratio * target_meal_calories))
    fat = int(round(template.fat_ratio * target_meal_calories))

    return Meal(
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

# ------------------------------------------------------------------------------
# 3) Helper functions
# ------------------------------------------------------------------------------

def compute_day_totals(meals: List[Meal]) -> Tuple[Nutrition, float]:
    """
    Sum nutrition + cost across a list of meals.

    Parameters
    ----------
    meals:
        List of Meal objects for a single day.

    Returns
    -------
    (nutrition_totals, cost_total):
        nutrition_totals is a Nutrition object with summed macros/calories.
        cost_total is the summed cost (rounded to 2 decimals).
    """
    calories = sum(m.nutrition.calories for m in meals)
    protein = sum(m.nutrition.protein_g for m in meals)
    carbs = sum(m.nutrition.carbs_g for m in meals)
    fat = sum(m.nutrition.fat_g for m in meals)

    cost = round(sum(m.estimated_cost_usd for m in meals), 2)

    return Nutrition(
        calories=calories,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
    ), cost


def parse_start_date(start_date: Optional[str]) -> date:
    """
    Parse an ISO date string (YYYY-MM-DD) into a datetime.date.

    Why we have this helper:
    - Keeps endpoint code simpler.
    - Gives one place to change parsing/validation later.

    Week 1 simplification:
    - If start_date is missing, we just use today's date.
    - If it's provided, we assume it's correctly formatted.
      (You can harden this later with better error handling.)
    """
    if not start_date:
        return date.today()

    year, month, day = map(int, start_date.split("-"))
    return date(year, month, day)


def _default_daily_macro_targets(calories_per_day: int) -> tuple[float, float, float]:
    """
    Derive macro targets from calories using a simple 30/40/30 split.
    """
    protein_g = (calories_per_day * 0.30) / 4.0
    carbs_g = (calories_per_day * 0.40) / 4.0
    fat_g = (calories_per_day * 0.30) / 9.0
    return protein_g, carbs_g, fat_g


def _slot_name_penalty(recipe_title: str, meal_type: Literal["breakfast", "lunch", "dinner"]) -> float:
    """
    Lightly nudges obvious breakfast/dinner names into more plausible slots.
    """
    title = recipe_title.lower()

    has_breakfast_hint = any(word in title for word in BREAKFAST_HINTS)
    has_dinner_hint = any(word in title for word in DINNER_HINTS)
    has_sweet_hint = any(word in title for word in SWEET_HINTS)

    if meal_type == "breakfast":
        if has_breakfast_hint:
            return -0.20
        if has_dinner_hint:
            return 0.20

    if meal_type == "dinner" and has_dinner_hint:
        return -0.10

    if meal_type in ("lunch", "dinner") and has_sweet_hint:
        return 1.20

    return 0.0


def _is_sweet_title(title: str) -> bool:
    return any(word in title.lower() for word in SWEET_HINTS)


def _recipe_nutrition_score(
    recipe: RealRecipe,
    meal_type: Literal["breakfast", "lunch", "dinner"],
    target_calories: float,
    target_protein_g: float,
    target_carbs_g: float,
    target_fat_g: float,
    times_used: int,
) -> float:
    """
    Lower score is better: calorie fit + macro fit + repeat penalty + mild title heuristic.
    """
    cal_err = abs(recipe.calories - target_calories) / max(target_calories, 1.0)
    protein_err = abs(recipe.protein_g - target_protein_g) / max(target_protein_g, 1.0)
    carbs_err = abs(recipe.carbs_g - target_carbs_g) / max(target_carbs_g, 1.0)
    fat_err = abs(recipe.fat_g - target_fat_g) / max(target_fat_g, 1.0)

    macro_err = (protein_err + carbs_err + fat_err) / 3.0
    repeat_penalty = times_used * 0.15
    low_protein_penalty = 0.60 if meal_type in ("lunch", "dinner") and recipe.protein_g < 15 else 0.0

    return (
        2.0 * cal_err
        + 1.0 * macro_err
        + repeat_penalty
        + low_protein_penalty
        + _slot_name_penalty(recipe.title, meal_type)
    )


def _pick_optimized_recipe(
    candidates: list[RealRecipe],
    meal_type: Literal["breakfast", "lunch", "dinner"],
    target_calories: float,
    target_protein_g: float,
    target_carbs_g: float,
    target_fat_g: float,
    times_used_by_id: dict[str, int],
    used_today: set[str],
    seed: int,
) -> RealRecipe:
    """
    Deterministic best-pick selection for one meal slot.
    """
    def _best_from(pool: list[RealRecipe]) -> Optional[RealRecipe]:
        best_recipe: Optional[RealRecipe] = None
        best_score = float("inf")
        best_tiebreak = float("inf")

        for recipe in pool:
            if recipe.id in used_today:
                continue

            score = _recipe_nutrition_score(
                recipe=recipe,
                meal_type=meal_type,
                target_calories=target_calories,
                target_protein_g=target_protein_g,
                target_carbs_g=target_carbs_g,
                target_fat_g=target_fat_g,
                times_used=times_used_by_id.get(recipe.id, 0),
            )
            tiebreak = _stable_int_seed(recipe.id, meal_type, str(seed))

            if score < best_score or (score == best_score and tiebreak < best_tiebreak):
                best_recipe = recipe
                best_score = score
                best_tiebreak = tiebreak

        return best_recipe

    if meal_type in ("lunch", "dinner"):
        savory_only = [r for r in candidates if not _is_sweet_title(r.title)]
        best_recipe = _best_from(savory_only) if savory_only else None
        if best_recipe is not None:
            return best_recipe

    best_recipe = _best_from(candidates)
    if best_recipe is None:
        raise HTTPException(status_code=500, detail="No usable recipes found for optimization.")
    return best_recipe


# ------------------------------------------------------------------------------
# 3C) Real nutrition-only optimizer endpoint (v1)
# ------------------------------------------------------------------------------

@app.get("/optimize/meal-plan", response_model=WeeklyPlan)
def optimized_meal_plan(
    budget: float = Query(..., gt=0, description="Weekly budget in USD (currently not optimized yet)."),
    calories: int = Query(..., gt=0, description="Target calories per day (must be > 0)."),
    diet: Diet = Query("none", description="Diet preference (reserved for next optimizer iteration)."),
    start_date: Optional[str] = Query(
        None,
        description="Optional start date in YYYY-MM-DD. If omitted, today is used.",
    ),
    protein_target_g: Optional[float] = Query(
        None,
        gt=0,
        description="Optional daily protein target in grams. Must be provided with carbs/fat targets.",
    ),
    carbs_target_g: Optional[float] = Query(
        None,
        gt=0,
        description="Optional daily carbs target in grams. Must be provided with protein/fat targets.",
    ),
    fat_target_g: Optional[float] = Query(
        None,
        gt=0,
        description="Optional daily fat target in grams. Must be provided with protein/carbs targets.",
    ),
) -> WeeklyPlan:
    """
    Build a weekly plan using real recipe nutrition data and a simple deterministic scorer.

    v1 scope:
    - optimizes for calories + macros only
    - ignores prices and grocery availability (added in later iterations)
    """
    recipes = _load_real_recipes()
    if not recipes:
        raise HTTPException(
            status_code=500,
            detail=f"No recipes loaded from {RECIPES_NUTRITION_PATH}",
        )

    explicit_macros = [protein_target_g, carbs_target_g, fat_target_g]
    provided_macro_count = sum(1 for value in explicit_macros if value is not None)
    if provided_macro_count not in (0, 3):
        raise HTTPException(
            status_code=400,
            detail="If overriding macros, provide protein_target_g, carbs_target_g, and fat_target_g together.",
        )

    if provided_macro_count == 3:
        daily_protein_target = float(protein_target_g)
        daily_carbs_target = float(carbs_target_g)
        daily_fat_target = float(fat_target_g)
    else:
        daily_protein_target, daily_carbs_target, daily_fat_target = _default_daily_macro_targets(calories)

    start = parse_start_date(start_date)
    seed = _stable_int_seed(
        str(start),
        str(budget),
        str(calories),
        str(diet),
        str(daily_protein_target),
        str(daily_carbs_target),
        str(daily_fat_target),
    )

    times_used_by_id: dict[str, int] = {}
    days: list[DayPlan] = []

    for i in range(7):
        day_date = start + timedelta(days=i)
        used_today: set[str] = set()
        meals: list[Meal] = []

        for meal_type in ("breakfast", "lunch", "dinner"):
            split = MEAL_SPLITS[meal_type]
            recipe = _pick_optimized_recipe(
                candidates=recipes,
                meal_type=meal_type,
                target_calories=calories * split,
                target_protein_g=daily_protein_target * split,
                target_carbs_g=daily_carbs_target * split,
                target_fat_g=daily_fat_target * split,
                times_used_by_id=times_used_by_id,
                used_today=used_today,
                seed=seed + i,
            )

            used_today.add(recipe.id)
            times_used_by_id[recipe.id] = times_used_by_id.get(recipe.id, 0) + 1

            meals.append(
                Meal(
                    meal_type=meal_type,
                    name=recipe.title,
                    servings=1,
                    nutrition=Nutrition(
                        calories=int(round(recipe.calories)),
                        protein_g=int(round(recipe.protein_g)),
                        carbs_g=int(round(recipe.carbs_g)),
                        fat_g=int(round(recipe.fat_g)),
                    ),
                    estimated_cost_usd=0.0,
                )
            )

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
        calories=sum(d.totals.calories for d in days),
        protein_g=sum(d.totals.protein_g for d in days),
        carbs_g=sum(d.totals.carbs_g for d in days),
        fat_g=sum(d.totals.fat_g for d in days),
    )
    week_total_cost = round(sum(d.total_cost_usd for d in days), 2)

    return WeeklyPlan(
        inputs={
            "budget": budget,
            "calories": calories,
            "diet": diet,
            "start_date": start_date,
            "optimizer": "nutrition_v1",
            "protein_target_g": round(daily_protein_target, 2),
            "carbs_target_g": round(daily_carbs_target, 2),
            "fat_target_g": round(daily_fat_target, 2),
        },
        days=days,
        week_totals=week_totals,
        week_total_cost_usd=week_total_cost,
    )


# ------------------------------------------------------------------------------
# 4) Week 1 demo endpoint
# ------------------------------------------------------------------------------

@app.get("/demo/meal-plan", response_model=WeeklyPlan)
def demo_meal_plan(
    budget: float = Query(..., gt=0, description="Weekly budget in USD (must be > 0)."),
    calories: int = Query(..., gt=0, description="Target calories per day (must be > 0)."),
    diet: Diet = Query("none", description="Diet preference (Week 1 mostly ignores this)."),
    start_date: Optional[str] = Query(
        None,
        description="Optional start date in YYYY-MM-DD. If omitted, today is used.",
    ),
) -> WeeklyPlan:
    """
    Generate a FAKE weekly meal plan for Week 1.

    What this endpoint guarantees:
    - Always returns 7 days
    - Always returns breakfast/lunch/dinner for each day
    - Always returns totals for each day and the full week
    - Stable JSON shape (frontend can build against it)

    How the fake numbers work:
    - We split the daily calorie target into three meals:
        breakfast ~30%, lunch ~35%, dinner = remainder
    - We assign simple macro values that look plausible.
    - We fake costs by allocating the weekly budget evenly per day,
      then splitting that day’s budget across meals.

    Later weeks will replace:
    - fake costs -> grocery pricing logic
    - fake macro allocation -> real nutrition computed from recipes/USDA
    - hardcoded meal names -> real recipe selection
    """
    # Convert the optional string into a real date object.
    start = parse_start_date(start_date)

    # Split calories across 3 meals.
    # These ratios are arbitrary but reasonable for a demo.
    breakfast_cals = int(calories * 0.30)
    lunch_cals = int(calories * 0.35)
    dinner_cals = calories - breakfast_cals - lunch_cals  # ensures total = calories

    # Allocate a daily budget (weekly budget / 7).
    # We clamp to at least 1.0 just to avoid silly-looking $0.00 meals.
    daily_budget = max(budget / 7.0, 1.0)

    # We'll build up the week day-by-day.
    days: List[DayPlan] = []

    for i in range(7):
        day_date = start + timedelta(days=i)

        # Create 3 meals for this day.
        # These are "fake" but structured exactly how real meals will be structured later.
        # Determine a bucket so changing calories tends to change which meals appear
        bucket = _calorie_bucket(calories)

        # Stable seed based on inputs so results are reproducible for the demo
        seed = _stable_int_seed(
            str(start),
            str(budget),
            str(calories),
            str(diet),
        )

        # Pick templates deterministically (varies by day + meal slot)
        breakfast_t = _pick_template(BREAKFAST_CATALOG, seed, i, 0, bucket)
        lunch_t = _pick_template(LUNCH_CATALOG, seed, i, 1, bucket)
        dinner_t = _pick_template(DINNER_CATALOG, seed, i, 2, bucket)

        # Split calories across meals (same approach as before)
        target_breakfast_cals = breakfast_cals
        target_lunch_cals = lunch_cals
        target_dinner_cals = dinner_cals

        # Split daily budget across meals (same idea as before, just simpler)
        breakfast_cost = min(daily_budget * 0.25, 5.00)
        lunch_cost = min(daily_budget * 0.35, 8.00)
        dinner_cost = min(daily_budget * 0.40, 12.00)

        meals = [
            _build_meal_from_template(
                meal_type="breakfast",
                template=breakfast_t,
                target_meal_calories=target_breakfast_cals,
                estimated_cost_usd=breakfast_cost,
            ),
            _build_meal_from_template(
                meal_type="lunch",
                template=lunch_t,
                target_meal_calories=target_lunch_cals,
                estimated_cost_usd=lunch_cost,
            ),
            _build_meal_from_template(
                meal_type="dinner",
                template=dinner_t,
                target_meal_calories=target_dinner_cals,
                estimated_cost_usd=dinner_cost,
            ),
        ]

        # Compute totals for this day (sum across the 3 meals).
        totals, total_cost = compute_day_totals(meals)

        # Append the day's plan to the week.
        days.append(
            DayPlan(
                date=day_date.isoformat(),
                meals=meals,
                totals=totals,
                total_cost_usd=total_cost,
            )
        )

    # Compute week totals by summing each day total.
    week_totals = Nutrition(
        calories=sum(d.totals.calories for d in days),
        protein_g=sum(d.totals.protein_g for d in days),
        carbs_g=sum(d.totals.carbs_g for d in days),
        fat_g=sum(d.totals.fat_g for d in days),
    )
    week_total_cost = round(sum(d.total_cost_usd for d in days), 2)

    # Return a single object that matches the WeeklyPlan schema.
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


# ------------------------------------------------------------------------------
# 5) (Optional) A simple health check endpoint
# ------------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    """
    Simple health check.
    Useful for deployment and for quickly verifying the server is running.
    """
    return {"status": "ok"}
