import type { Recipe, DayPlan, ShoppingItem, Store, BudgetEntry } from '../types';

export const MOCK_RECIPES: Recipe[] = [
  {
    id: 'r1',
    name: 'Oatmeal with Berries',
    description: 'Creamy oatmeal topped with fresh berries and a drizzle of honey.',
    image: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400',
    calories: 320,
    protein: 12,
    carbs: 52,
    fats: 8,
    cost: 2.5,
    nutritionScore: 92,
    ingredients: [
      { id: 'i1', name: 'Rolled oats', amount: '1 cup', price: 0.5 },
      { id: 'i2', name: 'Mixed berries', amount: '1/2 cup', price: 1.2 },
      { id: 'i3', name: 'Honey', amount: '1 tbsp', price: 0.3 },
    ],
  },
  {
    id: 'r2',
    name: 'Grilled Chicken Salad',
    description: 'Mixed greens with grilled chicken, cherry tomatoes, and light vinaigrette.',
    image: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400',
    calories: 420,
    protein: 38,
    carbs: 18,
    fats: 22,
    cost: 5.2,
    nutritionScore: 88,
    ingredients: [
      { id: 'i4', name: 'Chicken breast', amount: '150g', price: 2.8 },
      { id: 'i5', name: 'Mixed greens', amount: '2 cups', price: 1.0 },
      { id: 'i6', name: 'Cherry tomatoes', amount: '6', price: 0.6 },
    ],
  },
  {
    id: 'r3',
    name: 'Salmon with Vegetables',
    description: 'Baked salmon with roasted broccoli and quinoa.',
    image: 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400',
    calories: 520,
    protein: 42,
    carbs: 35,
    fats: 24,
    cost: 8.5,
    nutritionScore: 90,
    ingredients: [
      { id: 'i7', name: 'Salmon fillet', amount: '180g', price: 5.0 },
      { id: 'i8', name: 'Broccoli', amount: '1 cup', price: 0.8 },
      { id: 'i9', name: 'Quinoa', amount: '1/2 cup', price: 0.9 },
    ],
  },
  {
    id: 'r4',
    name: 'Avocado Toast',
    description: 'Whole grain toast with mashed avocado, lemon, and chili flakes.',
    image: 'https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400',
    calories: 280,
    protein: 8,
    carbs: 28,
    fats: 16,
    cost: 3.0,
    nutritionScore: 85,
    ingredients: [
      { id: 'i10', name: 'Whole grain bread', amount: '2 slices', price: 0.4 },
      { id: 'i11', name: 'Avocado', amount: '1/2', price: 1.2 },
    ],
  },
  {
    id: 'r5',
    name: 'Turkey Wrap',
    description: 'Whole wheat wrap with turkey, hummus, and veggies.',
    image: 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400',
    calories: 380,
    protein: 28,
    carbs: 42,
    fats: 12,
    cost: 4.2,
    nutritionScore: 86,
    ingredients: [
      { id: 'i12', name: 'Whole wheat wrap', amount: '1', price: 0.5 },
      { id: 'i13', name: 'Turkey slices', amount: '100g', price: 2.0 },
      { id: 'i14', name: 'Hummus', amount: '2 tbsp', price: 0.5 },
    ],
  },
  {
    id: 'r6',
    name: 'Vegetable Stir-Fry',
    description: 'Colorful vegetables with tofu and brown rice.',
    image: 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400',
    calories: 410,
    protein: 18,
    carbs: 48,
    fats: 16,
    cost: 4.8,
    nutritionScore: 87,
    ingredients: [
      { id: 'i15', name: 'Tofu', amount: '150g', price: 1.5 },
      { id: 'i16', name: 'Brown rice', amount: '1 cup', price: 0.6 },
      { id: 'i17', name: 'Mixed vegetables', amount: '2 cups', price: 2.0 },
    ],
  },
];

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function buildWeekPlan(): DayPlan[] {
  return DAYS.map((day, i) => {
    const recipes = [...MOCK_RECIPES].sort(() => Math.random() - 0.5);
    const meals = [
      { type: 'breakfast' as const, recipe: recipes[0] },
      { type: 'lunch' as const, recipe: recipes[1] },
      { type: 'dinner' as const, recipe: recipes[2] },
    ];
    return {
      day,
      date: `Feb ${10 + i}`,
      totalCost: meals.reduce((s, m) => s + m.recipe.cost, 0),
      totalCalories: meals.reduce((s, m) => s + m.recipe.calories, 0),
      meals: meals.map((m, j) => ({
        id: `${day}-${m.type}-${j}`,
        type: m.type,
        recipe: m.recipe,
        day,
      })),
    };
  });
}

export const MOCK_WEEK_PLAN: DayPlan[] = buildWeekPlan();

export const MOCK_SHOPPING_ITEMS: ShoppingItem[] = [
  { id: 's1', name: 'Rolled oats', amount: '2 cups', price: 1.0, storeId: 'store1', storeName: 'Whole Foods', category: 'Grains', available: true },
  { id: 's2', name: 'Chicken breast', amount: '500g', price: 6.5, storeId: 'store1', storeName: 'Whole Foods', category: 'Protein', available: true },
  { id: 's3', name: 'Salmon fillet', amount: '360g', price: 10.0, storeId: 'store2', storeName: 'Trader Joe\'s', category: 'Protein', available: true },
  { id: 's4', name: 'Mixed berries', amount: '1 cup', price: 2.4, storeId: 'store1', storeName: 'Whole Foods', category: 'Produce', available: true },
  { id: 's5', name: 'Avocado', amount: '2', price: 2.4, storeId: 'store2', storeName: 'Trader Joe\'s', category: 'Produce', available: true },
];

export const MOCK_STORES: Store[] = [
  { id: 'store1', name: 'Whole Foods', distance: 1.2, totalPrice: 18.5, items: MOCK_SHOPPING_ITEMS.filter(i => i.storeId === 'store1') },
  { id: 'store2', name: 'Trader Joe\'s', distance: 2.1, totalPrice: 16.2, items: MOCK_SHOPPING_ITEMS.filter(i => i.storeId === 'store2') },
];

export const MOCK_BUDGET: BudgetEntry[] = [
  { id: 'b1', weekId: 'w1', label: 'Week of Feb 3', spent: 72, budget: 100, category: 'groceries', date: '2025-02-09' },
  { id: 'b2', weekId: 'w2', label: 'Week of Feb 10', spent: 45, budget: 100, category: 'groceries', date: '2025-02-09' },
];

export const USER_NAME = 'Alex';
