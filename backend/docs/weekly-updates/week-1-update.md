# Week 1 Backend Update – Clickable Demo API (Fake Data)

**Branch:** backend  
**Location:** backend/weekly-updates/week-01.md

---

## Summary
This week focused on setting up the backend foundation and delivering a **working, end-to-end demo API** using fake data. The goal was to prove that the backend can accept inputs and return a complete weekly meal plan in a stable JSON format, independent of frontend or data logic.

This unblocks frontend development early and establishes a clear API contract that future backend work will build upon.

---

## What Was Accomplished
- Set up a FastAPI backend inside the repo (`backend/`)
- Implemented a demo endpoint:
  - `GET /demo/meal-plan`
- Defined and enforced a clear response schema using Pydantic models
- Demo endpoint returns:
  - A 7-day weekly meal plan
  - Breakfast, lunch, and dinner for each day
  - Nutrition data per meal
  - Daily nutrition and cost totals
  - Weekly nutrition and cost totals
- Added input validation for required parameters (`budget`, `calories`)
- Enabled CORS to allow future frontend integration
- Added a simple health check endpoint (`GET /health`)
- Fully documented the backend code with detailed comments and docstrings

All meal data, nutrition values, and costs are intentionally fake and deterministic for demo purposes.

---

## How to Run the Backend
From the repository root (`NutriPlan/`):

    uvicorn backend.app.main:app --reload

The backend will be available at:

    http://127.0.0.1:8000

---

## How to Test

### Swagger UI (Recommended)
Open in a browser:

    http://127.0.0.1:8000/docs

### Example API Call

    curl "http://127.0.0.1:8000/demo/meal-plan?budget=70&calories=2200&diet=none"

### Expected Output
- HTTP 200 response
- JSON object containing:
  - `days` array of length 7
  - 3 meals per day
  - `totals` for each day
  - `week_totals` and `week_total_cost_usd`

---

## Notes / Limitations
- Meal plans, nutrition data, and pricing are hardcoded and fake
- Endpoint exists only to demonstrate API flow and schema stability
- No real meal-planning logic, nutrition computation, or pricing integration yet

---

## Next Week (Planned)
- Integrate real nutrition data (USDA + recipe APIs)
- Replace fake nutrition values with real computed totals
- Maintain the same API schema to avoid breaking frontend integration

---

## Dated: 02/08/2026
