"""
build_target_index.py

Milestone 2.1:
- Reads the target_items/ directory (category folders containing *.json files)
- Flattens all products into one list
- Builds a category index (category -> list of products)
- Saves:
  - data/stores/target/products_flat.json
  - data/stores/target/products_by_category.json

Your dataset shape today:
{
  "products": [
    {"name": "...", "price": "...", "unit_price": "...?"},
    ...
  ]
}
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

# Resolve all paths from THIS file's location, not from current working directory.
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent

TARGET_ITEMS_DIR = REPO_ROOT / "target_items"
OUT_FLAT = BACKEND_DIR / "data" / "stores" / "target" / "products_flat.json"
OUT_BY_CAT = BACKEND_DIR / "data" / "stores" / "target" / "products_by_category.json"


def safe_read_json(path: Path) -> Any:
    """Read JSON with a clear error if file is bad."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed reading JSON: {path}\n{e}")


def main():
    if not TARGET_ITEMS_DIR.is_dir():
        raise FileNotFoundError(
            f"Could not find '{TARGET_ITEMS_DIR}'. "
            f"Place your dataset folder there or change TARGET_ITEMS_DIR."
        )

    flat: List[Dict[str, Any]] = []
    by_cat: Dict[str, List[Dict[str, Any]]] = {}

    for cat_path in sorted(TARGET_ITEMS_DIR.iterdir()):
        if not cat_path.is_dir():
            continue
        category = cat_path.name

        by_cat.setdefault(category, [])

        for fpath in sorted(cat_path.glob("*.json")):
            data = safe_read_json(fpath)

            products = data.get("products", [])
            if not isinstance(products, list):
                continue

            for p in products:
                name = (p.get("name") or "").strip()
                if not name:
                    continue

                record = {
                    "category": category,
                    "source_file": fpath.name,
                    "name": name,
                    "price": p.get("price"),
                    "unit_price": p.get("unit_price"),
                }
                flat.append(record)
                by_cat[category].append(record)

    OUT_FLAT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUT_FLAT, "w") as f:
        json.dump(flat, f, indent=2)

    with open(OUT_BY_CAT, "w") as f:
        json.dump(by_cat, f, indent=2)

    print(f"Categories found: {len(by_cat)}")
    print(f"Total products: {len(flat)}")
    print(f"Saved: {OUT_FLAT}")
    print(f"Saved: {OUT_BY_CAT}")


if __name__ == "__main__":
    main()
