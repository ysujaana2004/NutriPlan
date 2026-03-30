import { useState } from 'react';
import { Search } from 'lucide-react';
import { MOCK_RECIPES } from '../data/mock';
import { RecipeDetailModal } from '../components/Modals/RecipeDetailModal';

export function Recipes() {
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filtered = MOCK_RECIPES.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.ingredients.some((i) => i.name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Recipes</h1>
      <div className="mb-6 relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          type="search"
          placeholder="Search recipes or ingredients…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-gray-200 bg-white py-2.5 pl-9 pr-3 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((recipe) => (
          <button
            key={recipe.id}
            onClick={() => setSelectedId(recipe.id)}
            className="group rounded-xl border border-gray-200 bg-white text-left shadow-card transition-shadow hover:shadow-cardHover"
          >
            <div className="relative h-40 overflow-hidden rounded-t-xl">
              <img
                src={recipe.image}
                alt=""
                className="h-full w-full object-cover transition-transform group-hover:scale-105"
              />
              <div className="absolute bottom-2 right-2 rounded bg-white/90 px-2 py-0.5 text-xs font-medium text-gray-700">
                ${recipe.cost.toFixed(2)}
              </div>
            </div>
            <div className="p-4">
              <h3 className="font-medium text-gray-900 group-hover:text-primary">{recipe.name}</h3>
              <p className="mt-1 line-clamp-2 text-sm text-gray-500">{recipe.description}</p>
              <p className="mt-2 text-sm text-gray-500">
                {recipe.calories} cal · P {recipe.protein}g C {recipe.carbs}g F {recipe.fats}g
              </p>
            </div>
          </button>
        ))}
      </div>
      {filtered.length === 0 && (
        <p className="py-12 text-center text-gray-500">No recipes match your search.</p>
      )}
      <RecipeDetailModal
        recipeId={selectedId}
        onClose={() => setSelectedId(null)}
        onAddToShoppingList={() => {}}
      />
    </div>
  );
}
