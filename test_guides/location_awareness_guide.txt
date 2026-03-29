# NutriPlan Week 7 Milestone: Location Awareness Implementation Guide

This guide breaks down the "Week 7 (Mar 17 – Mar 23): Location Awareness" milestone into actionable technical steps for both the frontend and backend.

## 1. Backend: Update API Schemas
**Goal:** Allow the frontend to send a ZIP code in request payloads and return recommended stores.
* Step 1.1: Open `backend/app/schemas.py`.
* Step 1.2: Add an optional `zip_code: str | None = None` field to the request models for `/optimize/meal-plan` and potentially `/demo/meal-plan`.
* Step 1.3: Update response models (`WeeklyPlan` or the shopping list model) to return a new payload:
    * `recommended_store: dict = {"name": "Target", "address": "123 Main St", "distance_miles": 1.2}`

## 2. Backend: Location & Price Logic
**Goal:** Mock or implement store location filtering and location-based price validation.
* Step 2.1: Create a new service file, e.g., `backend/app/location_service.py`.
* Step 2.2: Add a function `find_nearest_stores(zip_code: str)` that returns a list of mock stores based on the provided ZIP code. This can be hardcoded dictionary lookups (e.g., if ZIP starts with 90, return California Target locations) or integrate a free geocoding API.
* Step 2.3: In `backend/app/optimizer.py`, modify your pricing logic. If a ZIP code is provided, fetch the nearest store from `location_service` and apply a mock "regional price modifier" (e.g., +5% for urban ZIP codes) to the `target_items` costs.
* Step 2.4: Update the router in `backend/app/main.py` to pass the ZIP code down through to the optimizer and include the recommended store in the response.

## 3. Frontend: User Input for ZIP Code
**Goal:** Give the user a way to input their ZIP code on the dashboard or settings page.
* Step 3.1: Open `frontend/src/pages/Settings.tsx` (or `Dashboard.tsx`, depending on where you want it).
* Step 3.2: Add a new text `<input type="text" placeholder="Enter ZIP Code" />` bound to a React state variable `zipCode`.
* Step 3.3: (Optional but recommended) Validate that the ZIP code is a 5-digit number.
* Step 3.4: Save the `zipCode` to global state (Context/Redux/Zustand) or `localStorage` so it persists across sessions.

## 4. Frontend: Pass Location to API
**Goal:** Modify API calls to include the ZIP code.
* Step 4.1: If using a centralized API client or `fetch` functions in your components, retrieve the saved `zipCode`.
* Step 4.2: Append `&zip_code=12345` as a query parameter when calling `/optimize/meal-plan` or include it in the JSON body.

## 5. Frontend: Display Store Output
**Goal:** Show the recommended store to the user alongside the shopping list.
* Step 5.1: Open `frontend/src/pages/ShoppingList.tsx`.
* Step 5.2: Create a new UI card at the top of the shopping list: "Recommended Store for Your Location".
* Step 5.3: Parse the `recommended_store` object from the backend API response and display the store name, address, and estimated distance.
* Step 5.4: Use `lucide-react` icons (like `<MapPin />`) to make the interface look polished.

## 6. Testing & Validation
**Goal:** Ensure location logic works as expected.
* Step 6.1: Run `uvicorn backend.app.main:app --reload` and test the `/docs` UI.
* Step 6.2: Ensure entering different ZIP codes yields different store recommendations or regional price fluctuations in the meal plan cost.
* Step 6.3: Ensure omitting the ZIP code falls back gracefully without breaking the app.
