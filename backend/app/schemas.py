"""
Shared request/response schema definitions for the meal-planning API.

Why this file exists:
- It centralizes the data contracts returned by backend endpoints.
- It keeps API model definitions separate from planner logic.
- It provides one place to evolve shape/typing for frontend compatibility.

Models defined here:
- Diet: allowed diet query values accepted by endpoints.
- Nutrition: calorie and macro totals.
- Meal: one meal entry in a day plan, including recipe_id and cost.
- DayPlan: one day worth of meals and day totals.
- WeeklyPlan: top-level API response consumed by the frontend.

Usage:
- Imported by endpoint wiring (main.py), demo planner, and optimizer.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Diet = Literal["none", "vegetarian", "high_protein", "low_carb"]


class Nutrition(BaseModel):
    """Nutrition totals used at meal, day, and week levels."""

    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int


class IngredientLine(BaseModel):
    """Single ingredient line shown in recipe details."""

    id: str
    name: str
    amount: str


class Meal(BaseModel):
    """Single meal in a generated day plan."""

    recipe_id: str
    meal_type: Literal["breakfast", "lunch", "dinner"]
    name: str
    servings: int
    nutrition: Nutrition
    estimated_cost_usd: float
    image_url: Optional[str] = None
    ingredients: List[IngredientLine] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)


class DayPlan(BaseModel):
    """One day of a weekly meal plan."""

    date: str
    meals: List[Meal]
    totals: Nutrition
    total_cost_usd: float


class ShoppingListItem(BaseModel):
    """Aggregated purchasable ingredient item derived from selected recipes."""

    canonical_id: str
    canonical_name: str
    product_name: str
    category: str
    unit_price_usd: float
    estimated_units: int
    estimated_total_cost_usd: float
    recipes: List[str]


class MissingShoppingItem(BaseModel):
    """Ingredient that appears in selected recipes but has no matched Target product."""

    canonical_id: str
    canonical_name: str
    recipes: List[str]


class ShoppingListSummary(BaseModel):
    """Top-level shopping list payload returned with optimized weekly plans."""

    items: List[ShoppingListItem]
    missing_items: List[MissingShoppingItem]
    total_estimated_cost_usd: float


class WeeklyPlan(BaseModel):
    """Full weekly response returned to the frontend."""

    inputs: dict
    days: List[DayPlan]
    week_totals: Nutrition
    week_total_cost_usd: float
    shopping_list: Optional[ShoppingListSummary] = None
