from fastapi.testclient import TestClient
from app.main import app

# This creates a dummy client to interact API (acts like the frontend)
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