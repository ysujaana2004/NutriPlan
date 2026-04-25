"""
fetch_recipe_details.py

Step 2 (efficient):
- Reads data/recipes.json (list of {id, title})
- Fetches full recipe details in BULK (one request per chunk)
- Saves to data/recipes-full.json

Why bulk?
- Much fewer HTTP requests (e.g., 60 recipes -> 1 request)
- Less overhead + typically friendlier to rate limits
"""

import json
import os
import time
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("SPOONACULAR_API_KEY")

if not API_KEY:
    raise ValueError("SPOONACULAR_API_KEY not found in environment variables.")

# ----------------------------
# CONFIG
# ----------------------------

INPUT_PATH = "data/recipes.json"
OUTPUT_PATH = "data/recipes-full.json"

# Chunk size: keep it <= 100 to be safe for URL/query length and API limits.
CHUNK_SIZE = 80

# Small sleep between chunks (only matters if you have multiple chunks)
SLEEP_SECONDS = 0.25


def chunk_list(items: List[int], size: int) -> List[List[int]]:
    """Split a list into chunks of length `size`."""
    return [items[i : i + size] for i in range(0, len(items), size)]


def load_recipe_ids(path: str) -> List[int]:
    """Load recipe IDs from the Step 1 file."""
    with open(path, "r") as f:
        data = json.load(f)

    # Step 1 script saved as a list of {id, title}
    return [int(r["id"]) for r in data if "id" in r]


def fetch_bulk(ids: List[int]) -> List[Dict[str, Any]]:
    """
    Fetch full recipe info for a chunk of recipe IDs using Spoonacular bulk endpoint.
    """
    url = "https://api.spoonacular.com/recipes/informationBulk"
    params = {
        "ids": ",".join(map(str, ids)),
        "includeNutrition": "false",
        "apiKey": API_KEY,
    }

    resp = requests.get(url, params=params, timeout=30)

    if resp.status_code != 200:
        raise Exception(f"Bulk request failed: {resp.status_code} {resp.text[:300]}")

    data = resp.json()

    # Bulk endpoint usually returns a list of recipe objects
    if not isinstance(data, list):
        raise Exception(f"Unexpected response shape (expected list). Got: {type(data)}")

    return data


def main():
    ids = load_recipe_ids(INPUT_PATH)

    if not ids:
        raise Exception(f"No recipe IDs found in {INPUT_PATH}")

    all_recipes: List[Dict[str, Any]] = []

    id_chunks = chunk_list(ids, CHUNK_SIZE)

    for idx, chunk in enumerate(id_chunks, start=1):
        print(f"[{idx}/{len(id_chunks)}] Fetching {len(chunk)} recipes in bulk...")
        recipes = fetch_bulk(chunk)
        all_recipes.extend(recipes)

        # Only sleep if more chunks remain
        if idx < len(id_chunks):
            time.sleep(SLEEP_SECONDS)

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_recipes, f, indent=2)

    print(f"\nSaved {len(all_recipes)} full recipes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()