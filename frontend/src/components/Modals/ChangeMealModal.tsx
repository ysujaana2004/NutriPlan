import { X } from 'lucide-react';
import { MOCK_RECIPES } from '../../data/mock';
import type { MealSlot } from '../../types';

interface ChangeMealModalProps {
  open: boolean;
  slot: MealSlot | null;
  onClose: () => void;
  onSelect: (recipeId: string) => void;
}

export function ChangeMealModal({ open, slot, onClose, onSelect }: ChangeMealModalProps) {
  if (!open || !slot) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative max-h-[85vh] w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-lg font-bold text-gray-900">Change meal – {slot.type}</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto p-4">
          <div className="grid gap-3 sm:grid-cols-2">
            {MOCK_RECIPES.filter((r) => r.id !== slot.recipe.id).map((recipe) => (
              <button
                key={recipe.id}
                onClick={() => onSelect(recipe.id)}
                className="flex gap-3 rounded-xl border border-gray-200 p-3 text-left transition-colors hover:border-primary hover:bg-primary-light/10"
              >
                <img
                  src={recipe.image}
                  alt=""
                  className="h-16 w-20 shrink-0 rounded-lg object-cover"
                />
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-gray-900">{recipe.name}</p>
                  <p className="text-sm text-gray-500">
                    {recipe.calories} cal · ${recipe.cost.toFixed(2)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
