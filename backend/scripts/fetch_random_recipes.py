"""
fetch_recipe_ids.py

Fetch ~60 random recipe IDs from Spoonacular and save them to:
data/recipes-random.json

This is Step 1 of a 3-step process to efficiently get detailed recipe info:
1. Fetch random recipe IDs (this script)
2. Fetch full details in bulk (fetch_recipe_details.py)
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("SPOONACULAR_API_KEY")

if not API_KEY:
    raise ValueError("SPOONACULAR_API_KEY not found in environment variables.")

import requests
import json
import os

# Config
NUM_RECIPES = 60
URL = "https://api.spoonacular.com/recipes/complexSearch"

params = {
    "number": NUM_RECIPES,
    "sort": "random",
    "addRecipeInformation": "false",
    "addRecipeNutrition": "false",
    "apiKey": API_KEY
}

response = requests.get(URL, params=params)

if response.status_code != 200:
    raise Exception(f"API request failed: {response.status_code} {response.text}")

data = response.json()

recipes = [
    {"id": r["id"], "title": r["title"]}
    for r in data.get("results", [])
]

os.makedirs("data", exist_ok=True)

with open("data/recipes-random.json", "w") as f:
    json.dump(recipes, f, indent=2)

print(f"Saved {len(recipes)} recipes to data/recipes-random.json")