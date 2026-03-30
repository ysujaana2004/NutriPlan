import { useMemo } from 'react';
import { DollarSign, TrendingDown } from 'lucide-react';
import { MOCK_BUDGET } from '../data/mock';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const CATEGORY_LABELS: Record<string, string> = {
  groceries: 'Groceries',
  eating_out: 'Eating out',
  other: 'Other',
};

const CATEGORY_COLORS: Record<string, string> = {
  groceries: '#4CAF50',
  eating_out: '#FFB74D',
  other: '#9E9E9E',
};

export function Budget() {
  const byWeek = useMemo(() => {
    const map = new Map<string, { label: string; spent: number; budget: number; entries: typeof MOCK_BUDGET }>();
    MOCK_BUDGET.forEach((e) => {
      const existing = map.get(e.weekId);
      if (!existing) {
        map.set(e.weekId, {
          label: e.label,
          spent: e.spent,
          budget: e.budget,
          entries: [e],
        });
      } else {
        existing.spent += e.spent;
        existing.entries.push(e);
      }
    });
    return Array.from(map.values());
  }, []);

  const totalSpent = MOCK_BUDGET.reduce((s, e) => s + e.spent, 0);
  const totalBudget = byWeek.reduce((s, w) => s + w.budget, 0);
  const remaining = totalBudget - totalSpent;

  const chartData = byWeek.map((w) => ({
    name: w.label,
    spent: w.spent,
    budget: w.budget,
    remaining: Math.max(0, w.budget - w.spent),
  }));

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Budget</h1>

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 text-gray-500">
            <DollarSign className="h-5 w-5" />
            <span className="text-sm font-medium">Total spent</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-gray-900">${totalSpent.toFixed(2)}</p>
          <p className="text-xs text-gray-400">Across all weeks</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 text-gray-500">
            <DollarSign className="h-5 w-5" />
            <span className="text-sm font-medium">Total budget</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-gray-900">${totalBudget.toFixed(2)}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 text-gray-500">
            <TrendingDown className="h-5 w-5" />
            <span className="text-sm font-medium">Remaining</span>
          </div>
          <p className={`mt-1 text-2xl font-bold ${remaining >= 0 ? 'text-primary' : 'text-red-600'}`}>
            ${Math.abs(remaining).toFixed(2)} {remaining >= 0 ? 'left' : 'over'}
          </p>
        </div>
      </div>

      <div className="mb-8 rounded-xl border border-gray-200 bg-white p-4">
        <h3 className="mb-4 font-semibold text-gray-900">Spending by week</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="spent" name="Spent" fill="#4CAF50" radius={[4, 4, 0, 0]} />
              <Bar dataKey="remaining" name="Remaining" fill="#E8F5E9" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
        <h3 className="border-b border-gray-200 p-4 font-semibold text-gray-900">
          How much you spent (by category)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left font-medium text-gray-700">Week</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Category</th>
                <th className="px-4 py-3 text-right font-medium text-gray-700">Spent</th>
                <th className="px-4 py-3 text-right font-medium text-gray-700">Budget</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_BUDGET.map((e) => (
                <tr key={e.id} className="border-b border-gray-100">
                  <td className="px-4 py-3 text-gray-900">{e.label}</td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-block rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: `${CATEGORY_COLORS[e.category]}20`,
                        color: CATEGORY_COLORS[e.category],
                      }}
                    >
                      {CATEGORY_LABELS[e.category]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium">${e.spent.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-gray-500">${e.budget.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
