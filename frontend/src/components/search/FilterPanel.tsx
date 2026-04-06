'use client'

interface FilterPanelProps {
  facets: {
    marketplaces: Record<string, number>
    price: { min_price: number; max_price: number; avg_price: number }
  } | null
  filters: {
    marketplace_ids: number[]
    min_price?: number
    max_price?: number
    in_stock: boolean
    sort_by: string
  }
  onFiltersChange: (filters: any) => void
}

const MARKETPLACES = [
  { id: 1, name: 'Яндекс Маркет', key: 'yandex', color: '#ffcc00' },
  { id: 2, name: 'Wildberries', key: 'wildberries', color: '#cb11ab' },
  { id: 3, name: 'Ситилинк', key: 'citilink', color: '#ff6600' },
  { id: 4, name: 'Регард', key: 'regard', color: '#e53935' },
  { id: 5, name: 'AliExpress', key: 'aliexpress', color: '#ff4747' },
  { id: 6, name: 'Onliner', key: 'onliner', color: '#65cb02' },
]

export function FilterPanel({ facets, filters, onFiltersChange }: FilterPanelProps) {
  const toggleMarketplace = (id: number) => {
    const ids = filters.marketplace_ids.includes(id)
      ? filters.marketplace_ids.filter(i => i !== id)
      : [...filters.marketplace_ids, id]
    onFiltersChange({ ...filters, marketplace_ids: ids })
  }

  return (
    <div className="space-y-6">
      {/* Маркетплейсы */}
      <div>
        <h3 className="text-sm font-semibold text-[var(--t)] mb-3">Маркетплейсы</h3>
        <div className="space-y-2">
          {MARKETPLACES.map((mp) => {
            const count = facets?.marketplaces[mp.key] || 0
            const isActive = filters.marketplace_ids.includes(mp.id)
            return (
              <button
                key={mp.id}
                onClick={() => toggleMarketplace(mp.id)}
                className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-all ${
                  isActive
                    ? 'border-[var(--ac)] bg-[rgba(108,92,231,.1)]'
                    : 'border-[var(--bd)] hover:border-[var(--bl)] bg-[var(--ci)]'
                }`}
              >
                <span
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ background: mp.color }}
                />
                <span className={`text-sm font-medium ${isActive ? 'text-[var(--t)]' : 'text-[var(--td)]'}`}>
                  {mp.name}
                </span>
                <span className="ml-auto text-xs text-[var(--tm)]">{count}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Сортировка */}
      <div>
        <h3 className="text-sm font-semibold text-[var(--t)] mb-3">Сортировка</h3>
        <select
          value={filters.sort_by}
          onChange={(e) => onFiltersChange({ ...filters, sort_by: e.target.value })}
          className="w-full p-3 rounded-xl bg-[var(--ci)] border border-[var(--bd)] text-[var(--t)] text-sm"
        >
          <option value="relevance">По релевантности</option>
          <option value="price_asc">Сначала дешёвые</option>
          <option value="price_desc">Сначала дорогие</option>
          <option value="rating">По рейтингу</option>
        </select>
      </div>

      {/* В наличии */}
      <div>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.in_stock}
            onChange={(e) => onFiltersChange({ ...filters, in_stock: e.target.checked })}
            className="w-5 h-5 rounded border-[var(--bd)] bg-[var(--ci)] accent-[var(--ac)]"
          />
          <span className="text-sm text-[var(--td)]">Только в наличии</span>
        </label>
      </div>

      {/* Сброс */}
      <button
        onClick={() => onFiltersChange({
          marketplace_ids: [],
          min_price: undefined,
          max_price: undefined,
          in_stock: true,
          sort_by: 'relevance',
        })}
        className="w-full p-3 rounded-xl border border-[var(--bd)] text-[var(--td)] text-sm hover:border-[var(--r)] hover:text-[var(--r)] transition-colors"
      >
        Сбросить фильтры
      </button>
    </div>
  )
}
