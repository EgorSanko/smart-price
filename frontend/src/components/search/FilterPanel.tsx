/**
 * FilterPanel - фиолетово-графитовая тема
 */

'use client'

import { useState } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SearchFacets } from '@/types'

interface FilterPanelProps {
  facets: SearchFacets | null
  filters: {
    marketplace_ids: number[]
    min_price: number | undefined
    max_price: number | undefined
    in_stock: boolean
    sort_by: string
  }
  onFiltersChange: (filters: FilterPanelProps['filters']) => void
}

const marketplaces = [
  { id: 1, name: 'Ozon', color: '#005bff' },
  { id: 2, name: 'Wildberries', color: '#cb11ab' },
  { id: 3, name: 'Яндекс Маркет', color: '#ffcc00' },
  { id: 4, name: 'AliExpress', color: '#ff4747' },
]

const sortOptions = [
  { value: 'relevance', label: 'По релевантности' },
  { value: 'price_asc', label: 'Сначала дешевле' },
  { value: 'price_desc', label: 'Сначала дороже' },
  { value: 'rating', label: 'По рейтингу' },
]

function FilterSection({ title, defaultOpen = true, children }: { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border-b border-graphite-600 pb-5 mb-5 last:border-0 last:pb-0 last:mb-0">
      <button onClick={() => setIsOpen(!isOpen)} className="flex items-center justify-between w-full text-left mb-3">
        <span className="font-semibold text-txt-primary">{title}</span>
        <ChevronDown className={cn('w-5 h-5 text-txt-muted transition-transform', isOpen && 'rotate-180')} />
      </button>
      {isOpen && children}
    </div>
  )
}

export function FilterPanel({ facets, filters, onFiltersChange }: FilterPanelProps) {
  const toggleMarketplace = (id: number) => {
    const newIds = filters.marketplace_ids.includes(id)
      ? filters.marketplace_ids.filter((mpId) => mpId !== id)
      : [...filters.marketplace_ids, id]
    onFiltersChange({ ...filters, marketplace_ids: newIds })
  }

  return (
    <div>
      {/* Sort */}
      <FilterSection title="Сортировка">
        <select
          value={filters.sort_by}
          onChange={(e) => onFiltersChange({ ...filters, sort_by: e.target.value })}
          className="w-full bg-graphite-700 border border-graphite-600 rounded-xl px-4 py-2.5 text-sm font-medium text-txt-primary focus:outline-none focus:ring-2 focus:ring-accent"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </FilterSection>

      {/* Marketplaces */}
      <FilterSection title="Маркетплейсы">
        <div className="space-y-2">
          {marketplaces.map((mp) => {
            const isChecked = filters.marketplace_ids.includes(mp.id)
            return (
              <label
                key={mp.id}
                className={cn(
                  'flex items-center gap-3 p-2.5 rounded-xl cursor-pointer transition-colors',
                  isChecked ? 'bg-graphite-700' : 'hover:bg-graphite-700'
                )}
              >
                <div
                  className={cn(
                    'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
                    isChecked ? 'bg-accent border-accent' : 'border-graphite-500'
                  )}
                >
                  {isChecked && <Check className="w-3 h-3 text-white" />}
                </div>
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: mp.color }} />
                <span className="text-sm font-medium text-txt-secondary">{mp.name}</span>
                <input type="checkbox" checked={isChecked} onChange={() => toggleMarketplace(mp.id)} className="sr-only" />
              </label>
            )
          })}
        </div>
      </FilterSection>

      {/* Price */}
      <FilterSection title="Цена">
        <div className="flex items-center gap-2">
          <input
            type="number"
            placeholder="От"
            value={filters.min_price || ''}
            onChange={(e) => onFiltersChange({ ...filters, min_price: e.target.value ? parseInt(e.target.value) : undefined })}
            className="flex-1 bg-graphite-700 border border-graphite-600 rounded-xl px-3 py-2.5 text-sm text-txt-primary placeholder:text-txt-muted focus:outline-none focus:ring-2 focus:ring-accent"
          />
          <span className="text-txt-muted">—</span>
          <input
            type="number"
            placeholder="До"
            value={filters.max_price || ''}
            onChange={(e) => onFiltersChange({ ...filters, max_price: e.target.value ? parseInt(e.target.value) : undefined })}
            className="flex-1 bg-graphite-700 border border-graphite-600 rounded-xl px-3 py-2.5 text-sm text-txt-primary placeholder:text-txt-muted focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>
      </FilterSection>

      {/* In stock */}
      <FilterSection title="Наличие" defaultOpen={false}>
        <label className="flex items-center gap-3 cursor-pointer">
          <div
            className={cn(
              'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
              filters.in_stock ? 'bg-accent border-accent' : 'border-graphite-500'
            )}
          >
            {filters.in_stock && <Check className="w-3 h-3 text-white" />}
          </div>
          <span className="text-sm font-medium text-txt-secondary">Только в наличии</span>
          <input type="checkbox" checked={filters.in_stock} onChange={(e) => onFiltersChange({ ...filters, in_stock: e.target.checked })} className="sr-only" />
        </label>
      </FilterSection>

      {/* Reset */}
      <button
        onClick={() => onFiltersChange({ marketplace_ids: [], min_price: undefined, max_price: undefined, in_stock: true, sort_by: 'relevance' })}
        className="w-full text-sm font-medium text-txt-muted hover:text-accent-light py-2 transition-colors"
      >
        Сбросить фильтры
      </button>
    </div>
  )
}
