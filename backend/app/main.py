"""
FastAPI entrypoint for the backend service.

What this file is responsible for:
- Creating/configuring the FastAPI app object.
- Defining public HTTP endpoints exposed to the frontend.
- Validating endpoint query parameters.
- Delegating all planner logic to specialized modules.

What this file intentionally does NOT do:
- It does not implement optimization logic directly.
- It does not load raw recipe/Target data files.
- It does not perform matching/scoring calculations.

Endpoint overview:
- /optimize/meal-plan: real nutrition-first planner (uses optimizer module).
- /optimize/meal-plan/replace: replace one generated meal and recompute totals.
- /health: simple readiness check.

Design goal:
- Keep API wiring thin so business logic stays testable and maintainable
  in focused modules (optimizer, data_access, demo_planner, etc.).
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# from ..archive.demo_planner import build_demo_weekly_plan
from .optimizer import build_optimized_weekly_plan, replace_meal_in_weekly_plan
from .schemas import Diet, ReplaceMealRequest, WeeklyPlan
from .store_registry import (
    display_name_for_store_key,
    location_query_name_for_store_key,
    normalize_store_key,
)


app = FastAPI(
    title="Meal Planner Demo API",
    description="Meal planning API with demo and nutrition-first optimized endpoints.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/optimize/meal-plan", response_model=WeeklyPlan)
async def optimized_meal_plan(
    budget: float = Query(..., gt=0, description="Weekly budget in USD."),
    calories: int = Query(..., gt=0, description="Target calories per day."),
    diet: Diet = Query("none", description="Diet preference."),
    start_date: Optional[str] = Query(None, description="Optional YYYY-MM-DD start date."),
    zip_code: Optional[str] = Query(None, description="Optional ZIP code to find local stores."),
    store_preference: str = Query("Target", description="Preferred store (Target, Walmart, BJs, Whole Foods)."),
    protein_target_g: Optional[float] = Query(
        None,
        gt=0,
        description="Optional daily protein grams (must be provided with carbs/fat targets).",
    ),
    carbs_target_g: Optional[float] = Query(
        None,
        gt=0,
        description="Optional daily carbs grams (must be provided with protein/fat targets).",
    ),
    fat_target_g: Optional[float] = Query(
        None,
        gt=0,
        description="Optional daily fat grams (must be provided with protein/carbs targets).",
    ),
) -> WeeklyPlan:
    """Return nutrition-first weekly plan enriched with store coverage/cost metadata."""

    store_key = normalize_store_key(store_preference)
    store_name = display_name_for_store_key(store_key)
    if zip_code:
        from .location_service import find_nearby_stores
        await find_nearby_stores(zip_code, location_query_name_for_store_key(store_key))

    return build_optimized_weekly_plan(
        store_name=store_name,
        budget=budget,
        calories=calories,
        diet=diet,
        start_date=start_date,
        protein_target_g=protein_target_g,
        carbs_target_g=carbs_target_g,
        fat_target_g=fat_target_g,
    )


@app.post("/optimize/meal-plan/replace", response_model=WeeklyPlan)
async def replace_meal(request: ReplaceMealRequest) -> WeeklyPlan:
    """Replace one meal in an existing weekly plan and recompute aggregate outputs."""

    return replace_meal_in_weekly_plan(
        current_plan=request.current_plan,
        day_index=request.day_index,
        meal_type=request.meal_type,
        current_recipe_id=request.current_recipe_id,
    )


@app.get("/stores/nearby")
async def nearby_stores(
    zip_code: str = Query(..., description="ZIP Code to search near"),
    store_name: str = Query("Target", description="Store name, e.g., Target, Walmart, BJs, Whole Foods.")
) -> dict:
    """Find nearby stores using the Google Places API."""
    from .location_service import find_nearby_stores
    store_key = normalize_store_key(store_name)
    normalized_display_name = display_name_for_store_key(store_key)
    stores = await find_nearby_stores(zip_code, location_query_name_for_store_key(store_key))
    return {"store_name": normalized_display_name, "zip_code": zip_code, "results": stores}


@app.get("/health")
def health() -> dict:
    """Simple health check endpoint."""

    return {"status": "ok"}
