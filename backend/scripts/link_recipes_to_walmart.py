"""Compatibility wrapper around link_recipes.py for Walmart."""

from __future__ import annotations

from link_recipes import main


if __name__ == "__main__":
    main(["--store", "walmart"])
