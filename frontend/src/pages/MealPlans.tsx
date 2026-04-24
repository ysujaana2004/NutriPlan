import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart, Plus, Trash2, RefreshCw, Settings2 } from 'lucide-react';
import { MOCK_WEEK_PLAN, MOCK_RECIPES } from '../data/mock';
import type { DayPlan, MealSlot, MealType, Recipe } from '../types';
import { replaceMealInPlan, type BackendWeeklyPlan } from '../services/api';
import { transformBackendPlanToFrontend } from '../utils/transform';
import { RecipeDetailModal } from '../components/Modals/RecipeDetailModal';
import { WeekPreferencesModal } from '../components/Modals/WeekPreferencesModal';

const MEAL_LABELS: Record<MealType, string> = {
  breakfast: 'Breakfast',
  lunch: 'Lunch',
  dinner: 'Dinner',
  snack: 'Snack',
};

export function MealPlans() {
  const navigate = useNavigate();

  const loadGeneratedBackendPlan = (): BackendWeeklyPlan | null => {
    try {
      const stored = sessionStorage.getItem('generatedBackendPlan');
      if (stored) {
        return JSON.parse(stored) as BackendWeeklyPlan;
      }
    } catch (e) {
      console.error('Failed to parse stored backend plan:', e);
    }
    return null;
  };

  // Check for generated plan from sessionStorage, otherwise use mock data.
  const getInitialPlan = (backendPlan: BackendWeeklyPlan | null): DayPlan[] => {
    if (backendPlan) {
      return transformBackendPlanToFrontend(backendPlan);
    }

    try {
      const stored = sessionStorage.getItem('generatedPlan');
      if (stored) {
        return JSON.parse(stored) as DayPlan[];
      }
    } catch (e) {
      console.error('Failed to parse stored frontend plan:', e);
    }
    return MOCK_WEEK_PLAN;
  };

  const [backendPlan, setBackendPlan] = useState<BackendWeeklyPlan | null>(loadGeneratedBackendPlan);
  const [plan, setPlan] = useState<DayPlan[]>(getInitialPlan(backendPlan));
  const [activeDay, setActiveDay] = useState(0);
  const [recipeModal, setRecipeModal] = useState<Recipe | null>(null);
  const [weekPrefsOpen, setWeekPrefsOpen] = useState(false);
  const [refreshingSlotId, setRefreshingSlotId] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  const day = plan[activeDay];
  const backendManaged = backendPlan !== null;
  const totalWeeklyCost = plan.reduce((s, d) => s + d.totalCost, 0);
  const totalWeeklyCal = plan.reduce((s, d) => s + d.totalCalories, 0);

  const removeMeal = (slotId: string) => {
    setPlan((prev) =>
      prev.map((d) => ({
        ...d,
        meals: d.meals.filter((m) => m.id !== slotId),
        totalCost: d.meals
          .filter((m) => m.id !== slotId)
          .reduce((s, m) => s + m.recipe.cost, 0),
        totalCalories: d.meals
          .filter((m) => m.id !== slotId)
          .reduce((s, m) => s + m.recipe.calories, 0),
      }))
    );
  };

  const addMeal = (dayIndex: number, type: MealType) => {
    const recipe = MOCK_RECIPES[Math.floor(Math.random() * MOCK_RECIPES.length)];
    const newSlot: MealSlot = {
      id: `new-${dayIndex}-${type}-${Date.now()}`,
      type,
      recipe,
      day: plan[dayIndex].day,
    };
    setPlan((prev) => {
      const next = [...prev];
      const day = { ...next[dayIndex] };
      day.meals = [...day.meals, newSlot];
      day.totalCost += recipe.cost;
      day.totalCalories += recipe.calories;
      next[dayIndex] = day;
      return next;
    });
  };

  const isRefreshableMealType = (type: MealType): type is 'breakfast' | 'lunch' | 'dinner' =>
    type === 'breakfast' || type === 'lunch' || type === 'dinner';

  const handleRefreshMeal = async (slot: MealSlot) => {
    setRefreshError(null);
    if (!backendPlan) {
      setRefreshError('Refresh is only available for backend-generated meal plans.');
      return;
    }
    if (!isRefreshableMealType(slot.type)) {
      setRefreshError('Only breakfast, lunch, and dinner can be refreshed.');
      return;
    }

    setRefreshingSlotId(slot.id);
    try {
      const updatedBackendPlan = await replaceMealInPlan({
        current_plan: backendPlan,
        day_index: activeDay,
        meal_type: slot.type,
        current_recipe_id: slot.recipe.id,
      });
      const updatedFrontendPlan = transformBackendPlanToFrontend(updatedBackendPlan);
      setBackendPlan(updatedBackendPlan);
      setPlan(updatedFrontendPlan);

      sessionStorage.setItem('generatedBackendPlan', JSON.stringify(updatedBackendPlan));
      sessionStorage.setItem('generatedPlan', JSON.stringify(updatedFrontendPlan));
      sessionStorage.setItem('generatedShoppingList', JSON.stringify(updatedBackendPlan.shopping_list ?? null));
    } catch (error) {
      setRefreshError(error instanceof Error ? error.message : 'Failed to refresh meal.');
    } finally {
      setRefreshingSlotId(null);
    }
  };

  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Meal Plan</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setWeekPrefsOpen(true)}
            className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <Settings2 className="h-4 w-4" />
            Week preferences
          </button>
          <button
            onClick={() => navigate('/shopping-list')}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
          >
            <ShoppingCart className="h-4 w-4" />
            View Shopping List
          </button>
        </div>
      </div>
      {refreshError && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {refreshError}
        </div>
      )}

      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="flex-1">
          <div className="flex gap-1 overflow-x-auto rounded-t-xl border border-b-0 border-gray-200 bg-gray-50 p-1">
            {plan.map((d, i) => (
              <button
                key={d.day}
                onClick={() => setActiveDay(i)}
                className={`min-w-[4rem] rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  i === activeDay ? 'bg-white text-primary shadow-sm' : 'text-gray-600 hover:bg-white/60'
                }`}
              >
                {d.day}
              </button>
            ))}
          </div>
          <div className="rounded-b-xl border border-gray-200 bg-white p-4">
            <p className="mb-4 text-sm text-gray-500">{day.date}</p>
            <div className="space-y-4">
              {day.meals.map((slot) => (
                <div
                  key={slot.id}
                  className="flex flex-col gap-3 rounded-xl border border-gray-200 bg-gray-50/50 p-4 sm:flex-row sm:items-center"
                >
                  <div className="flex-1 sm:flex sm:items-center sm:gap-4">
                    <img
                      src={slot.recipe.image}
                      alt=""
                      className="h-20 w-28 shrink-0 rounded-lg object-cover"
                    />
                    <div>
                      <p className="text-xs font-medium uppercase text-gray-500">
                        {MEAL_LABELS[slot.type]}
                      </p>
                      <p className="font-medium text-gray-900">{slot.recipe.name}</p>
                      <p className="text-sm text-gray-500">
                        {slot.recipe.calories} cal · ${slot.recipe.cost.toFixed(2)}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setRecipeModal(slot.recipe)}
                      className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      View Recipe
                    </button>
                    <button
                      onClick={() => handleRefreshMeal(slot)}
                      disabled={!backendManaged || refreshingSlotId !== null || !isRefreshableMealType(slot.type)}
                      className="flex items-center gap-1 rounded-lg border border-primary bg-primary-light/30 px-3 py-1.5 text-sm font-medium text-primary hover:bg-primary-light/50"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      {refreshingSlotId === slot.id ? 'Refreshing...' : 'Change'}
                    </button>
                    <button
                      onClick={() => removeMeal(slot.id)}
                      disabled={backendManaged}
                      className="flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-100"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Remove
                    </button>
                  </div>
                </div>
              ))}
              <div className="flex flex-wrap gap-2">
                {(['breakfast', 'lunch', 'dinner'] as MealType[]).map((type) => (
                  <button
                    key={type}
                    onClick={() => addMeal(activeDay, type)}
                    disabled={backendManaged}
                    className="flex items-center gap-1 rounded-lg border border-dashed border-gray-300 bg-white px-3 py-2 text-sm text-gray-500 hover:border-primary hover:bg-primary-light/10 hover:text-primary"
                  >
                    <Plus className="h-4 w-4" />
                    Add {MEAL_LABELS[type]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        <aside className="w-full rounded-xl border border-gray-200 bg-white p-5 lg:w-72">
          <h3 className="mb-4 font-semibold text-gray-900">Day summary</h3>
          <div className="space-y-2 text-sm">
            <p className="flex justify-between">
              <span className="text-gray-500">Total daily cost</span>
              <span className="font-medium">${day.totalCost.toFixed(2)}</span>
            </p>
            <p className="flex justify-between">
              <span className="text-gray-500">Total calories</span>
              <span className="font-medium">{day.totalCalories}</span>
            </p>
          </div>
          <h3 className="mt-6 mb-4 font-semibold text-gray-900">Week totals</h3>
          <div className="space-y-2 text-sm">
            <p className="flex justify-between">
              <span className="text-gray-500">Weekly spend</span>
              <span className="font-medium">${totalWeeklyCost.toFixed(2)}</span>
            </p>
            <p className="flex justify-between">
              <span className="text-gray-500">Weekly calories</span>
              <span className="font-medium">{totalWeeklyCal.toLocaleString()}</span>
            </p>
          </div>
          <button
            onClick={() => navigate('/shopping-list')}
            className="mt-6 w-full rounded-lg bg-primary py-2.5 text-sm font-medium text-white hover:bg-primary-dark"
          >
            View Shopping List
          </button>
        </aside>
      </div>

      <RecipeDetailModal
        recipe={recipeModal}
        onClose={() => setRecipeModal(null)}
        onAddToShoppingList={() => {}}
      />
      <WeekPreferencesModal
        open={weekPrefsOpen}
        weekLabel="This week"
        onClose={() => setWeekPrefsOpen(false)}
        onSave={() => {}}
      />
    </div>
  );
}
