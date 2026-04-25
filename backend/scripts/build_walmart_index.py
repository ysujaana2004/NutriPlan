"""Compatibility wrapper around build_index.py for Walmart."""

from __future__ import annotations

from build_index import main


if __name__ == "__main__":
    main(["--store", "walmart"])
