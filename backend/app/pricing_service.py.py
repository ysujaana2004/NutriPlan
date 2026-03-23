from .data_access import load_cheapest_target_by_canonical_id, load_cheapest_walmart_by_canonical_id

def get_store_pricing(store_name: str) -> dict:
    if store_name.lower() == "walmart":
        return load_cheapest_walmart_by_canonical_id()
    # Default to Target
    return load_cheapest_target_by_canonical_id()