"""
build_ingredient_universe.py

- Reads data/recipes-full.json
- Extracts ingredient names using nameClean when available
- Aggressively filters out instruction fragments / junk
- Normalizes common variants
- Writes data/ingredients-from-recipes.json
"""

import json
import os
import re

INPUT_PATH = "data/recipes-full.json"
OUTPUT_PATH = "data/ingredients-from-recipes.json"

# Expand over time as you see patterns.
NORMALIZE_MAP = {
    # salts/pepper
    "kosher salt": "salt",
    "sea salt": "salt",
    "coarse salt": "salt",
    "coarse sea salt": "salt",
    "ground pepper": "black pepper",
    "pepper": "black pepper",

    # oils
    "extra virgin olive oil": "olive oil",
    "virgin olive oil": "olive oil",
    "quality olive oil": "olive oil",

    # onions
    "green onion": "scallion",
    "spring onion": "scallion",

    # tomatoes typos/variants
    "tomatoe": "tomato",
    "plum tomatoe": "plum tomato",
    "beefsteak tomatoe": "beefsteak tomato",
    "canned tomatoe": "canned tomato",
    "sundried tomatoe": "sun-dried tomato",

    # dairy wording
    "heavy whipping cream": "heavy cream",
    "thickened cream": "heavy cream",
    "natural yoghurt": "yogurt",
    "nonfat milk": "milk",

    # sugar
    "confectioner's sugar": "powdered sugar",
    "confectioners' sugar": "powdered sugar",
    "icing sugar": "powdered sugar",
    "icing mixture/sugar": "powdered sugar",
}

# Phrases that scream "this is an instruction sentence"
BAD_PHRASES = [
    "add ", "stir", "simmer", "allow", "until", "preferably", "to taste",
    "drizzle", "pinch", "batch", "remove", "from a local", "cups", "teaspoon",
]

# Brand-ish tokens: if present, we usually want to drop the whole thing
BRAND_TOKENS = ["barilla", "botticelli", "goya", "jif", "elmhurst", "mcvitie", "lawry"]


def looks_like_sentence(s: str) -> bool:
    """
    Heuristic: reject long instruction-like strings.
    """
    if len(s) >= 45:
        return True
    if any(p in s for p in BAD_PHRASES) and len(s) >= 18:
        return True
    # multiple numbers often means it's not a clean ingredient name
    if len(re.findall(r"\d", s)) >= 2:
        return True
    return False


def drop_brand(s: str) -> bool:
    """
    If it contains a strong brand token, drop it (or map it yourself later).
    """
    return any(tok in s for tok in BRAND_TOKENS)


def normalize_name(raw: str) -> str:
    """
    Normalize and clean an ingredient name into a canonical-ish token.
    """
    s = (raw or "").lower().strip()

    # Remove parentheses notes
    s = re.sub(r"\([^)]*\)", "", s).strip()

    # Remove anything after separators (often instructions)
    s = re.split(r"\s*[-–—:,;]\s*", s)[0].strip()

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    # Apply explicit mapping
    s = NORMALIZE_MAP.get(s, s)

    # Light plural squash (conservative)
    if s.endswith("ies") and len(s) > 4:
        s = s[:-3] + "y"
    elif s.endswith("s") and len(s) > 3 and not s.endswith(("ss", "us", "is")):
        s = s[:-1]

    return s


def main():
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Missing {INPUT_PATH}. Run Step 2 first.")

    with open(INPUT_PATH, "r") as f:
        recipes = json.load(f)

    unique = set()

    for r in recipes:
        for ing in r.get("extendedIngredients", []):
            # IMPORTANT: prefer nameClean
            raw = ing.get("nameClean") or ing.get("name") or ing.get("originalName") or ""
            raw = raw.strip()

            if not raw:
                continue

            s = raw.lower().strip()

            # hard filters
            if looks_like_sentence(s):
                continue
            if drop_brand(s):
                continue
            if s in {"x", "yo", "old", "semi", "sea", "sun"}:
                continue

            norm = normalize_name(raw)
            if norm and not looks_like_sentence(norm):
                unique.add(norm)

    out = sorted(unique)

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Recipes scanned: {len(recipes)}")
    print(f"Unique ingredients (cleaned): {len(out)}")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()