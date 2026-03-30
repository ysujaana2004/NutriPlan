# NutriPlan Unit Testing Guide

This guide explains how to set up and write unit tests for your FastAPI backend using `pytest` and `TestClient`.

## 1. Install Testing Dependencies
First, ensure you have the `pytest` testing library installed. Run this in your `backend` folder:
```bash
pip install pytest httpx
```
(DONE)

## 2. Setting Up Your Test Folder
Your backend already has a `tests/` folder. This is where all your test files should go. 
Make sure your file structure looks like this:
```text
backend/
├── app/
│   ├── main.py
│   ├── location_service.py
│   └── ...
└── tests/
    ├── __init__.py  (Can be an empty file)
    └── test_location_api.py  (New test file)
```
(DONE)


## 3. Writing Your First Test (Example: Testing the New Endpoint)
Create a file named `test_location_api.py` inside the `tests/` folder.
Here is an exact template you can use to test the `/stores/nearby` endpoint you just created:

```python
from fastapi.testclient import TestClient
from app.main import app

# This creates a dummy client to interact with your API as if a frontend was calling it
client = TestClient(app)

def test_nearby_stores_requires_zip_code():
    # Test throwing an error if NO zip code is provided
    response = client.get("/stores/nearby")
    assert response.status_code == 422  # HTTP 422 Unprocessable Entity

def test_nearby_stores_success():
    # Test a successful search
    response = client.get("/stores/nearby?zip_code=90210&store_name=Target")
    
    # 1. Check that the server returned a 200 OK status
    assert response.status_code == 200
    
    # 2. Check the JSON response payload
    data = response.json()
    assert data["zip_code"] == "90210"
    assert data["store_name"] == "Target"
    
    # Ensure there is a "results" list (even if the list is empty locally due to missing API keys)
    assert "results" in data
    assert isinstance(data["results"], list)
```

## 4. How to Run Your Tests
To actually run your tests and see if everything passes, open your terminal (make sure you are inside the `backend` folder), and type:

```bash
pytest tests/
```

If everything works, you will see a bunch of green dots and a message saying **"1 passed in 0.12s"**!

------------------------
### Best Practices:
*   **Name your files starting with `test_`:** Pytest automatically searches for any file named `test_something.py`.
*   **Name your functions starting with `test_`:** Pytest will only run functions that begin with the word `test_`.
*   **Use `assert`:** This is Python's built-in way to check if something is True. If `assert 1 == 1`, the test passes. If `assert 1 == 2`, the test fails and shows you the line of code that caused the crash.
