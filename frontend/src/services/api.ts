// API service for backend communication

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Backend response types (matching the FastAPI models)
export interface BackendNutrition {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface BackendMeal {
  meal_type: 'breakfast' | 'lunch' | 'dinner';
  name: string;
  servings: number;
  nutrition: BackendNutrition;
  estimated_cost_usd: number;
}

export interface BackendDayPlan {
  date: string;
  meals: BackendMeal[];
  totals: BackendNutrition;
  total_cost_usd: number;
}

export interface BackendWeeklyPlan {
  inputs: {
    budget: number;
    calories: number;
    diet: string;
    start_date: string | null;
  };
  days: BackendDayPlan[];
  week_totals: BackendNutrition;
  week_total_cost_usd: number;
}

export interface MealPlanParams {
  budget: number;
  calories: number;
  diet?: 'none' | 'vegetarian' | 'high_protein' | 'low_carb';
  start_date?: string;
}

/**
 * Fetches a meal plan from the backend /demo/meal-plan endpoint
 */
export async function fetchMealPlan(params: MealPlanParams): Promise<BackendWeeklyPlan> {
  const queryParams = new URLSearchParams({
    budget: params.budget.toString(),
    calories: params.calories.toString(),
    ...(params.diet && { diet: params.diet }),
    ...(params.start_date && { start_date: params.start_date }),
  });

  const response = await fetch(`${API_BASE_URL}/demo/meal-plan?${queryParams}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch meal plan: ${response.status} ${errorText}`);
  }

  return response.json();
}

