// API service for backend communication

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Backend response types (matching the FastAPI models)
export interface BackendNutrition {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface BackendIngredientLine {
  id: string;
  name: string;
  amount: string;
}

export interface BackendMeal {
  recipe_id: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner';
  name: string;
  servings: number;
  nutrition: BackendNutrition;
  estimated_cost_usd: number;
  image_url?: string | null;
  ingredients?: BackendIngredientLine[];
  instructions?: string[];
}

export interface BackendDayPlan {
  date: string;
  meals: BackendMeal[];
  totals: BackendNutrition;
  total_cost_usd: number;
}

export interface BackendShoppingListItem {
  canonical_id: string;
  canonical_name: string;
  product_name: string;
  category: string;
  unit_price_usd: number;
  estimated_units: number;
  estimated_total_cost_usd: number;
  recipes: string[];
}

export interface BackendMissingShoppingItem {
  canonical_id: string;
  canonical_name: string;
  recipes: string[];
}

export interface BackendShoppingListSummary {
  items: BackendShoppingListItem[];
  missing_items: BackendMissingShoppingItem[];
  total_estimated_cost_usd: number;
}

export interface BackendWeeklyPlan {
  inputs: {
    budget: number;
    calories: number;
    diet: string;
    start_date: string | null;
    store_name?: string;
  };
  days: BackendDayPlan[];
  week_totals: BackendNutrition;
  week_total_cost_usd: number;
  shopping_list?: BackendShoppingListSummary | null;
}

export interface ReplaceMealParams {
  current_plan: BackendWeeklyPlan;
  day_index: number;
  meal_type: 'breakfast' | 'lunch' | 'dinner';
  current_recipe_id?: string;
}

export interface MealPlanParams {
  budget: number;
  calories: number;
  diet?: 'none' | 'vegetarian' | 'high_protein' | 'low_carb';
  start_date?: string;
}

/**
 * Fetches a meal plan from the backend /optimize/meal-plan endpoint
 */
export async function fetchMealPlan(params: MealPlanParams): Promise<BackendWeeklyPlan> {
  const queryParams = new URLSearchParams({
    budget: params.budget.toString(),
    calories: params.calories.toString(),
    ...(params.diet && { diet: params.diet }),
    ...(params.start_date && { start_date: params.start_date }),
  });

  const response = await fetch(`${API_BASE_URL}/optimize/meal-plan?${queryParams}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch meal plan: ${response.status} ${errorText}`);
  }

  return response.json();
}

/**
 * Replaces one meal in an existing backend weekly plan.
 */
export async function replaceMealInPlan(params: ReplaceMealParams): Promise<BackendWeeklyPlan> {
  const response = await fetch(`${API_BASE_URL}/optimize/meal-plan/replace`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to replace meal: ${response.status} ${errorText}`);
  }

  return response.json();
}
