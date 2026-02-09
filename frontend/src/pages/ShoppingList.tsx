import { useState, useMemo } from 'react';
import { MapPin, Store, LayoutGrid, DollarSign } from 'lucide-react';
import { MOCK_SHOPPING_ITEMS, MOCK_STORES } from '../data/mock';
import type { ShoppingItem } from '../types';

type SortBy = 'price' | 'distance';
type GroupBy = 'store' | 'category';

// Mock: same item at multiple stores with different prices for comparison
const itemsWithComparison: (ShoppingItem & { prices: { storeName: string; price: number }[] })[] = [
  { ...MOCK_SHOPPING_ITEMS[0], prices: [{ storeName: 'Whole Foods', price: 1.0 }, { storeName: 'Trader Joe\'s', price: 0.89 }] },
  { ...MOCK_SHOPPING_ITEMS[1], prices: [{ storeName: 'Whole Foods', price: 6.5 }, { storeName: 'Trader Joe\'s', price: 5.99 }] },
  { ...MOCK_SHOPPING_ITEMS[2], prices: [{ storeName: 'Whole Foods', price: 11.0 }, { storeName: 'Trader Joe\'s', price: 10.0 }] },
  { ...MOCK_SHOPPING_ITEMS[3], prices: [{ storeName: 'Whole Foods', price: 2.4 }, { storeName: 'Trader Joe\'s', price: 2.19 }] },
  { ...MOCK_SHOPPING_ITEMS[4], prices: [{ storeName: 'Whole Foods', price: 2.6 }, { storeName: 'Trader Joe\'s', price: 2.4 }] },
];

export function ShoppingList() {
  const [sortBy, setSortBy] = useState<SortBy>('price');
  const [groupBy, setGroupBy] = useState<GroupBy>('category');

  const sortedAndGrouped = useMemo(() => {
    let list = [...itemsWithComparison];
    if (sortBy === 'price') {
      list.sort((a, b) => a.price - b.price);
    } else {
      list.sort((a, b) => {
        const storeA = MOCK_STORES.find((s) => s.id === a.storeId);
        const storeB = MOCK_STORES.find((s) => s.id === b.storeId);
        return (storeA?.distance ?? 0) - (storeB?.distance ?? 0);
      });
    }
    if (groupBy === 'store') {
      const byStore = new Map<string, typeof list>();
      list.forEach((item) => {
        const key = item.storeName;
        if (!byStore.has(key)) byStore.set(key, []);
        byStore.get(key)!.push(item);
      });
      return { type: 'store' as const, groups: byStore };
    }
    const byCategory = new Map<string, typeof list>();
    list.forEach((item) => {
      const key = item.category;
      if (!byCategory.has(key)) byCategory.set(key, []);
      byCategory.get(key)!.push(item);
    });
    return { type: 'category' as const, groups: byCategory };
  }, [sortBy, groupBy]);

  const cheapestStore = MOCK_STORES.length
    ? MOCK_STORES.reduce((best, s) => (s.totalPrice < best.totalPrice ? s : best))
    : null;

  return (
    <div className="mx-auto max-w-7xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Shopping List</h1>

      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="flex-1">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
            <div className="flex rounded-lg border border-gray-200 bg-white p-0.5">
              <button
                onClick={() => setSortBy('price')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium ${
                  sortBy === 'price' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <DollarSign className="h-4 w-4" />
                Price
              </button>
              <button
                onClick={() => setSortBy('distance')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium ${
                  sortBy === 'distance' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <MapPin className="h-4 w-4" />
                Distance
              </button>
            </div>
            <span className="text-sm font-medium text-gray-700">Group by:</span>
            <div className="flex rounded-lg border border-gray-200 bg-white p-0.5">
              <button
                onClick={() => setGroupBy('store')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium ${
                  groupBy === 'store' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Store className="h-4 w-4" />
                Store
              </button>
              <button
                onClick={() => setGroupBy('category')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium ${
                  groupBy === 'category' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <LayoutGrid className="h-4 w-4" />
                Category
              </button>
            </div>
          </div>

          <div className="space-y-6 rounded-xl border border-gray-200 bg-white p-4">
            {Array.from(sortedAndGrouped.groups.entries()).map(([groupName, items]) => (
              <div key={groupName}>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
                  {groupName}
                </h3>
                <ul className="space-y-2">
                  {items.map((item) => (
                    <li
                      key={item.id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-gray-100 bg-gray-50/50 p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary-light/30 flex items-center justify-center">
                          <Store className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{item.name}</p>
                          <p className="text-sm text-gray-500">{item.amount}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-medium text-primary">${item.price.toFixed(2)}</p>
                          <p className="text-xs text-gray-500">{item.storeName}</p>
                        </div>
                        {'prices' in item && item.prices && (
                          <div className="hidden rounded border border-gray-200 bg-white px-2 py-1 text-xs sm:block">
                            <p className="font-medium text-gray-500">Price comparison</p>
                            {item.prices.map((p) => (
                              <p key={p.storeName}>
                                {p.storeName}: ${p.price.toFixed(2)}
                              </p>
                            ))}
                          </div>
                        )}
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            item.available ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                          }`}
                        >
                          {item.available ? 'In stock' : 'Check store'}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <aside className="w-full rounded-xl border border-gray-200 bg-white p-5 lg:w-80">
          <h3 className="mb-4 font-semibold text-gray-900">Cheapest store near you</h3>
          {cheapestStore ? (
            <>
              <div className="mb-3 flex items-center gap-3 rounded-lg bg-primary-light/20 p-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-white">
                  <Store className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{cheapestStore.name}</p>
                  <p className="text-sm text-gray-500">{cheapestStore.distance} mi away</p>
                  <p className="text-primary font-semibold">${cheapestStore.totalPrice.toFixed(2)} total</p>
                </div>
              </div>
              <div className="flex h-40 items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-center text-sm text-gray-500">
                Map placeholder – e.g. Google Maps embed with store pins
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-500">No store data available for your location.</p>
          )}
        </aside>
      </div>
    </div>
  );
}
