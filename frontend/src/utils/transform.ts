// Transform backend response to frontend format
import type { BackendWeeklyPlan, BackendMeal } from '../services/api';
import type { DayPlan, MealSlot, Recipe } from '../types';

/**
 * Converts a backend meal to a frontend Recipe
 */
function backendMealToRecipe(meal: BackendMeal, index: number): Recipe {
  return {
    id: meal.recipe_id || `recipe-${meal.meal_type}-${index}`,
    name: meal.name,
    description: `${meal.name} - ${meal.meal_type}`,
    image: meal.image_url || `https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&sig=${index}`,
    calories: meal.nutrition.calories,
    protein: meal.nutrition.protein_g,
    carbs: meal.nutrition.carbs_g,
    fats: meal.nutrition.fat_g,
    cost: meal.estimated_cost_usd,
    ingredients: (meal.ingredients ?? []).map((ingredient) => ({
      id: ingredient.id,
      name: ingredient.name,
      amount: ingredient.amount,
      // Ingredient-level prices are not currently returned by backend.
      price: 0,
    })),
    instructions: meal.instructions ?? [],
  };
}

/**
 * Formats an ISO date string (YYYY-MM-DD) to a display format (e.g., "Feb 9")
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[date.getMonth()]} ${date.getDate()}`;
}

/**
 * Converts backend weekly plan to frontend DayPlan format
 */
export function transformBackendPlanToFrontend(backendPlan: BackendWeeklyPlan): DayPlan[] {
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  
  return backendPlan.days.map((day, dayIndex) => {
    const date = new Date(day.date);
    const dayName = dayNames[date.getDay()];
    
    const meals: MealSlot[] = day.meals.map((meal, mealIndex) => {
      const recipe = backendMealToRecipe(meal, dayIndex * 10 + mealIndex);
      
      return {
        id: `${day.date}-${meal.meal_type}-${mealIndex}`,
        type: meal.meal_type,
        recipe,
        day: dayName,
      };
    });

    return {
      day: dayName,
      date: formatDate(day.date),
      meals,
      totalCost: day.total_cost_usd,
      totalCalories: day.totals.calories,
    };
  });
}
