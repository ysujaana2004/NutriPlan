# NutriPlan Backend

This folder contains the **backend service** for NutriPlan.  
The backend is responsible for generating meal plans, computing nutrition and costs, and exposing a clean API that the frontend can consume.

The backend is implemented in **Python using FastAPI** and is developed independently of the frontend and data components, with clear interfaces between them.

---

## Purpose of the Backend

The backend’s responsibilities include:
- Exposing HTTP API endpoints for the frontend
- Generating weekly meal plans based on user inputs
- Computing nutrition totals (calories, macros, etc.)
- Estimating grocery costs
- Integrating with external data sources (USDA, recipes, grocery pricing)
- Enforcing a stable API schema

The backend **does not handle UI logic** and **does not scrape or collect raw data directly**.  
Instead, it calls well-defined functions provided by the data layer.

---

## Folder Structure

    backend/
    ├─ app/
    │  ├─ main.py        # FastAPI app entry point (Week 1 demo lives here)
    │  ├─ api.py         # API routes (future)
    │  ├─ schemas.py     # Pydantic request/response models (API contract)
    │  ├─ services.py    # Core backend logic (planner, nutrition, pricing)
    │  ├─ config.py      # Environment variables and configuration
    │  └─ __init__.py
    ├─ tests/
    │  ├─ test_demo_api.py
    │  └─ __init__.py
    ├─ weekly-updates/   # Weekly progress reports (one per week)
    ├─ requirements.txt
    ├─ .env.example
    └─ README.md

**Note:** In early weeks, code may temporarily live in `main.py` for simplicity.  
As the project progresses, logic should be moved into `schemas.py`, `api.py`, and `services.py`.

---

## How to Run the Backend (Local Development)

From the **repository root**:

    uvicorn backend.app.main:app --reload

The backend will be available at:

    http://127.0.0.1:8000

---

## API Documentation

FastAPI automatically generates interactive API documentation.

Once the server is running, visit:

    http://127.0.0.1:8000/docs

This page shows:
- Available endpoints
- Required query parameters
- Example requests and responses
- Response schemas

---

## Weekly Progress Updates

All backend progress is documented weekly in:

    backend/weekly-updates/

Each file follows a consistent format and includes:
- What was completed that week
- How to run and test the work
- Known limitations
- Planned work for the next week

Example:

    backend/weekly-updates/week-01.md

This makes backend progress transparent to teammates, instructors, and reviewers.

---

## Development Philosophy

- **Schema-first**: API response shapes are defined explicitly and enforced
- **Separation of concerns**: endpoints, logic, and data access are kept separate
- **Deterministic outputs** in early demos to avoid frontend breakage
- **Incremental complexity**: start simple, then layer in real logic

---

## Current Status

- Week 1: Clickable demo API using fake data (completed)
- Real nutrition, pricing, and planning logic will be integrated in later weeks
- API schema stability is prioritized to avoid breaking frontend integration

---

## Notes

- Environment variables should be placed in a local `.env` file (see `.env.example`)
- The backend is designed to work within a **monorepo** alongside `frontend/` and `data/`

For detailed weekly progress, see the files in `backend/weekly-updates/`.