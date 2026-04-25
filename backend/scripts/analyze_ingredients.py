"""
analyze_ingredients.py

Reads recipes from data/recipes/recipes.json
Counts unique ingredients and saves them to data/recipes/ingredients-from-recipes.json
"""

import json
import re
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
RECIPES_DIR = BACKEND_DIR / "data" / "recipes"

INPUT_PATH = RECIPES_DIR / "recipes.json"
OUTPUT_PATH = RECIPES_DIR / "ingredients-from-recipes.json"


def normalize(name: str) -> str:
    """
    Basic normalization to prevent ingredient explosion.
    """
    name = name.lower()

    # remove text after dash or comma
    name = re.split(r"[-,]", name)[0]

    # remove extra spaces
    name = name.strip()

    return name


def main():

    with open(INPUT_PATH, "r") as f:
        recipes = json.load(f)

    ingredient_set = set()

    for recipe in recipes:

        ingredients = recipe.get("extendedIngredients", [])

        for ing in ingredients:

            name = ing.get("name", "")

            name = normalize(name)

            if name:
                ingredient_set.add(name)

    ingredient_list = sorted(list(ingredient_set))

    print("Total recipes:", len(recipes))
    print("Unique ingredients:", len(ingredient_list))
    print()

    for ing in ingredient_list:
        print(ing)

    # save to file
    with open(OUTPUT_PATH, "w") as f:
        json.dump(ingredient_list, f, indent=2)

    print("\nSaved ingredient list to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
