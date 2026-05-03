import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, Flame, ShoppingCart, Plus, Store, CalendarDays, TrendingDown } from 'lucide-react';
import { GeneratePlanModal } from '../components/Modals/GeneratePlanModal';
import type { DayPlan } from '../types';
import type { BackendWeeklyPlan } from '../services/api';

function loadPlan(): BackendWeeklyPlan | null {
  try {
    const raw = sessionStorage.getItem('generatedBackendPlan');
    return raw ? (JSON.parse(raw) as BackendWeeklyPlan) : null;
  } catch {
    return null;
  }
}

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function Dashboard() {
  const navigate = useNavigate();
  const [generateOpen, setGenerateOpen] = useState(false);
  const plan = useMemo(loadPlan, []);

  const handleGenerateDone = (frontendPlan: DayPlan[], backendPlan: BackendWeeklyPlan) => {
    setGenerateOpen(false);
    sessionStorage.setItem('generatedPlan', JSON.stringify(frontendPlan));
    sessionStorage.setItem('generatedBackendPlan', JSON.stringify(backendPlan));
    sessionStorage.setItem('generatedShoppingList', JSON.stringify(backendPlan.shopping_list ?? null));
    navigate('/meal-plans');
  };

  // ── Derived stats from real plan data ──────────────────────────────
  const weeklyBudget = plan?.inputs.budget ?? null;
  const estimatedCost = plan?.week_total_cost_usd ?? null;
  const avgDailyCalories = plan
    ? Math.round(plan.week_totals.calories / plan.days.length)
    : null;
  const remaining = weeklyBudget != null && estimatedCost != null ? weeklyBudget - estimatedCost : null;
  const storeName = plan?.inputs.store_name ?? null;

  // Today's meals
  const today = new Date();
  const todayLabel = DAY_LABELS[today.getDay()];
  const todaysPlan = plan?.days.find((d) => {
    const date = new Date(d.date + 'T00:00:00');
    return date.getDay() === today.getDay();
  }) ?? plan?.days[0] ?? null;

  const hasPlan = plan !== null;

  return (
    <div className="mx-auto max-w-6xl">
      {/* ── Hero banner ─────────────────────────────────────────────── */}
      <section className="mb-8 rounded-2xl bg-gradient-to-br from-primary/10 to-primary-light/20 p-6 sm:p-8">
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
          Welcome to NutriPlan 👋
        </h1>
        <p className="mt-1 text-gray-600">
          {hasPlan
            ? "Your meal plan is ready. Here's your week at a glance."
            : 'Generate a meal plan to get started.'}
        </p>
        {hasPlan && (
          <div className="mt-4 flex flex-wrap gap-2 text-sm">
            {weeklyBudget != null && (
              <span className="rounded-full bg-white/80 px-3 py-1 text-gray-700">
                Budget: ${weeklyBudget}/wk
              </span>
            )}
            {storeName && (
              <span className="rounded-full bg-white/80 px-3 py-1 text-gray-700">
                Store: {storeName}
              </span>
            )}
            <span className="rounded-full bg-white/80 px-3 py-1 text-gray-700">
              {plan!.days.length} days planned
            </span>
          </div>
        )}
      </section>

      {/* ── Stat cards ──────────────────────────────────────────────── */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {/* Weekly spend */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card">
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-orange-50 text-orange-500">
            <DollarSign className="h-5 w-5" />
          </div>
          <p className="text-sm text-gray-500">Weekly Spend</p>
          <p className="text-2xl font-bold text-gray-900">
            {estimatedCost != null ? `$${estimatedCost.toFixed(2)}` : '—'}
          </p>
          <p className="text-xs text-gray-400">
            {weeklyBudget != null ? `of $${weeklyBudget.toFixed(0)} budget` : 'Generate a plan to see'}
          </p>
        </div>

        {/* Avg daily calories */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card">
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-500">
            <Flame className="h-5 w-5" />
          </div>
          <p className="text-sm text-gray-500">Calories / Day</p>
          <p className="text-2xl font-bold text-gray-900">
            {avgDailyCalories != null ? avgDailyCalories.toLocaleString() : '—'}
          </p>
          <p className="text-xs text-gray-400">avg across the week</p>
        </div>

        {/* Remaining budget */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card">
          <div className={`mb-2 flex h-10 w-10 items-center justify-center rounded-lg ${remaining != null && remaining < 0 ? 'bg-red-50 text-red-500' : 'bg-green-50 text-green-500'}`}>
            <TrendingDown className="h-5 w-5" />
          </div>
          <p className="text-sm text-gray-500">Budget Remaining</p>
          <p className={`text-2xl font-bold ${remaining != null && remaining < 0 ? 'text-red-600' : 'text-gray-900'}`}>
            {remaining != null
              ? `${remaining >= 0 ? '+' : '-'}$${Math.abs(remaining).toFixed(2)}`
              : '—'}
          </p>
          <p className="text-xs text-gray-400">
            {remaining != null ? (remaining >= 0 ? 'under budget' : 'over budget') : 'Generate a plan to see'}
          </p>
        </div>
      </div>

      <div className="mb-8 grid gap-6 lg:grid-cols-2">
        {/* ── Today's meals ─────────────────────────────────────────── */}
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <CalendarDays className="h-4 w-4 text-indigo-500" />
              {todaysPlan ? `${todayLabel}'s Meals` : "Today's Meals"}
            </h2>
            {hasPlan && (
              <button
                onClick={() => navigate('/meal-plans')}
                className="text-xs font-medium text-primary hover:underline"
              >
                View full plan →
              </button>
            )}
          </div>
          {todaysPlan ? (
            <div className="space-y-3">
              {todaysPlan.meals.map((meal) => (
                <div
                  key={meal.recipe_id}
                  className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5"
                >
                  <div>
                    <p className="text-xs font-medium uppercase text-gray-400 mb-0.5">
                      {meal.meal_type}
                    </p>
                    <p className="text-sm font-medium text-gray-900 line-clamp-1">{meal.name}</p>
                  </div>
                  <div className="text-right shrink-0 ml-3">
                    <p className="text-sm font-semibold text-indigo-600">
                      {meal.nutrition.calories} cal
                    </p>
                    <p className="text-xs text-gray-400">${meal.estimated_cost_usd.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <CalendarDays className="mb-2 h-8 w-8 text-gray-200" />
              <p className="text-sm text-gray-500">No meal plan yet.</p>
              <p className="text-xs text-gray-400">Generate one below to get started.</p>
            </div>
          )}
        </div>

        {/* ── Shopping snapshot ─────────────────────────────────────── */}
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <ShoppingCart className="h-4 w-4 text-green-500" />
              Shopping Snapshot
            </h2>
            {hasPlan && (
              <button
                onClick={() => navigate('/shopping-list')}
                className="text-xs font-medium text-primary hover:underline"
              >
                Full list →
              </button>
            )}
          </div>
          {plan?.shopping_list ? (
            <>
              <div className="mb-4 flex items-center justify-between rounded-lg bg-green-50 px-4 py-3">
                <span className="text-sm font-medium text-green-800">Estimated total</span>
                <span className="text-lg font-bold text-green-700">
                  ${plan.shopping_list.total_estimated_cost_usd.toFixed(2)}
                </span>
              </div>
              {storeName && (
                <div className="mb-3 flex items-center gap-1.5 text-xs text-gray-400">
                  <Store className="h-3.5 w-3.5" />
                  Priced at {storeName}
                </div>
              )}
              <div className="space-y-2">
                {plan.shopping_list.items.slice(0, 5).map((item) => (
                  <div key={item.canonical_id} className="flex justify-between text-sm">
                    <span className="text-gray-700 truncate">{item.canonical_name}</span>
                    <span className="ml-3 shrink-0 font-medium text-gray-900">
                      ${item.estimated_total_cost_usd.toFixed(2)}
                    </span>
                  </div>
                ))}
                {plan.shopping_list.items.length > 5 && (
                  <p className="text-xs text-gray-400 pt-1">
                    + {plan.shopping_list.items.length - 5} more items
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <ShoppingCart className="mb-2 h-8 w-8 text-gray-200" />
              <p className="text-sm text-gray-500">No shopping list yet.</p>
              <p className="text-xs text-gray-400">It'll appear here after you generate a plan.</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Generate CTA ─────────────────────────────────────────────── */}
      <div className="flex justify-center">
        <button
          onClick={() => setGenerateOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-primary px-6 py-3 font-medium text-white shadow-card hover:bg-primary-dark"
        >
          <Plus className="h-5 w-5" />
          {hasPlan ? 'Regenerate Plan' : 'Generate New Plan'}
        </button>
      </div>

      <GeneratePlanModal
        open={generateOpen}
        onClose={() => setGenerateOpen(false)}
        onDone={handleGenerateDone}
      />
    </div>
  );
}
