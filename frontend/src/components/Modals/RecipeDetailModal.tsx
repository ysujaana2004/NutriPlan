import { ShoppingCart } from 'lucide-react';
import { useState } from 'react';
import { MOCK_RECIPES } from '../../data/mock';
import type { Recipe } from '../../types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Legend,
} from 'recharts';

interface RecipeDetailModalProps {
  recipeId?: string | null;
  recipe?: Recipe | null;
  onClose: () => void;
  onAddToShoppingList: () => void;
}

const PIE_COLORS = ['#4CAF50', '#81C784', '#A3E4A6', '#FFB74D'];

/**
 * Resolves recipe details from direct recipe data or falls back to mock lookup by id.
 */
function resolveRecipe(recipe: Recipe | null | undefined, recipeId: string | null | undefined): Recipe | null {
  if (recipe) {
    return recipe;
  }
  if (!recipeId) {
    return null;
  }
  return MOCK_RECIPES.find((candidate) => candidate.id === recipeId) ?? null;
}

export function RecipeDetailModal({ recipeId = null, recipe = null, onClose, onAddToShoppingList }: RecipeDetailModalProps) {
  const [tab, setTab] = useState<'ingredients' | 'instructions' | 'nutrition'>('ingredients');
  const selectedRecipe = resolveRecipe(recipe, recipeId);

  if (!selectedRecipe) return null;

  const nutritionData = [
    { name: 'Protein', value: selectedRecipe.protein, fill: PIE_COLORS[0] },
    { name: 'Carbs', value: selectedRecipe.carbs, fill: PIE_COLORS[1] },
    { name: 'Fats', value: selectedRecipe.fats, fill: PIE_COLORS[2] },
  ];
  const barData = [
    { name: 'Protein', g: selectedRecipe.protein },
    { name: 'Carbs', g: selectedRecipe.carbs },
    { name: 'Fats', g: selectedRecipe.fats },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-xl">
        <div className="max-h-[90vh] overflow-y-auto">
          <div className="relative h-48 sm:h-56">
            <img
              src={selectedRecipe.image}
              alt=""
              className="h-full w-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
            <div className="absolute bottom-4 left-4 right-4 text-white">
              <h2 className="text-xl font-bold">{selectedRecipe.name}</h2>
              <p className="text-sm opacity-90">{selectedRecipe.description}</p>
            </div>
          </div>
          <div className="p-4">
            <div className="mb-4 flex flex-wrap gap-3 text-sm">
              <span className="rounded-full bg-primary-light/30 px-3 py-1 text-primary">
                {selectedRecipe.calories} cal
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1 text-gray-700">
                P: {selectedRecipe.protein}g
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1 text-gray-700">
                C: {selectedRecipe.carbs}g
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1 text-gray-700">
                F: {selectedRecipe.fats}g
              </span>
              <span className="rounded-full bg-accent-orange/20 px-3 py-1 text-amber-800">
                ${selectedRecipe.cost.toFixed(2)}
              </span>
            </div>
            <div className="mb-4 flex gap-2 border-b border-gray-200">
              <button
                onClick={() => setTab('ingredients')}
                className={`border-b-2 px-3 py-2 text-sm font-medium ${
                  tab === 'ingredients'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500'
                }`}
              >
                Ingredients
              </button>
              <button
                onClick={() => setTab('instructions')}
                className={`border-b-2 px-3 py-2 text-sm font-medium ${
                  tab === 'instructions'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500'
                }`}
              >
                Instructions
              </button>
              <button
                onClick={() => setTab('nutrition')}
                className={`border-b-2 px-3 py-2 text-sm font-medium ${
                  tab === 'nutrition'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500'
                }`}
              >
                Nutrition
              </button>
            </div>
            {tab === 'ingredients' && (
              <ul className="mb-4 space-y-2">
                {selectedRecipe.ingredients.length === 0 && (
                  <li className="text-sm text-gray-500">Ingredients are not available for this recipe yet.</li>
                )}
                {selectedRecipe.ingredients.map((ing) => (
                  <li key={ing.id} className="flex justify-between text-sm">
                    <span>{ing.name} - {ing.amount}</span>
                    {ing.price > 0 ? <span className="text-accent-orange">${ing.price.toFixed(2)}</span> : null}
                  </li>
                ))}
              </ul>
            )}
            {tab === 'instructions' && (
              <ol className="mb-4 list-decimal space-y-2 pl-5 text-sm text-gray-700">
                {(selectedRecipe.instructions ?? []).length === 0 && (
                  <li className="list-none pl-0 text-gray-500">Instructions are not available for this recipe yet.</li>
                )}
                {(selectedRecipe.instructions ?? []).map((step, index) => (
                  <li key={`${selectedRecipe.id}-step-${index}`}>{step}</li>
                ))}
              </ol>
            )}
            {tab === 'nutrition' && (
              <div className="mb-4">
                <div className="mb-4 h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={barData} layout="vertical" margin={{ left: 0, right: 20 }}>
                      <XAxis type="number" />
                      <YAxis dataKey="name" type="category" width={60} />
                      <Tooltip />
                      <Bar dataKey="g" fill="#4CAF50" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="h-40">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={nutritionData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={60}
                        label
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
            <div className="flex gap-3">
              <button
                onClick={onAddToShoppingList}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary py-2.5 font-medium text-white hover:bg-primary-dark"
              >
                <ShoppingCart className="h-4 w-4" />
                Add to Shopping List
              </button>
              <button
                onClick={onClose}
                className="rounded-lg border border-gray-200 px-4 py-2.5 font-medium text-gray-700 hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
