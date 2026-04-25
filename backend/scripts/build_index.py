"""
build_index.py

Generic store index builder.

Usage:
  python backend/scripts/build_index.py --store target
  python backend/scripts/build_index.py --store walmart
  python backend/scripts/build_index.py --store bjs
  python backend/scripts/build_index.py --store whole_foods
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
DATA_STORES_DIR = BACKEND_DIR / "data" / "stores"

DEFAULT_ITEMS_DIR_BY_STORE = {
    "target": REPO_ROOT / "store_inventories" / "target_items",
    "walmart": REPO_ROOT / "store_inventories" / "walmart_items",
    "bjs": REPO_ROOT / "store_inventories" / "BJs_items",
    "whole_foods": REPO_ROOT / "store_inventories" / "whole_foods_items",
}

STORE_ALIASES = {
    "bj": "bjs",
    "bj_s": "bjs",
    "bj's": "bjs",
    "wholefoods": "whole_foods",
}


def normalize_store_key(raw: str) -> str:
    """Normalize user input into a canonical store key."""

    token = re.sub(r"[^a-z0-9]+", "_", str(raw).strip().lower()).strip("_")
    return STORE_ALIASES.get(token, token)


def safe_read_json(path: Path) -> Any:
    """Read JSON and raise a clear error for malformed files."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Failed reading JSON: {path}\n{exc}") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build store product indexes for one store key.")
    parser.add_argument("--store", required=True, help="Store key/name (e.g. target, walmart, bjs, whole_foods).")
    parser.add_argument(
        "--items-dir",
        default=None,
        help="Optional raw items directory. If omitted, uses built-in defaults for known stores.",
    )
    return parser.parse_args(argv)


def resolve_items_dir(store_key: str, items_dir_arg: str | None) -> Path:
    """Resolve source raw-items directory from CLI arg or known defaults."""

    if items_dir_arg:
        path = Path(items_dir_arg)
        return path if path.is_absolute() else REPO_ROOT / path

    path = DEFAULT_ITEMS_DIR_BY_STORE.get(store_key)
    if path is None:
        raise ValueError(
            f"No default items directory known for store '{store_key}'. "
            "Pass --items-dir explicitly."
        )
    return path


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    store_key = normalize_store_key(args.store)
    items_dir = resolve_items_dir(store_key, args.items_dir)

    if not items_dir.is_dir():
        raise FileNotFoundError(
            f"Could not find items directory: {items_dir}. "
            "Provide a valid --items-dir or verify the default mapping."
        )

    out_dir = DATA_STORES_DIR / store_key
    out_flat = out_dir / "products_flat.json"
    out_by_cat = out_dir / "products_by_category.json"

    flat: list[dict[str, object]] = []
    by_cat: dict[str, list[dict[str, object]]] = {}

    for category_path in sorted(items_dir.iterdir()):
        if not category_path.is_dir():
            continue
        category = category_path.name
        by_cat.setdefault(category, [])

        for file_path in sorted(category_path.glob("*.json")):
            payload = safe_read_json(file_path)
            products = payload.get("products", [])
            if not isinstance(products, list):
                continue

            for product in products:
                name = str(product.get("name") or "").strip()
                if not name:
                    continue

                row = {
                    "category": category,
                    "source_file": file_path.name,
                    "name": name,
                    "price": product.get("price"),
                    "unit_price": product.get("unit_price"),
                }
                flat.append(row)
                by_cat[category].append(row)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_flat.write_text(json.dumps(flat, indent=2), encoding="utf-8")
    out_by_cat.write_text(json.dumps(by_cat, indent=2), encoding="utf-8")

    print(f"Store: {store_key}")
    print(f"Categories found: {len(by_cat)}")
    print(f"Total products: {len(flat)}")
    print(f"Saved: {out_flat}")
    print(f"Saved: {out_by_cat}")


if __name__ == "__main__":
    main()
