"""
Nutrition-first weekly meal planner with store integration penalties.

Core workflow in this module:
1. Load enriched RealRecipe candidates from data_access.
2. Compute target calories/macros per meal slot.
3. Score candidate recipes using:
   - calorie fit
   - macro fit
   - repeat avoidance
   - simple title heuristics
   - store coverage penalties
   - budget-aware cost penalties
4. Select deterministic best recipes for 7 days x 3 meals.
5. Return a WeeklyPlan response object for API endpoints.

Scope of this optimizer (intentionally simple):
- It is not a full mathematical optimizer/solver.
- It uses transparent heuristic scoring for maintainability.
- It now returns a simple aggregated shopping list based on canonical
  ingredient coverage and cheapest matched store products.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Literal, Optional

from fastapi import HTTPException

from .data_access import (
    RealRecipe,
    load_canonical_name_by_id,
   # load_cheapest_target_by_canonical_id,
    load_real_recipes,
    load_recipe_coverage_by_store,
)
from .pricing_service import get_store_pricing
from .planner_utils import compute_day_totals, default_daily_macro_targets, parse_start_date, stable_int_seed
from .schemas import (
    DayPlan,
    Diet,
    IngredientLine,
    Meal,
    MissingShoppingItem,
    Nutrition,
    ShoppingListItem,
    ShoppingListSummary,
    WeeklyPlan,
)


MEAL_SPLITS: dict[Literal["breakfast", "lunch", "dinner"], float] = {
    "breakfast": 0.30,
    "lunch": 0.35,
    "dinner": 0.35,
}
MAX_WEEKLY_REPEATS_PER_SLOT: dict[Literal["breakfast", "lunch", "dinner"], int] = {
    "breakfast": 2,
    "lunch": 2,
    "dinner": 2,
}
RECENT_SLOT_WINDOW_DAYS = 2
CALORIE_ERROR_WEIGHT = 5.0
CALORIE_UNDERSHOOT_MULTIPLIER = 1.45
MACRO_ERROR_WEIGHT = 0.60
INTEGRATION_PENALTY_WEIGHT = 0.70
GLOBAL_REPEAT_PENALTY_WEIGHT = 0.08
SLOT_REPEAT_PENALTY_WEIGHT = 0.35
SLOT_REPEAT_EXTRA_AFTER_FIRST = 0.30

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

BREAKFAST_DISH_TYPES = {"breakfast", "morning meal", "brunch"}
LUNCH_DISH_TYPES = {"lunch"}
DINNER_DISH_TYPES = {"dinner"}
MAIN_MEAL_DISH_TYPES = {"main course", "main dish"}
NON_BREAKFAST_DISH_TYPES = LUNCH_DISH_TYPES | DINNER_DISH_TYPES | MAIN_MEAL_DISH_TYPES


def has_dish_type(recipe: RealRecipe, tags: set[str]) -> bool:
    """Return True when the recipe has any of the requested normalized dish-type tags."""

    return any(tag in tags for tag in recipe.dish_types)


def meal_slot_metadata_penalty(recipe: RealRecipe, meal_type: Literal["breakfast", "lunch", "dinner"]) -> float:
    """Apply slot-fit adjustment using recipe dish-type metadata when available."""

    has_breakfast = has_dish_type(recipe, BREAKFAST_DISH_TYPES)
    has_lunch = has_dish_type(recipe, LUNCH_DISH_TYPES)
    has_dinner = has_dish_type(recipe, DINNER_DISH_TYPES)
    has_main = has_dish_type(recipe, MAIN_MEAL_DISH_TYPES)

    # If structured dish types are missing, do not force a guess.
    if not (has_breakfast or has_lunch or has_dinner or has_main):
        return 0.0

    if meal_type == "breakfast":
        if has_breakfast:
            return -0.35
        if has_lunch or has_dinner or has_main:
            return 2.0
        return 0.40

    if meal_type == "lunch":
        if has_lunch or has_main:
            return -0.15
        if has_breakfast:
            return 1.0
        return 0.0

    if has_dinner or has_main:
        return -0.15
    if has_breakfast:
        return 1.0
    return 0.0


def preferred_pool_for_slot(
    candidates: list[RealRecipe],
    meal_type: Literal["breakfast", "lunch", "dinner"],
) -> list[RealRecipe]:
    """Prefer meal-slot-compatible recipes, but keep graceful fallback pools."""

    if meal_type == "breakfast":
        tagged_breakfast = [recipe for recipe in candidates if has_dish_type(recipe, BREAKFAST_DISH_TYPES)]
        if tagged_breakfast:
            return tagged_breakfast

        # If no explicit breakfast options are tagged, at least avoid explicit lunch/dinner mains.
        no_explicit_non_breakfast = [recipe for recipe in candidates if not has_dish_type(recipe, NON_BREAKFAST_DISH_TYPES)]
        return no_explicit_non_breakfast if no_explicit_non_breakfast else candidates

    if meal_type == "lunch":
        tagged_lunch = [
            recipe
            for recipe in candidates
            if has_dish_type(recipe, LUNCH_DISH_TYPES) or has_dish_type(recipe, MAIN_MEAL_DISH_TYPES)
        ]
        return tagged_lunch if tagged_lunch else candidates

    tagged_dinner = [
        recipe
        for recipe in candidates
        if has_dish_type(recipe, DINNER_DISH_TYPES) or has_dish_type(recipe, MAIN_MEAL_DISH_TYPES)
    ]
    return tagged_dinner if tagged_dinner else candidates


def slot_name_penalty(recipe_title: str, meal_type: Literal["breakfast", "lunch", "dinner"]) -> float:
    """Add a small penalty when recipe title appears mismatched for a meal slot."""

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


def is_sweet_title(title: str) -> bool:
    """Return True when a title looks dessert/sweet-oriented."""

    return any(word in title.lower() for word in SWEET_HINTS)


def coverage_and_cost_penalty(recipe: RealRecipe, target_meal_budget_usd: float) -> float:
    """Compute penalty from missing coverage and per-meal budget mismatch."""

    coverage_penalty = (1.0 - recipe.coverage_ratio) * 1.4
    missing_penalty = recipe.missing_canonical_count * 0.20

    if target_meal_budget_usd <= 0:
        budget_penalty = 0.0
    else:
        cost_ratio = recipe.estimated_cost_usd / target_meal_budget_usd
        base_cost_penalty = 0.05 * cost_ratio
        over_budget_penalty = 0.0
        if cost_ratio > 1.0:
            over_budget_penalty = min(cost_ratio - 1.0, 3.0) * 0.90
        budget_penalty = base_cost_penalty + over_budget_penalty

    return coverage_penalty + missing_penalty + budget_penalty


def variety_candidate_pools(
    pool: list[RealRecipe],
    meal_type: Literal["breakfast", "lunch", "dinner"],
    times_used_by_slot_and_id: dict[tuple[Literal["breakfast", "lunch", "dinner"], str], int],
    recent_recipe_ids_for_slot: list[str],
) -> list[list[RealRecipe]]:
    """Build fallback pools that prioritize variety but never block final selection."""

    max_repeats = MAX_WEEKLY_REPEATS_PER_SLOT[meal_type]
    recent_ids = set(recent_recipe_ids_for_slot[-RECENT_SLOT_WINDOW_DAYS:])

    under_cap = [
        recipe for recipe in pool if times_used_by_slot_and_id.get((meal_type, recipe.id), 0) < max_repeats
    ]
    not_recent = [recipe for recipe in pool if recipe.id not in recent_ids]
    under_cap_and_not_recent = [recipe for recipe in under_cap if recipe.id not in recent_ids]

    candidate_pools = [under_cap_and_not_recent, under_cap, not_recent, pool]
    return [candidate_pool for candidate_pool in candidate_pools if candidate_pool]


def recipe_nutrition_score(
    recipe: RealRecipe,
    meal_type: Literal["breakfast", "lunch", "dinner"],
    target_calories: float,
    target_protein_g: float,
    target_carbs_g: float,
    target_fat_g: float,
    target_meal_budget_usd: float,
    times_used_total: int,
    times_used_for_slot: int,
) -> float:
    """Score one recipe for one meal slot; lower score is better."""

    cal_delta = recipe.calories - target_calories
    cal_err = abs(cal_delta) / max(target_calories, 1.0)
    if cal_delta < 0:
        cal_err *= CALORIE_UNDERSHOOT_MULTIPLIER
    protein_err = abs(recipe.protein_g - target_protein_g) / max(target_protein_g, 1.0)
    carbs_err = abs(recipe.carbs_g - target_carbs_g) / max(target_carbs_g, 1.0)
    fat_err = abs(recipe.fat_g - target_fat_g) / max(target_fat_g, 1.0)

    macro_err = (protein_err + carbs_err + fat_err) / 3.0
    global_repeat_penalty = times_used_total * GLOBAL_REPEAT_PENALTY_WEIGHT
    slot_repeat_penalty = (times_used_for_slot * SLOT_REPEAT_PENALTY_WEIGHT) + (
        max(times_used_for_slot - 1, 0) * SLOT_REPEAT_EXTRA_AFTER_FIRST
    )
    low_protein_penalty = 0.60 if meal_type in ("lunch", "dinner") and recipe.protein_g < 15 else 0.0
    integration_penalty = coverage_and_cost_penalty(recipe, target_meal_budget_usd)

    return (
        CALORIE_ERROR_WEIGHT * cal_err
        + MACRO_ERROR_WEIGHT * macro_err
        + global_repeat_penalty
        + slot_repeat_penalty
        + low_protein_penalty
        + (INTEGRATION_PENALTY_WEIGHT * integration_penalty)
        + meal_slot_metadata_penalty(recipe, meal_type)
        + slot_name_penalty(recipe.title, meal_type)
    )


def pick_optimized_recipe(
    candidates: list[RealRecipe],
    meal_type: Literal["breakfast", "lunch", "dinner"],
    target_calories: float,
    target_protein_g: float,
    target_carbs_g: float,
    target_fat_g: float,
    target_meal_budget_usd: float,
    times_used_by_id: dict[str, int],
    times_used_by_slot_and_id: dict[tuple[Literal["breakfast", "lunch", "dinner"], str], int],
    recent_recipe_ids_for_slot: list[str],
    used_today: set[str],
    seed: int,
) -> RealRecipe:
    """Pick one best recipe for a meal slot with deterministic tie-breaking."""

    def best_from(pool: list[RealRecipe]) -> Optional[RealRecipe]:
        """Return lowest-scoring recipe from pool not already used today."""

        best_recipe: Optional[RealRecipe] = None
        best_score = float("inf")
        best_tiebreak = float("inf")
        for recipe in pool:
            if recipe.id in used_today:
                continue

            score = recipe_nutrition_score(
                recipe=recipe,
                meal_type=meal_type,
                target_calories=target_calories,
                target_protein_g=target_protein_g,
                target_carbs_g=target_carbs_g,
                target_fat_g=target_fat_g,
                target_meal_budget_usd=target_meal_budget_usd,
                times_used_total=times_used_by_id.get(recipe.id, 0),
                times_used_for_slot=times_used_by_slot_and_id.get((meal_type, recipe.id), 0),
            )
            tiebreak = stable_int_seed(recipe.id, meal_type, str(seed))

            if score < best_score or (score == best_score and tiebreak < best_tiebreak):
                best_recipe = recipe
                best_score = score
                best_tiebreak = tiebreak

        return best_recipe

    fully_covered = [recipe for recipe in candidates if recipe.missing_canonical_count == 0 and recipe.coverage_ratio > 0]
    candidate_pool = fully_covered if fully_covered else candidates
    candidate_pool = preferred_pool_for_slot(candidate_pool, meal_type)

    def best_with_variety(pool: list[RealRecipe]) -> Optional[RealRecipe]:
        """Try increasingly relaxed pools to improve variety without causing hard failure."""

        for candidate_subpool in variety_candidate_pools(
            pool=pool,
            meal_type=meal_type,
            times_used_by_slot_and_id=times_used_by_slot_and_id,
            recent_recipe_ids_for_slot=recent_recipe_ids_for_slot,
        ):
            best_recipe = best_from(candidate_subpool)
            if best_recipe is not None:
                return best_recipe
        return None

    if meal_type in ("lunch", "dinner"):
        savory_only = [recipe for recipe in candidate_pool if not is_sweet_title(recipe.title)]
        best_recipe = best_with_variety(savory_only) if savory_only else None
        if best_recipe is not None:
            return best_recipe

    best_recipe = best_with_variety(candidate_pool)
    if best_recipe is None:
        raise HTTPException(status_code=500, detail="No usable recipes found for optimization.")
    return best_recipe


def canonical_display_name(canonical_id: str, canonical_name_by_id: dict[str, str]) -> str:
    """Return human-friendly canonical name with sensible fallback."""

    return canonical_name_by_id.get(canonical_id, canonical_id.replace("_", " "))


def build_shopping_list_summary(
    selected_recipe_ids: list[str],
    recipe_name_by_id: dict[str, str],
    store_name: str,
) -> ShoppingListSummary:
    """Aggregate shopping list items from selected recipe IDs."""

    coverage_by_id = load_recipe_coverage_by_store(store_name)
    cheapest_lookup = get_store_pricing(store_name)
    #cheapest_lookup = load_cheapest_target_by_canonical_id()
    canonical_name_by_id = load_canonical_name_by_id()

    covered_units: dict[str, int] = {}
    covered_recipe_names: dict[str, set[str]] = {}
    missing_recipe_names: dict[str, set[str]] = {}

    for recipe_id in selected_recipe_ids:
        coverage = coverage_by_id.get(recipe_id)
        if coverage is None:
            continue

        recipe_name = recipe_name_by_id.get(recipe_id, recipe_id)

        for canonical_id in coverage.covered_canonical:
            covered_units[canonical_id] = covered_units.get(canonical_id, 0) + 1
            covered_recipe_names.setdefault(canonical_id, set()).add(recipe_name)

        for canonical_id in coverage.missing_canonical:
            missing_recipe_names.setdefault(canonical_id, set()).add(recipe_name)

    items: list[ShoppingListItem] = []
    for canonical_id in sorted(covered_units):
        choice = cheapest_lookup.get(canonical_id)
        if choice is None:
            # If lookup disappeared after coverage generation, treat as missing.
            missing_recipe_names.setdefault(canonical_id, set()).update(covered_recipe_names.get(canonical_id, set()))
            continue

        estimated_units = covered_units[canonical_id]
        unit_price = round(choice.price_usd, 2)
        total_cost = round(unit_price * estimated_units, 2)
        items.append(
            ShoppingListItem(
                canonical_id=canonical_id,
                canonical_name=canonical_display_name(canonical_id, canonical_name_by_id),
                product_name=choice.product_name,
                category=choice.category,
                unit_price_usd=unit_price,
                estimated_units=estimated_units,
                estimated_total_cost_usd=total_cost,
                recipes=sorted(covered_recipe_names.get(canonical_id, set())),
            )
        )

    missing_items: list[MissingShoppingItem] = []
    for canonical_id in sorted(missing_recipe_names):
        missing_items.append(
            MissingShoppingItem(
                canonical_id=canonical_id,
                canonical_name=canonical_display_name(canonical_id, canonical_name_by_id),
                recipes=sorted(missing_recipe_names[canonical_id]),
            )
        )

    total_estimated_cost = round(sum(item.estimated_total_cost_usd for item in items), 2)
    return ShoppingListSummary(
        items=items,
        missing_items=missing_items,
        total_estimated_cost_usd=total_estimated_cost,
    )


def build_optimized_weekly_plan(
    store_name: str,  #Addec store name param
    budget: float,
    calories: int,
    diet: Diet,
    start_date: Optional[str],
    protein_target_g: Optional[float],
    carbs_target_g: Optional[float],
    fat_target_g: Optional[float],
) -> WeeklyPlan:
    """Build a weekly plan using nutrition targets and store-aware penalties."""

    recipes = load_real_recipes(store_name)
    if not recipes:
        raise HTTPException(status_code=500, detail="No real recipes available for optimization.")

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
        daily_protein_target, daily_carbs_target, daily_fat_target = default_daily_macro_targets(calories)

    start = parse_start_date(start_date)
    seed = stable_int_seed(
        str(start),
        str(budget),
        str(calories),
        str(diet),
        str(daily_protein_target),
        str(daily_carbs_target),
        str(daily_fat_target),
    )

    times_used_by_id: dict[str, int] = {}
    times_used_by_slot_and_id: dict[tuple[Literal["breakfast", "lunch", "dinner"], str], int] = {}
    recent_recipe_ids_by_slot: dict[Literal["breakfast", "lunch", "dinner"], list[str]] = {
        "breakfast": [],
        "lunch": [],
        "dinner": [],
    }
    days: list[DayPlan] = []
    selected_recipe_ids: list[str] = []
    recipe_name_by_id: dict[str, str] = {}
    for day_index in range(7):
        day_date = start + timedelta(days=day_index)
        used_today: set[str] = set()
        meals: list[Meal] = []

        for meal_type in ("breakfast", "lunch", "dinner"):
            split = MEAL_SPLITS[meal_type]
            target_meal_budget_usd = (budget / 7.0) * split
            recipe = pick_optimized_recipe(
                candidates=recipes,
                meal_type=meal_type,
                target_calories=calories * split,
                target_protein_g=daily_protein_target * split,
                target_carbs_g=daily_carbs_target * split,
                target_fat_g=daily_fat_target * split,
                target_meal_budget_usd=target_meal_budget_usd,
                times_used_by_id=times_used_by_id,
                times_used_by_slot_and_id=times_used_by_slot_and_id,
                recent_recipe_ids_for_slot=recent_recipe_ids_by_slot[meal_type],
                used_today=used_today,
                seed=seed + day_index,
            )

            used_today.add(recipe.id)
            times_used_by_id[recipe.id] = times_used_by_id.get(recipe.id, 0) + 1
            slot_key = (meal_type, recipe.id)
            times_used_by_slot_and_id[slot_key] = times_used_by_slot_and_id.get(slot_key, 0) + 1
            recent_recipe_ids_by_slot[meal_type].append(recipe.id)
            recent_recipe_ids_by_slot[meal_type] = recent_recipe_ids_by_slot[meal_type][-RECENT_SLOT_WINDOW_DAYS:]
            selected_recipe_ids.append(recipe.id)
            recipe_name_by_id[recipe.id] = recipe.title

            meals.append(
                Meal(
                    recipe_id=recipe.id,
                    meal_type=meal_type,
                    name=recipe.title,
                    servings=1,
                    nutrition=Nutrition(
                        calories=int(round(recipe.calories)),
                        protein_g=int(round(recipe.protein_g)),
                        carbs_g=int(round(recipe.carbs_g)),
                        fat_g=int(round(recipe.fat_g)),
                    ),
                    estimated_cost_usd=round(recipe.estimated_cost_usd, 2),
                    image_url=recipe.image_url or None,
                    ingredients=[
                        IngredientLine(
                            id=f"{recipe.id}-ing-{idx}",
                            name=name,
                            amount=amount,
                        )
                        for idx, (name, amount) in enumerate(recipe.ingredient_lines, start=1)
                    ],
                    instructions=list(recipe.instruction_steps),
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
        calories=sum(day.totals.calories for day in days),
        protein_g=sum(day.totals.protein_g for day in days),
        carbs_g=sum(day.totals.carbs_g for day in days),
        fat_g=sum(day.totals.fat_g for day in days),
    )
    week_total_cost = round(sum(day.total_cost_usd for day in days), 2)
    shopping_list = build_shopping_list_summary(selected_recipe_ids, recipe_name_by_id, store_name)
   #shopping_list = build_shopping_list_summary(selected_recipe_ids, recipe_name_by_id)
    return WeeklyPlan(
        inputs={
            "budget": budget,
            "calories": calories,
            "diet": diet,
            "start_date": start_date,
            "optimizer": "nutrition_v1",
            "target_lookup_size": len(get_store_pricing(store_name)),
            "recipe_coverage_rows": len(load_recipe_coverage_by_store(store_name)),
            "protein_target_g": round(daily_protein_target, 2),
            # "target_lookup_size": len(load_cheapest_target_by_canonical_id()),
            "carbs_target_g": round(daily_carbs_target, 2),
            "fat_target_g": round(daily_fat_target, 2),

        },
        days=days,
        week_totals=week_totals,
        week_total_cost_usd=week_total_cost,
        shopping_list=shopping_list,
    )
