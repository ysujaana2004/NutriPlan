import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, Flame, Award, Plus } from 'lucide-react';
import { USER_NAME } from '../data/mock';
import { GeneratePlanModal } from '../components/Modals/GeneratePlanModal';
import type { DayPlan } from '../types';
import type { BackendWeeklyPlan } from '../services/api';

const stats = [
  { label: 'Weekly Spend', value: '$72', sub: 'of $100 budget', icon: DollarSign, color: 'text-accent-orange' },
  { label: 'Calories / Day', value: '1,240', sub: 'avg', icon: Flame, color: 'text-primary' },
  { label: 'Avg Nutrition Score', value: '88', sub: 'out of 100', icon: Award, color: 'text-accent-yellow' },
];

export function Dashboard() {
  const navigate = useNavigate();
  const [generateOpen, setGenerateOpen] = useState(false);

  const handleGenerateDone = (plan: DayPlan[], backendPlan: BackendWeeklyPlan) => {
    setGenerateOpen(false);
    // Store generated plan data so other pages can use the same backend payload.
    sessionStorage.setItem('generatedPlan', JSON.stringify(plan));
    sessionStorage.setItem('generatedShoppingList', JSON.stringify(backendPlan.shopping_list ?? null));
    navigate('/meal-plans');
  };

  return (
    <div className="mx-auto max-w-6xl">
      <section className="mb-8 rounded-2xl bg-gradient-to-br from-primary/10 to-primary-light/20 p-6 sm:p-8">
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
          Welcome back, {USER_NAME} 👋
        </h1>
        <p className="mt-1 text-gray-600">Your healthy week starts here.</p>
        <div className="mt-4 flex flex-wrap gap-2 text-sm">
          <span className="rounded-full bg-white/80 px-3 py-1 text-gray-700">Budget: $100/wk</span>
          <span className="rounded-full bg-white/80 px-3 py-1 text-gray-700">Goal: Balanced</span>
          <span className="rounded-full bg-white/80 px-3 py-1 text-gray-700">Location: On</span>
        </div>
      </section>

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {stats.map(({ label, value, sub, icon: Icon, color }) => (
          <div
            key={label}
            className="rounded-xl border border-gray-200 bg-white p-5 shadow-card transition-shadow hover:shadow-cardHover"
          >
            <div className={`mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 ${color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <p className="text-sm text-gray-500">{label}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-400">{sub}</p>
          </div>
        ))}
      </div>

      <div className="flex justify-center">
        <button
          onClick={() => setGenerateOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-primary px-6 py-3 font-medium text-white shadow-card hover:bg-primary-dark"
        >
          <Plus className="h-5 w-5" />
          Generate New Plan
        </button>
      </div>

      <GeneratePlanModal open={generateOpen} onClose={() => setGenerateOpen(false)} onDone={handleGenerateDone} />
    </div>
  );
}
