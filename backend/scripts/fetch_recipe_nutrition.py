"""
fetch_recipe_nutrition_bulk.py

Goal:
- Reads data/recipes.json (list of {id, title})
- Fetches nutrition in BULK (informationBulk with includeNutrition=true)
- Extracts ONLY macros (calories, protein, carbs, fat)
- Saves to data/recipes-nutrition.json

Why bulk?
- 60 recipes -> usually 1 request
- Much simpler + friendlier to rate limits
"""

import json
import os
import time
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPOONACULAR_API_KEY")
if not API_KEY:
    raise ValueError("SPOONACULAR_API_KEY not found in environment variables.")

# ----------------------------
# CONFIG
# ----------------------------
INPUT_PATH = "data/recipes.json"
OUTPUT_PATH = "data/recipes-nutrition.json"

CHUNK_SIZE = 80
SLEEP_SECONDS = 0.25


def chunk_list(items: List[int], size: int) -> List[List[int]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def load_recipe_ids(path: str) -> List[int]:
    with open(path, "r") as f:
        data = json.load(f)
    return [int(r["id"]) for r in data if "id" in r]


def extract_macros(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Spoonacular returns nutrition as:
      recipe["nutrition"]["nutrients"] = [ {name, amount, unit}, ... ]
    We extract calories/protein/carbs/fat by nutrient name.
    """
    nutrients = (recipe.get("nutrition") or {}).get("nutrients") or []

    wanted = {"Calories", "Protein", "Carbohydrates", "Fat"}
    found = {}

    for n in nutrients:
        name = n.get("name")
        if name in wanted:
            found[name] = float(n.get("amount", 0))

    return {
        "calories": found.get("Calories", 0.0),
        "protein": found.get("Protein", 0.0),
        "carbs": found.get("Carbohydrates", 0.0),
        "fat": found.get("Fat", 0.0),
    }


def fetch_bulk(ids: List[int]) -> List[Dict[str, Any]]:
    url = "https://api.spoonacular.com/recipes/informationBulk"
    params = {
        "ids": ",".join(map(str, ids)),
        "includeNutrition": "true",
        "apiKey": API_KEY,
    }

    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Bulk request failed: {resp.status_code} {resp.text[:300]}")

    data = resp.json()
    if not isinstance(data, list):
        raise Exception(f"Unexpected response shape (expected list). Got: {type(data)}")

    return data


def main():
    ids = load_recipe_ids(INPUT_PATH)
    if not ids:
        raise Exception(f"No recipe IDs found in {INPUT_PATH}")

    all_rows: List[Dict[str, Any]] = []

    for idx, chunk in enumerate(chunk_list(ids, CHUNK_SIZE), start=1):
        print(f"[{idx}] Fetching nutrition for {len(chunk)} recipes...")
        recipes = fetch_bulk(chunk)

        for r in recipes:
            rid = r.get("id")
            title = r.get("title")
            macros = extract_macros(r)

            all_rows.append(
                {
                    "id": rid,
                    "title": title,
                    "nutrition": macros,
                }
            )

        if idx < len(chunk_list(ids, CHUNK_SIZE)):
            time.sleep(SLEEP_SECONDS)

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_rows, f, indent=2)

    print(f"\nSaved nutrition for {len(all_rows)} recipes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()