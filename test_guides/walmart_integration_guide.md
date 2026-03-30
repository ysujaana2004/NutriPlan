# NutriPlan Walmart Integration Guide

This guide details the step-by-step process for integrating the new `wallmart_items` dataset directly into your optimizer, allowing the system to seamlessly switch between Target and Walmart based on the user's location.

## Part 1: Standardize the Walmart Data
**Goal:** Ensure your Walmart JSON files can be read the same way as your Target JSON files.
1. Inspect one of your `wallmart_items` files (e.g., `chicken.json`).
2. Make sure the JSON shape matches your Target items exactly. Specifically, the python parser will need to easily find the price. If Walmart's price format looks like `"$5.98/lb"` and Target looks like `"$8.99"`, you'll need to make sure your price parser (`backend/app/matching.py`) can clean and extract both formats gracefully!

(DONE)


## Part 2: Refactor Data Access
**Goal:** Add a loader for Walmart data right next to your Target loader.
1. Open `backend/app/data_access.py`.
2. Find the global path for the Target items (e.g., `TARGET_PRODUCTS_FLAT_PATH`).
3. Add a new global path for Walmart: 
   `WALMART_PRODUCTS_FLAT_PATH = Path(__file__).parent.parent.parent / "wallmart_items" / "walmart_products_flat.json"` 
   *(Note: You might need a script to flatten the Walmart folder into a single JSON just like you did for Target).*
4. Copy the `load_cheapest_target_by_canonical_id()` function, rename it to `load_cheapest_walmart_by_canonical_id()`, and point it to the Walmart path.


(DONE )



## Part 3: Create the Pricing Service "Adapter"
**Goal:** Build a bridge so the optimizer doesn't have to care *which* store it uses.
1. Create a new file: `backend/app/pricing_service.py`.
2. Add a function that takes the `store_name` as a parameter and returns the correct pricing dictionary:
```python
from .data_access import load_cheapest_target_by_canonical_id, load_cheapest_walmart_by_canonical_id

def get_store_pricing(store_name: str) -> dict:
    if store_name.lower() == "walmart":
        return load_cheapest_walmart_by_canonical_id()
    # Default to Target
    return load_cheapest_target_by_canonical_id()
```
(DONE)


## Part 4: Upgrade the Optimizer
**Goal:** Swap out the hardcoded Target logic for the new dynamic pricing service.
1. Open `backend/app/optimizer.py`.
2. Look for every place you call `load_cheapest_target_by_canonical_id()`. There are likely two main spots:
   * Inside `build_shopping_list_summary(...)`
   * Inside `build_optimized_weekly_plan(...)` where it passes properties to the JSON output.
3. Add `store_name: str` to the parameters of `build_optimized_weekly_plan`.
4. Swap the direct Target loader calls with `get_store_pricing(store_name)` from the new `pricing_service.py`.

(DONE)

## Part 5: Connect the API 
**Goal:** Pass the Location Service choice down into the Optimizer.
1. Open `backend/app/main.py`.
2. Inside `optimized_meal_plan(...)`:
   * Use the `location_service.py` to find the nearest store based on the `zip_code` (e.g., Target or Walmart).
   * Pass that string ("Target" or "Walmart") down into `build_optimized_weekly_plan(...)`.

(DONE)

## Summary
By following these steps, your optimizer simply asks the `pricing_service` for "the prices," and the service handles all the logic of fetching either Walmart or Target. Your optimizer logic remains perfectly untouched and fully functional!
