export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

export interface Recipe {
  id: string;
  name: string;
  description: string;
  image: string;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
  cost: number;
  ingredients: RecipeIngredient[];
  instructions?: string[];
  nutritionScore?: number;
}

export interface RecipeIngredient {
  id: string;
  name: string;
  amount: string;
  price: number;
}

export interface MealSlot {
  id: string;
  type: MealType;
  recipe: Recipe;
  day: string;
}

export interface DayPlan {
  day: string;
  date: string;
  meals: MealSlot[];
  totalCost: number;
  totalCalories: number;
}

export interface ShoppingItem {
  id: string;
  name: string;
  amount: string;
  price: number;
  storeId: string;
  storeName: string;
  storeLogo?: string;
  category: string;
  available: boolean;
  recipeId?: string;
}

export interface Store {
  id: string;
  name: string;
  logo?: string;
  distance: number;
  totalPrice: number;
  items: ShoppingItem[];
}

export interface UserPreferences {
  budget: number;
  healthGoal: string;
  location: string;
  dietary: ('vegan' | 'halal' | 'gluten-free' | 'low-carb')[];
  livePricing: boolean;
}

export interface WeekPreferences {
  weekId: string;
  weekLabel: string;
  budget?: number;
  healthGoal?: string;
  dietary?: string[];
}

export interface BudgetEntry {
  id: string;
  weekId: string;
  label: string;
  spent: number;
  budget: number;
  category: 'groceries' | 'eating_out' | 'other';
  date: string;
}
