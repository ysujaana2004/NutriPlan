import { useMemo } from 'react';
import { DollarSign, TrendingDown, ShoppingCart, Store } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import type { BackendWeeklyPlan } from '../services/api';

function loadPlan(): BackendWeeklyPlan | null {
  try {
    const raw = sessionStorage.getItem('generatedBackendPlan');
    return raw ? (JSON.parse(raw) as BackendWeeklyPlan) : null;
  } catch {
    return null;
  }
}

const DAY_ABBR = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const CATEGORY_COLORS = [
  '#6366f1', '#22c55e', '#f59e0b', '#ec4899',
  '#14b8a6', '#f97316', '#8b5cf6', '#0ea5e9',
];

export function Budget() {
  const plan = useMemo(loadPlan, []);

  // ── No plan yet ──────────────────────────────────────────────────────
  if (!plan) {
    return (
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Budget</h1>
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
          <DollarSign className="mx-auto mb-3 h-10 w-10 text-gray-300" />
          <p className="font-medium text-gray-700">No meal plan generated yet.</p>
          <p className="mt-1 text-sm text-gray-500">
            Generate a meal plan first, then come back here to see your budget breakdown.
          </p>
        </div>
      </div>
    );
  }

  // ── Derived values ────────────────────────────────────────────────────
  const weeklyBudget = plan.inputs.budget ?? 0;
  const estimatedCost = plan.week_total_cost_usd ?? 0;
  const remaining = weeklyBudget - estimatedCost;
  const usedPct = weeklyBudget > 0 ? Math.min((estimatedCost / weeklyBudget) * 100, 100) : 0;
  const storeName = plan.inputs.store_name ?? 'Selected Store';

  // Daily cost bar chart
  const dailyCostData = plan.days.map((d) => {
    const date = new Date(d.date + 'T00:00:00');
    return {
      name: DAY_ABBR[date.getDay()],
      cost: parseFloat(d.total_cost_usd.toFixed(2)),
    };
  });

  // Category breakdown from shopping list
  const categoryMap: Record<string, number> = {};
  for (const item of plan.shopping_list?.items ?? []) {
    const cat = item.category || 'Other';
    categoryMap[cat] = (categoryMap[cat] ?? 0) + item.estimated_total_cost_usd;
  }
  const categoryData = Object.entries(categoryMap)
    .map(([name, value]) => ({ name, value: parseFloat(value.toFixed(2)) }))
    .sort((a, b) => b.value - a.value);

  // Per-meal-type breakdown
  const mealTypeCost: Record<string, number> = { breakfast: 0, lunch: 0, dinner: 0 };
  for (const day of plan.days) {
    for (const meal of day.meals) {
      mealTypeCost[meal.meal_type] = (mealTypeCost[meal.meal_type] ?? 0) + meal.estimated_cost_usd;
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Budget</h1>

      {/* ── Top stat cards ───────────────────────────────────────────── */}
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex items-center gap-2 text-gray-500">
            <DollarSign className="h-4 w-4" />
            <span className="text-sm font-medium">Weekly budget</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-gray-900">${weeklyBudget.toFixed(2)}</p>
          <p className="text-xs text-gray-400">Set in preferences</p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex items-center gap-2 text-gray-500">
            <ShoppingCart className="h-4 w-4" />
            <span className="text-sm font-medium">Estimated cost</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-gray-900">${estimatedCost.toFixed(2)}</p>
          <div className="flex items-center gap-1.5 mt-1">
            <Store className="h-3 w-3 text-gray-400" />
            <p className="text-xs text-gray-400">{storeName} prices</p>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex items-center gap-2 text-gray-500">
            <TrendingDown className="h-4 w-4" />
            <span className="text-sm font-medium">Remaining</span>
          </div>
          <p className={`mt-1 text-2xl font-bold ${remaining >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {remaining >= 0 ? '+' : '-'}${Math.abs(remaining).toFixed(2)}
          </p>
          <p className="text-xs text-gray-400">{remaining >= 0 ? 'under budget' : 'over budget'}</p>
        </div>
      </div>

      {/* ── Budget progress bar ───────────────────────────────────────── */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">Budget used</h3>
          <span className={`text-sm font-semibold ${usedPct >= 100 ? 'text-red-600' : 'text-gray-600'}`}>
            {usedPct.toFixed(1)}%
          </span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-gray-100">
          <div
            className={`h-full rounded-full transition-all ${usedPct >= 100 ? 'bg-red-500' : usedPct >= 85 ? 'bg-amber-400' : 'bg-green-500'}`}
            style={{ width: `${usedPct}%` }}
          />
        </div>
        <div className="mt-2 flex justify-between text-xs text-gray-400">
          <span>$0</span>
          <span>${weeklyBudget.toFixed(2)}</span>
        </div>
      </div>

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        {/* ── Daily cost chart ────────────────────────────────────────── */}
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="mb-4 font-semibold text-gray-900">Estimated cost per day</h3>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyCostData} barSize={28}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${v}`} width={42} />
                <Tooltip formatter={(v) => [`$${typeof v === 'number' ? v.toFixed(2) : '0.00'}`, 'Est. cost']} />
                <Bar dataKey="cost" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ── Meal type breakdown ──────────────────────────────────────── */}
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="mb-4 font-semibold text-gray-900">Cost by meal type</h3>
          <div className="space-y-3">
            {(['breakfast', 'lunch', 'dinner'] as const).map((type) => {
              const cost = mealTypeCost[type] ?? 0;
              const pct = estimatedCost > 0 ? (cost / estimatedCost) * 100 : 0;
              const colors: Record<string, string> = {
                breakfast: 'bg-amber-400',
                lunch: 'bg-indigo-500',
                dinner: 'bg-green-500',
              };
              return (
                <div key={type}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="capitalize text-gray-700">{type}</span>
                    <span className="font-medium text-gray-900">${cost.toFixed(2)}</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                    <div
                      className={`h-full rounded-full ${colors[type]}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6">
            <h3 className="mb-3 font-semibold text-gray-900">Avg cost per day</h3>
            <p className="text-3xl font-bold text-indigo-600">
              ${plan.days.length > 0 ? (estimatedCost / plan.days.length).toFixed(2) : '—'}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">across {plan.days.length} days</p>
          </div>
        </div>
      </div>

      {/* ── Category breakdown pie + table ───────────────────────────── */}
      {categoryData.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="mb-4 font-semibold text-gray-900">Spending by ingredient category</h3>
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center">
            <div className="h-56 w-full lg:w-80 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    innerRadius={45}
                  >
                    {categoryData.map((_, i) => (
                      <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => [`$${typeof v === 'number' ? v.toFixed(2) : '0.00'}`, 'Cost']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="pb-2 text-left font-medium text-gray-500">Category</th>
                    <th className="pb-2 text-right font-medium text-gray-500">Cost</th>
                    <th className="pb-2 text-right font-medium text-gray-500">% of total</th>
                  </tr>
                </thead>
                <tbody>
                  {categoryData.map((row, i) => (
                    <tr key={row.name} className="border-b border-gray-50">
                      <td className="py-2 flex items-center gap-2">
                        <span
                          className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                          style={{ backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }}
                        />
                        <span className="text-gray-800">{row.name || 'Other'}</span>
                      </td>
                      <td className="py-2 text-right font-medium text-gray-900">
                        ${row.value.toFixed(2)}
                      </td>
                      <td className="py-2 text-right text-gray-500">
                        {estimatedCost > 0 ? ((row.value / estimatedCost) * 100).toFixed(1) : '0'}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
