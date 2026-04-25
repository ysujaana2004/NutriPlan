from .data_access import load_cheapest_products_by_store

def get_store_pricing(store_name: str) -> dict:
    """Return canonical-id -> cheapest store product mapping for the selected store."""

    return load_cheapest_products_by_store(store_name)
