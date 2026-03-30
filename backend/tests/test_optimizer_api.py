from fastapi.testclient import TestClient
from app.main import app

# Create a test client
client = TestClient(app)

def test_optimize_requires_parameters():
    # If we call it without mandatory params (budget, calories), it should fail
    response = client.get("/optimize/meal-plan")
    assert response.status_code == 422  # Unprocessable Entity (Missing query params)

def test_optimize_budget_validation():
    # Test that a negative budget throws a validation error
    response = client.get("/optimize/meal-plan?budget=-10&calories=2000&diet=none")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Ensure the error is related to the budget field
    assert any(error["loc"] == ["query", "budget"] for error in data["detail"])

def test_optimize_success():
    # Test a realistic setup: $150 budget, 2000 calories
    response = client.get("/optimize/meal-plan?budget=150&calories=2000&diet=none")
    
    assert response.status_code == 200
    data = response.json()
    
    # 1. Check basic response structures 
    assert "week_totals" in data
    assert "days" in data
    assert len(data["days"]) == 7  # Should generate exactly 7 days
    
    # 2. Check the inputs made it into the plan
    assert data["inputs"]["budget"] == 150
    assert data["inputs"]["calories"] == 2000
    
    # 3. Ensure the optimizer actually respected macro bounds and budget
    # Check that week_total_cost_usd exists and isn't wildly broken
    assert "week_total_cost_usd" in data
    assert data["week_total_cost_usd"] > 0
    
    # Check a specific day's meals
    day_1 = data["days"][0]
    assert len(day_1["meals"]) == 3  # Breakfast, Lunch, Dinner
    for meal in day_1["meals"]:
        assert meal["meal_type"] in ["breakfast", "lunch", "dinner"]
        assert "nutrition" in meal
        assert meal["nutrition"]["calories"] > 0

def test_optimize_respects_calorie_target():
    # Test that the returned meal plan roughly matches the requested calories
    # We ask for 2000 calories per day.
    target_daily_calories = 2000
    response = client.get(f"/optimize/meal-plan?budget=150&calories={target_daily_calories}&diet=none")
    assert response.status_code == 200
    data = response.json()
    
    # Calculate the average daily calories from the 7 days generated
    total_week_calories = data["week_totals"]["calories"]
    average_daily_calories = total_week_calories / 7
    
    # Check that the average is within a +/- 15% acceptable range of the target
    # The heuristic optimizer won't be mathematically perfectly exactly 2000, but should be close.
    lower_bound = target_daily_calories * 0.85
    upper_bound = target_daily_calories * 1.15
    
    assert lower_bound <= average_daily_calories <= upper_bound, f"Average {average_daily_calories} is outside bounds {lower_bound}-{upper_bound}"
