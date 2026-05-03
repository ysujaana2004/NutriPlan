import { useState } from 'react';
import { X } from 'lucide-react';
import { fetchMealPlan, type BackendWeeklyPlan } from '../../services/api';
import { transformBackendPlanToFrontend } from '../../utils/transform';
import type { DayPlan } from '../../types';

interface GeneratePlanModalProps {
  open: boolean;
  onClose: () => void;
  onDone: (frontendPlan: DayPlan[], backendPlan: BackendWeeklyPlan) => void;
}
/*
// Map frontend goal values to backend diet values
function mapGoalToDiet(goal: string): 'none' | 'vegetarian' | 'high_protein' | 'low_carb' {
  switch (goal) {
    case 'muscle':
      return 'high_protein';
    case 'low-carb':
      return 'low_carb';
    case 'weight-loss':
      return 'low_carb'; // Weight loss often aligns with low carb
    default:
      return 'none';
  }
}
*/
export function GeneratePlanModal({ open, onClose, onDone }: GeneratePlanModalProps) {
  const [budget, setBudget] = useState('100');
  const [calories, setCalories] = useState('2000');
  const [goal, setGoal] = useState('balanced');
  const [location, setLocation] = useState('');
  const [storePreference, setStorePreference] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setError(null);
    setLoading(true);

    try {
      const budgetNum = parseFloat(budget);
      const caloriesNum = parseInt(calories, 10);

      if (isNaN(budgetNum) || budgetNum <= 0) {
        setError('Please enter a valid budget greater than 0');
        setLoading(false);
        return;
      }

      if (isNaN(caloriesNum) || caloriesNum <= 0) {
        setError('Please enter a valid calorie target greater than 0');
        setLoading(false);
        return;
      }

      const backendPlan = await fetchMealPlan({
        budget: budgetNum,
        calories: caloriesNum,
        //diet: mapGoalToDiet(goal),
        store_preference: storePreference || undefined,
        zip_code: location || undefined,
        random_seed: Math.floor(Math.random() * 1000000),
      });

      const frontendPlan = transformBackendPlanToFrontend(backendPlan);
      onDone(frontendPlan, backendPlan);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate meal plan');
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Generate New Plan</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Weekly budget ($)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Daily calories</label>
            <input
              type="number"
              value={calories}
              onChange={(e) => setCalories(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          {/*
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Health goal</label>
            <select
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="balanced">Balanced</option>
              <option value="weight-loss">Weight loss</option>
              <option value="muscle">Muscle gain</option>
              <option value="low-carb">Low carb</option>
            </select>
          </div>
          */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Store Preference</label>
            <select
              value={storePreference}
              onChange={(e) => setStorePreference(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-700 bg-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="">Auto (Find closest to zip code)</option>
              <option value="Target">Target</option>
              <option value="Walmart">Walmart</option>
              <option value="BJs">BJ's Wholesale</option>
              <option value="Whole Foods">Whole Foods</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Location (Address or Zip)</label>
            <input
              type="text"
              placeholder="e.g. 123 Main St, NY or 10001"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>
        <div className="mt-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-200 py-2.5 font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex-1 rounded-lg bg-primary py-2.5 font-medium text-white hover:bg-primary-dark disabled:opacity-70"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Generating…
              </span>
            ) : (
              'Generate'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
