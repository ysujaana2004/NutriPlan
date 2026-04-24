from fastapi.testclient import TestClient
from app.main import app
from app.optimizer import build_optimized_weekly_plan, replace_meal_in_weekly_plan

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


def test_replace_meal_recomputes_totals_and_shopping_list():
    plan = build_optimized_weekly_plan(
        store_name="Target",
        budget=150,
        calories=2000,
        diet="none",
        start_date="2026-01-05",
        protein_target_g=None,
        carbs_target_g=None,
        fat_target_g=None,
    )

    day_index = 0
    meal_type = "lunch"
    original_meal = next(meal for meal in plan.days[day_index].meals if meal.meal_type == meal_type)
    original_recipe_id = original_meal.recipe_id

    updated = replace_meal_in_weekly_plan(
        current_plan=plan,
        day_index=day_index,
        meal_type=meal_type,
        current_recipe_id=original_recipe_id,
    )

    updated_meal = next(meal for meal in updated.days[day_index].meals if meal.meal_type == meal_type)
    assert updated_meal.recipe_id != original_recipe_id

    # Ensure original plan is not mutated.
    unchanged_original_meal = next(meal for meal in plan.days[day_index].meals if meal.meal_type == meal_type)
    assert unchanged_original_meal.recipe_id == original_recipe_id

    updated_day = updated.days[day_index]
    assert updated_day.totals.calories == sum(meal.nutrition.calories for meal in updated_day.meals)
    assert updated_day.totals.protein_g == sum(meal.nutrition.protein_g for meal in updated_day.meals)
    assert updated_day.totals.carbs_g == sum(meal.nutrition.carbs_g for meal in updated_day.meals)
    assert updated_day.totals.fat_g == sum(meal.nutrition.fat_g for meal in updated_day.meals)

    assert updated.week_totals.calories == sum(day.totals.calories for day in updated.days)
    assert updated.week_totals.protein_g == sum(day.totals.protein_g for day in updated.days)
    assert updated.week_totals.carbs_g == sum(day.totals.carbs_g for day in updated.days)
    assert updated.week_totals.fat_g == sum(day.totals.fat_g for day in updated.days)

    assert updated.shopping_list is not None
    assert updated.shopping_list.total_estimated_cost_usd > 0


def test_replace_meal_api_route_success():
    initial = client.get("/optimize/meal-plan?budget=150&calories=2000&diet=none&store_preference=Target")
    assert initial.status_code == 200
    plan = initial.json()

    lunch = next(meal for meal in plan["days"][0]["meals"] if meal["meal_type"] == "lunch")
    payload = {
        "current_plan": plan,
        "day_index": 0,
        "meal_type": "lunch",
        "current_recipe_id": lunch["recipe_id"],
    }

    response = client.post("/optimize/meal-plan/replace", json=payload)
    assert response.status_code == 200
    updated = response.json()

    updated_lunch = next(meal for meal in updated["days"][0]["meals"] if meal["meal_type"] == "lunch")
    assert updated_lunch["recipe_id"] != lunch["recipe_id"]
    assert "shopping_list" in updated
    assert updated["shopping_list"] is not None
