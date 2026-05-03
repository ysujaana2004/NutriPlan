import { useMemo, useState } from 'react';
import { AlertTriangle, DollarSign, LayoutGrid, ShoppingCart, MapPin } from 'lucide-react';
import type { BackendWeeklyPlan, BackendShoppingListItem } from '../services/api';

type SortBy = 'line_total' | 'unit_price';
type GroupBy = 'category' | 'product';

/**
 * Reads the last generated backend shopping list from session storage.
 */
function loadGeneratedBackendPlan(): BackendWeeklyPlan | null {
  try {
    const raw = sessionStorage.getItem('generatedBackendPlan');
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (error) {
    console.error('Failed to parse generated backend plan:', error);
    return null;
  }
}

/**
 * Returns a sorted copy of shopping items according to the selected strategy.
 */
function sortShoppingItems(items: BackendShoppingListItem[], sortBy: SortBy): BackendShoppingListItem[] {
  const copy = [...items];
  if (sortBy === 'unit_price') {
    copy.sort((a, b) => a.unit_price_usd - b.unit_price_usd);
  } else {
    copy.sort((a, b) => a.estimated_total_cost_usd - b.estimated_total_cost_usd);
  }
  return copy;
}

/**
 * Groups shopping items by category or by product name for display.
 */
function groupShoppingItems(items: BackendShoppingListItem[], groupBy: GroupBy): Map<string, BackendShoppingListItem[]> {
  const groups = new Map<string, BackendShoppingListItem[]>();
  for (const item of items) {
    const key = groupBy === 'category' ? item.category || 'Uncategorized' : item.product_name;
    const existing = groups.get(key) ?? [];
    existing.push(item);
    groups.set(key, existing);
  }
  return groups;
}

export function ShoppingList() {
  const [sortBy, setSortBy] = useState<SortBy>('line_total');
  const [groupBy, setGroupBy] = useState<GroupBy>('category');
  const backendPlan = useMemo(loadGeneratedBackendPlan, []);
  const generated = backendPlan?.shopping_list ?? null;
  const storeName = backendPlan?.inputs?.store_name ?? 'Target';
  const storeLocations = backendPlan?.inputs?.store_locations || [];

  const groupedItems = useMemo(() => {
    if (!generated) {
      return new Map<string, BackendShoppingListItem[]>();
    }
    const sorted = sortShoppingItems(generated.items ?? [], sortBy);
    return groupShoppingItems(sorted, groupBy);
  }, [generated, sortBy, groupBy]);

  if (!generated) {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Shopping List</h1>
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <p className="text-gray-700">No generated shopping list found yet.</p>
          <p className="mt-2 text-sm text-gray-500">
            Generate a meal plan first, then come back here to see your store-matched items.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Shopping List</h1>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-4 py-1.5 text-sm font-semibold text-primary">
          <MapPin className="h-4 w-4" />
          {storeName} prices
        </span>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <span className="text-sm font-medium text-gray-700">Sort by:</span>
        <div className="flex rounded-lg border border-gray-200 bg-white p-0.5">
          <button
            onClick={() => setSortBy('line_total')}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium ${
              sortBy === 'line_total' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <ShoppingCart className="h-4 w-4" />
            Total cost
          </button>
          <button
            onClick={() => setSortBy('unit_price')}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium ${
              sortBy === 'unit_price' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <DollarSign className="h-4 w-4" />
            Unit price
          </button>
        </div>
        <span className="text-sm font-medium text-gray-700">Group by:</span>
        <div className="flex rounded-lg border border-gray-200 bg-white p-0.5">
          <button
            onClick={() => setGroupBy('category')}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium ${
              groupBy === 'category' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <LayoutGrid className="h-4 w-4" />
            Category
          </button>
          <button
            onClick={() => setGroupBy('product')}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium ${
              groupBy === 'product' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <ShoppingCart className="h-4 w-4" />
            Product
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-6 rounded-xl border border-gray-200 bg-white p-4">
          {Array.from(groupedItems.entries()).map(([groupName, items]) => (
            <div key={groupName}>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
                {groupName}
              </h3>
              <ul className="space-y-2">
                {items.map((item) => (
                  <li
                    key={`${item.canonical_id}-${item.product_name}`}
                    className="rounded-lg border border-gray-100 bg-gray-50/50 p-3"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="font-medium text-gray-900">{item.canonical_name}</p>
                        <p className="text-sm text-gray-500">{item.product_name}</p>
                        <p className="text-xs text-gray-500">
                          Used by {item.recipes.length} recipe(s): {item.recipes.join(', ')}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-primary">${item.estimated_total_cost_usd.toFixed(2)}</p>
                        <p className="text-xs text-gray-500">
                          {item.estimated_units} unit(s) at ${item.unit_price_usd.toFixed(2)} each
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <aside className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
          <div>
            <h3 className="font-semibold text-gray-900">Estimated total</h3>
            <p className="mt-1 text-2xl font-bold text-primary">
              ${generated.total_estimated_cost_usd.toFixed(2)}
            </p>
            <p className="text-sm text-gray-500">{generated.items.length} matched item(s)</p>
          </div>

          <div>
            <h3 className="mb-2 flex items-center gap-2 font-semibold text-gray-900">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              Missing {storeName} Matches
            </h3>
            {generated.missing_items.length === 0 ? (
              <p className="text-sm text-gray-500">None. Every canonical ingredient has a matched product.</p>
            ) : (
              <ul className="space-y-2">
                {generated.missing_items.map((item) => (
                  <li key={item.canonical_id} className="rounded-md border border-amber-200 bg-amber-50 p-2 text-sm">
                    <p className="font-medium text-amber-800">{item.canonical_name}</p>
                    <p className="text-amber-700">Used by {item.recipes.join(', ')}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {storeLocations.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <h3 className="mb-2 flex items-center gap-2 font-semibold text-gray-900">
                <MapPin className="h-4 w-4 text-primary" />
                Selected Stores Location
              </h3>
              <div className="flex flex-col gap-3">
                {storeLocations.slice(0, 3).map((loc, idx) => (
                  <div key={idx} className="rounded-md bg-gray-50 p-3 text-sm">
                    <p className="font-medium text-gray-900">{loc.name}</p>
                    <p className="text-gray-600 mt-0.5">{loc.address}</p>
                    {loc.distance_miles !== undefined && (
                      <p className="text-gray-400 mt-1">{loc.distance_miles} miles away</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
