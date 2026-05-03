import { useState } from 'react';
import { X } from 'lucide-react';

interface WeekPreferencesModalProps {
  open: boolean;
  weekLabel: string;
  onClose: () => void;
  onSave: (prefs: { budget?: number; goal?: string; dietary?: string[]; storePreference?: string; zipCode?: string }) => void;
}

const DIET_OPTIONS = ['Vegan', 'Halal', 'Gluten-free', 'Low-carb'];
const GOALS = ['Balanced', 'Weight loss', 'Muscle gain', 'Low carb'];
const STORES = ['Target', 'Walmart', 'BJs', 'Whole Foods'];

export function WeekPreferencesModal({ open, weekLabel, onClose, onSave }: WeekPreferencesModalProps) {
  const [budget, setBudget] = useState('100');
  const [goal, setGoal] = useState('Balanced');
  const [dietary, setDietary] = useState<string[]>([]);
  const [storePreference, setStorePreference] = useState('');
  const [zipCode, setZipCode] = useState('');

  const toggleDiet = (d: string) => {
    setDietary((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]));
  };

  const handleSave = () => {
    onSave({
      budget: Number(budget) || undefined,
      goal: goal || undefined,
      dietary: dietary.length ? dietary : undefined,
      storePreference: storePreference,
      zipCode: zipCode || undefined,
    });
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">Preferences for {weekLabel}</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="mb-4 text-sm text-gray-500">
          Override your default preferences for this week only.
        </p>
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
            <label className="mb-1 block text-sm font-medium text-gray-700">Health goal</label>
            <select
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {GOALS.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Store Preference</label>
            <select
              value={storePreference}
              onChange={(e) => setStorePreference(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-gray-700 bg-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="">Auto (Find closest to zip code)</option>
              {STORES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Location (Address or Zip)</label>
            <input
              type="text"
              placeholder="e.g. 123 Main St, NY or 10001"
              value={zipCode}
              onChange={(e) => setZipCode(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">Dietary (optional)</label>
            <div className="flex flex-wrap gap-2">
              {DIET_OPTIONS.map((d) => (
                <button
                  key={d}
                  onClick={() => toggleDiet(d)}
                  type="button"
                  className={`rounded-full px-3 py-1.5 text-sm ${
                    dietary.includes(d) ? 'bg-primary text-white' : 'border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="mt-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-200 py-2.5 font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex-1 rounded-lg bg-primary py-2.5 font-medium text-white hover:bg-primary-dark"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
