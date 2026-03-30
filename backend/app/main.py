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
from .optimizer import build_optimized_weekly_plan
from .schemas import Diet, WeeklyPlan


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
#def optimized_meal_plan(
async def optimized_meal_plan(
    budget: float = Query(..., gt=0, description="Weekly budget in USD."),
    calories: int = Query(..., gt=0, description="Target calories per day."),
    diet: Diet = Query("none", description="Diet preference."),
    start_date: Optional[str] = Query(None, description="Optional YYYY-MM-DD start date."),
    zip_code: Optional[str] = Query(None, description="Optional ZIP code to find local stores."),
    store_preference: str = Query("Target", description="Preferred store (Target or Walmart)"),
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
    """Return nutrition-first weekly plan enriched with Target coverage/cost metadata."""

    store_name = store_preference
    if zip_code:
        from .location_service import find_nearby_stores
        # If the preferred store isn't nearby, blindly fallback to the other
        stores = await find_nearby_stores(zip_code, store_preference)
        if not stores:
            store_name = "Walmart" if store_preference.lower() == "target" else "Target"

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

# added this for location (March 20th )
@app.get("/stores/nearby")
async def nearby_stores(
    zip_code: str = Query(..., description="ZIP Code to search near"),
    store_name: str = Query("Target", description="Store name, e.g., 'Target' or 'Walmart'")
) -> dict:
    """Find nearby Target or Walmart stores using the Google Places API."""
    from .location_service import find_nearby_stores
    stores = await find_nearby_stores(zip_code, store_name)
    return {"store_name": store_name, "zip_code": zip_code, "results": stores}


@app.get("/health")
def health() -> dict:
    """Simple health check endpoint."""

    return {"status": "ok"}
