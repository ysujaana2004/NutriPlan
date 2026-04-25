"""
build_walmart_index.py

Walmart equivalent of build_target_index.py:
- Reads the walmart_items/ directory (category folders containing *.json files)
- Flattens all products into one list
- Builds a category index (category -> list of products)
- Saves:
  - data/stores/walmart/products_flat.json
  - data/stores/walmart/products_by_category.json

Dataset shape:
{
  "products": [
    {"name": "...", "price": "...", "unit_price": "...?"},
    ...
  ]
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent

WALMART_ITEMS_DIR = REPO_ROOT / "walmart_items"
OUT_FLAT = BACKEND_DIR / "data" / "stores" / "walmart" / "products_flat.json"
OUT_BY_CAT = BACKEND_DIR / "data" / "stores" / "walmart" / "products_by_category.json"


def safe_read_json(path: Path) -> Any:
    """Read JSON with a clear error if a file is malformed."""

    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        raise RuntimeError(f"Failed reading JSON: {path}\n{exc}") from exc


def main() -> None:
    """Flatten Walmart category JSON files into backend runtime indexes."""

    if not WALMART_ITEMS_DIR.is_dir():
        raise FileNotFoundError(
            f"Could not find '{WALMART_ITEMS_DIR}'. "
            "Place your dataset folder there or change WALMART_ITEMS_DIR."
        )

    flat: list[dict[str, object]] = []
    by_cat: dict[str, list[dict[str, object]]] = {}

    for cat_path in sorted(WALMART_ITEMS_DIR.iterdir()):
        if not cat_path.is_dir():
            continue
        category = cat_path.name
        by_cat.setdefault(category, [])

        for file_path in sorted(cat_path.glob("*.json")):
            data = safe_read_json(file_path)
            products = data.get("products", [])
            if not isinstance(products, list):
                continue

            for product in products:
                name = str(product.get("name") or "").strip()
                if not name:
                    continue

                record = {
                    "category": category,
                    "source_file": file_path.name,
                    "name": name,
                    "price": product.get("price"),
                    "unit_price": product.get("unit_price"),
                }
                flat.append(record)
                by_cat[category].append(record)

    OUT_FLAT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FLAT, "w", encoding="utf-8") as handle:
        json.dump(flat, handle, indent=2)

    with open(OUT_BY_CAT, "w", encoding="utf-8") as handle:
        json.dump(by_cat, handle, indent=2)

    print(f"Categories found: {len(by_cat)}")
    print(f"Total products: {len(flat)}")
    print(f"Saved: {OUT_FLAT}")
    print(f"Saved: {OUT_BY_CAT}")


if __name__ == "__main__":
    main()
