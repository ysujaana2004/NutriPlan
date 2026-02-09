import { useState } from 'react';
import { Moon, Sun } from 'lucide-react';

const DIET_OPTIONS = ['Vegan', 'Halal', 'Gluten-free', 'Low-carb'] as const;

export function Settings() {
  const [name, setName] = useState('Alex');
  const [email, setEmail] = useState('alex@example.com');
  const [goal, setGoal] = useState('Balanced');
  const [budget, setBudget] = useState('100');
  const [location, setLocation] = useState('San Francisco, CA');
  const [livePricing, setLivePricing] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [diet, setDiet] = useState<string[]>([]);

  const toggleDiet = (d: string) => {
    setDiet((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]));
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Settings</h1>

      <section className="mb-8 rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Profile</h2>
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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
              <option>Balanced</option>
              <option>Weight loss</option>
              <option>Muscle gain</option>
              <option>Low carb</option>
            </select>
          </div>
        </div>
      </section>

      <section className="mb-8 rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Dietary preferences</h2>
        <div className="flex flex-wrap gap-2">
          {DIET_OPTIONS.map((d) => (
            <button
              key={d}
              onClick={() => toggleDiet(d)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                diet.includes(d)
                  ? 'bg-primary text-white'
                  : 'border border-gray-200 bg-white text-gray-700 hover:border-primary hover:bg-primary-light/20'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </section>

      <section className="mb-8 rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Budget & location</h2>
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
            <label className="mb-1 block text-sm font-medium text-gray-700">Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="City or ZIP"
              className="w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>
      </section>

      <section className="mb-8 rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Preferences</h2>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-700">Enable live grocery pricing</span>
          <button
            onClick={() => setLivePricing(!livePricing)}
            className={`relative h-6 w-11 rounded-full transition-colors ${
              livePricing ? 'bg-primary' : 'bg-gray-200'
            }`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                livePricing ? 'left-6' : 'left-0.5'
              }`}
            />
          </button>
        </div>
      </section>

      <section className="mb-8 rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Theme</h2>
        <div className="flex gap-3">
          <button
            onClick={() => setDarkMode(false)}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg border-2 py-3 ${
              !darkMode ? 'border-primary bg-primary-light/20 text-primary' : 'border-gray-200 text-gray-600'
            }`}
          >
            <Sun className="h-5 w-5" />
            Light
          </button>
          <button
            onClick={() => setDarkMode(true)}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg border-2 py-3 ${
              darkMode ? 'border-primary bg-primary-light/20 text-primary' : 'border-gray-200 text-gray-600'
            }`}
          >
            <Moon className="h-5 w-5" />
            Dark
          </button>
        </div>
      </section>

      <p className="text-sm text-gray-500">
        To change preferences for a specific week, go to Meal Plans → select the week → use “Week preferences” there.
      </p>
    </div>
  );
}
