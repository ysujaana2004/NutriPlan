"""
bootstrap_spoonacular_recipes.py

Goal
----
Download ~50 recipes from Spoonacular and convert them into a clean
recipes.json file your backend can load.

Output structure
----------------
data/recipes.json

Each recipe contains:
- id
- name
- meal_type
- macros
- ingredients (with grams when possible)
- instructions
"""

import json
import requests
from pathlib import Path

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("SPOONACULAR_API_KEY")

if not API_KEY:
    raise ValueError("SPOONACULAR_API_KEY not found in environment variables.")

# -----------------------------
# CONFIG
# -----------------------------
NUM_RECIPES = 30

OUTPUT_FILE = Path("data/recipes.json")

# Map ingredient keywords -> your Target folders
CATEGORY_MAP = {
    "beef": "beef",
    "chicken": "chicken",
    "turkey": "turkey",
    "pork": "pork",
    "salmon": "fish and seafood",
    "fish": "fish and seafood",
    "shrimp": "fish and seafood",
    "milk": "milk",
    "cheese": "cheese",
    "yogurt": "yogurt",
    "egg": "eggs",
    "rice": "pasta_rice_grains",
    "pasta": "pasta_rice_grains",
    "spaghetti": "pasta_rice_grains",
    "broccoli": "vegetables",
    "carrot": "vegetables",
    "pepper": "vegetables",
    "tomato": "vegetables",
    "potato": "vegetables",
    "onion": "vegetables",
    "garlic": "vegetables",
    "apple": "fruit",
    "banana": "fruit",
    "strawberry": "fruit"
}


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def categorize_ingredient(name: str):
    """Return category based on keyword matching."""
    name_lower = name.lower()

    for key in CATEGORY_MAP:
        if key in name_lower:
            return CATEGORY_MAP[key]

    return "other"


def extract_macros(nutrition):
    """Extract calories/protein/carbs/fat from Spoonacular nutrition block."""

    macros = {
        "calories": None,
        "protein_g": None,
        "carbs_g": None,
        "fat_g": None
    }

    for nutrient in nutrition["nutrients"]:
        name = nutrient["name"].lower()

        if name == "calories":
            macros["calories"] = nutrient["amount"]

        if name == "protein":
            macros["protein_g"] = nutrient["amount"]

        if name == "carbohydrates":
            macros["carbs_g"] = nutrient["amount"]

        if name == "fat":
            macros["fat_g"] = nutrient["amount"]

    return macros

# Define good/ok/bad units for filtering recipes 
GOOD_UNITS = {
    "g", "gram", "grams", "kg", "mg",
    "ml", "milliliter", "milliliters", "l", "liter", "liters",
    "oz", "ounce", "ounces", "lb", "pound", "pounds",
    "tsp", "teaspoon", "teaspoons", "tbsp", "tablespoon", "tablespoons",
    "cup", "cups",
    "clove", "cloves", "slice", "slices", "piece", "pieces"
}

BAD_HINTS = {"to taste", "as needed"}

def recipe_has_convertible_units(recipe: dict, min_ratio: float = 0.6) -> bool:
    """Check if a recipe has a sufficient ratio of convertible ingredient units."""
    ings = recipe.get("extendedIngredients", [])
    if not ings:
        return False

    total = 0
    convertible = 0

    for ing in ings:
        total += 1

        raw_unit = (ing.get("unit") or "").strip().lower()

        measures = ing.get("measures") or {}
        metric_unit = ((measures.get("metric") or {}).get("unitShort") or "").strip().lower()
        us_unit = ((measures.get("us") or {}).get("unitShort") or "").strip().lower()

        # If unit text is basically "to taste", treat as not convertible (but don't hard reject)
        if raw_unit in BAD_HINTS:
            continue

        # If ANY of these units look convertible, count it
        if (raw_unit in GOOD_UNITS) or (metric_unit in GOOD_UNITS) or (us_unit in GOOD_UNITS):
            convertible += 1

    # Optional sanity bounds (make them wide)
    if total < 4 or total > 22:
        return False

    return (convertible / total) >= min_ratio


# -----------------------------
# MAIN LOGIC
# -----------------------------

def fetch_recipes():
    print("Downloading recipes from Spoonacular...")

    url = "https://api.spoonacular.com/recipes/random"

    params = {
        "apiKey": API_KEY,
        "number": NUM_RECIPES,
        # Spoonacular uses addRecipeNutrition on this endpoint (your earlier version worked);
        # keep includeNutrition if that's what your API account expects, but be consistent.
        "includeNutrition": True,
        "tags": "main course",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    recipes = []

    for recipe in data.get("recipes", []):

        if not recipe_has_convertible_units(recipe):
            continue

        # Macros
        macros = None
        if recipe.get("nutrition") and recipe["nutrition"].get("nutrients"):
            macros = extract_macros(recipe["nutrition"])

        # Ingredients (reset per recipe!)
        ingredients = []
        for ing in recipe.get("extendedIngredients", []):
            name = (ing.get("name") or "").strip()

            measures = ing.get("measures") or {}
            metric = measures.get("metric") or {}

            amount = ing.get("amount")
            unit = ing.get("unit")

            metric_amount = metric.get("amount")
            metric_unit = metric.get("unitShort")

            grams = None
            if metric_unit in ("g", "gram", "grams"):
                grams = float(metric_amount) if metric_amount is not None else None

            ingredients.append(
                {
                    "ingredient_id": name.lower().replace(" ", "_"),
                    "name": name,
                    "amount": amount,
                    "unit": unit,
                    "metric_amount": metric_amount,
                    "metric_unit": metric_unit,
                    "grams": grams,
                    "category": categorize_ingredient(name),
                }
            )

        instructions = recipe.get("instructions", "")

        recipes.append(
            {
                "id": f"spoon_{recipe['id']}",
                "name": recipe["title"],
                "meal_type": "dinner",
                "servings": recipe.get("servings", 1),
                "macros": macros,
                "ingredients": ingredients,
                "instructions": instructions,
                "tags": [],
            }
        )

    return recipes


def main():

    recipes = fetch_recipes()

    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(recipes, f, indent=2)

    print(f"\nSaved {len(recipes)} recipes to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()