"""
append_recipe_pipeline.py

Append NEW recipes through your full existing pipeline:
1) Append IDs/titles -> data/recipes-random.json
2) Append full details -> data/recipes-random-full.json
3) Append nutrition macros -> data/recipes-nutrition.json

The script is append-safe:
- never deletes existing rows
- de-dupes by recipe id
- creates timestamped backups before writing
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DATA_DIR = BACKEND_DIR / "data"

RANDOM_PATH = DATA_DIR / "recipes-random.json"
FULL_PATH = DATA_DIR / "recipes-random-full.json"
NUTRITION_PATH = DATA_DIR / "recipes-nutrition.json"

RANDOM_SEARCH_URL = "https://api.spoonacular.com/recipes/complexSearch"
BULK_INFO_URL = "https://api.spoonacular.com/recipes/informationBulk"

RANDOM_BATCH_SIZE = 100
BULK_CHUNK_SIZE = 80
SLEEP_SECONDS = 0.25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append new recipes to random/full/nutrition files without overwriting existing data."
    )
    parser.add_argument(
        "--add-count",
        type=int,
        default=80,
        help="How many new recipes to add (default: 80).",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=8,
        help="Max random-fetch rounds used to discover unique IDs (default: 8).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write files; print planned counts only.",
    )
    return parser.parse_args()


def chunk_list(items: List[int], size: int) -> List[List[int]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected list JSON in {path}, got {type(data).__name__}")
    return data


def row_id(row: Dict[str, Any]) -> int | None:
    rid = row.get("id")
    try:
        return int(rid)
    except (TypeError, ValueError):
        return None


def id_set(rows: List[Dict[str, Any]]) -> set[int]:
    out: set[int] = set()
    for row in rows:
        rid = row_id(row)
        if rid is not None:
            out.add(rid)
    return out


def dedupe_by_id_keep_first(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[int] = set()
    for row in rows:
        rid = row_id(row)
        if rid is None or rid in seen:
            continue
        seen.add(rid)
        out.append(row)
    return out


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.stem}.backup_{stamp}{path.suffix}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def fetch_random_id_rows(api_key: str, number: int) -> List[Dict[str, Any]]:
    params = {
        "number": number,
        "sort": "random",
        "addRecipeInformation": "false",
        "addRecipeNutrition": "false",
        "apiKey": api_key,
    }
    resp = requests.get(RANDOM_SEARCH_URL, params=params, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Random fetch failed: {resp.status_code} {resp.text[:300]}")
    payload = resp.json()
    results = payload.get("results", [])
    return [{"id": r["id"], "title": r.get("title", "")} for r in results if "id" in r]


def fetch_bulk(api_key: str, ids: List[int], include_nutrition: bool) -> List[Dict[str, Any]]:
    params = {
        "ids": ",".join(map(str, ids)),
        "includeNutrition": "true" if include_nutrition else "false",
        "apiKey": api_key,
    }
    resp = requests.get(BULK_INFO_URL, params=params, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Bulk fetch failed: {resp.status_code} {resp.text[:300]}")
    payload = resp.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected bulk response type: {type(payload).__name__}")
    return payload


def extract_macros(recipe: Dict[str, Any]) -> Dict[str, float]:
    nutrients = (recipe.get("nutrition") or {}).get("nutrients") or []
    wanted = {"Calories", "Protein", "Carbohydrates", "Fat"}
    found: Dict[str, float] = {}
    for n in nutrients:
        name = n.get("name")
        if name in wanted:
            found[name] = float(n.get("amount", 0.0))
    return {
        "calories": found.get("Calories", 0.0),
        "protein": found.get("Protein", 0.0),
        "carbs": found.get("Carbohydrates", 0.0),
        "fat": found.get("Fat", 0.0),
    }


def main() -> None:
    args = parse_args()
    if args.add_count <= 0:
        raise ValueError("--add-count must be > 0")

    load_dotenv()
    api_key = os.getenv("SPOONACULAR_API_KEY")
    if not api_key:
        raise ValueError("SPOONACULAR_API_KEY not found in environment variables.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing_random = load_json_list(RANDOM_PATH)
    existing_full = load_json_list(FULL_PATH)
    existing_nutrition = load_json_list(NUTRITION_PATH)

    existing_ids_all = id_set(existing_random) | id_set(existing_full) | id_set(existing_nutrition)

    print(f"Existing rows: random={len(existing_random)} full={len(existing_full)} nutrition={len(existing_nutrition)}")
    print(f"Existing unique recipe IDs across all files: {len(existing_ids_all)}")

    # Step 1: collect fresh IDs/titles
    new_id_rows: List[Dict[str, Any]] = []
    new_ids_seen: set[int] = set()

    for round_idx in range(1, args.max_rounds + 1):
        if len(new_id_rows) >= args.add_count:
            break

        batch = fetch_random_id_rows(api_key, RANDOM_BATCH_SIZE)
        fresh_batch = []
        for row in batch:
            rid = row_id(row)
            if rid is None:
                continue
            if rid in existing_ids_all or rid in new_ids_seen:
                continue
            new_ids_seen.add(rid)
            fresh_batch.append({"id": rid, "title": row.get("title", "")})
            if len(new_id_rows) + len(fresh_batch) >= args.add_count:
                break

        new_id_rows.extend(fresh_batch)
        print(
            f"[round {round_idx}] random={len(batch)} fresh={len(fresh_batch)} collected={len(new_id_rows)}/{args.add_count}"
        )

        if round_idx < args.max_rounds:
            time.sleep(SLEEP_SECONDS)

    if len(new_id_rows) < args.add_count:
        raise RuntimeError(
            f"Only found {len(new_id_rows)} new IDs after {args.max_rounds} rounds. "
            "Increase --max-rounds and retry."
        )

    new_ids = [int(r["id"]) for r in new_id_rows]

    # Step 2: full recipe details for the NEW IDs
    new_full_rows: List[Dict[str, Any]] = []
    id_chunks = chunk_list(new_ids, BULK_CHUNK_SIZE)
    for idx, chunk in enumerate(id_chunks, start=1):
        print(f"[full {idx}/{len(id_chunks)}] fetching {len(chunk)} recipes...")
        rows = fetch_bulk(api_key, chunk, include_nutrition=False)
        new_full_rows.extend(rows)
        if idx < len(id_chunks):
            time.sleep(SLEEP_SECONDS)

    # Step 3: nutrition for the NEW IDs
    new_nutrition_rows: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(id_chunks, start=1):
        print(f"[nutrition {idx}/{len(id_chunks)}] fetching {len(chunk)} recipes...")
        rows = fetch_bulk(api_key, chunk, include_nutrition=True)
        for recipe in rows:
            rid = recipe.get("id")
            if rid is None:
                continue
            new_nutrition_rows.append(
                {
                    "id": rid,
                    "title": recipe.get("title", ""),
                    "nutrition": extract_macros(recipe),
                }
            )
        if idx < len(id_chunks):
            time.sleep(SLEEP_SECONDS)

    merged_random = dedupe_by_id_keep_first(existing_random + new_id_rows)
    merged_full = dedupe_by_id_keep_first(existing_full + new_full_rows)
    merged_nutrition = dedupe_by_id_keep_first(existing_nutrition + new_nutrition_rows)

    print(
        "Planned totals after append: "
        f"random={len(merged_random)} full={len(merged_full)} nutrition={len(merged_nutrition)}"
    )
    print(
        f"New rows fetched: ids={len(new_id_rows)} full={len(new_full_rows)} nutrition={len(new_nutrition_rows)}"
    )

    if args.dry_run:
        print("Dry run enabled. No files written.")
        return

    backups = {
        "random": backup_file(RANDOM_PATH),
        "full": backup_file(FULL_PATH),
        "nutrition": backup_file(NUTRITION_PATH),
    }

    RANDOM_PATH.write_text(json.dumps(merged_random, indent=2), encoding="utf-8")
    FULL_PATH.write_text(json.dumps(merged_full, indent=2), encoding="utf-8")
    NUTRITION_PATH.write_text(json.dumps(merged_nutrition, indent=2), encoding="utf-8")

    print("Backups created:")
    for key, path in backups.items():
        print(f"- {key}: {path if path else '(none, file did not exist)'}")
    print("Saved:")
    print(f"- {RANDOM_PATH}")
    print(f"- {FULL_PATH}")
    print(f"- {NUTRITION_PATH}")


if __name__ == "__main__":
    main()

