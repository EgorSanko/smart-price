/**
 * Search page with improved UX
 */

'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useState, useEffect, useRef, Suspense } from 'react'
import Link from 'next/link'
import { ProductCard, ProductCardSkeleton } from '@/components/product'
import { FilterPanel } from '@/components/search'
import { useSearch, useSearchSuggestions } from '@/hooks/useSearch'
import { formatNumber } from '@/lib/utils'
import { 
  ChevronLeft, 
  ChevronRight, 
  SlidersHorizontal, 
  X, 
  Package, 
  Search,
  TrendingUp,
  Sparkles
} from 'lucide-react'

const POPULAR_SEARCHES = [
  'iPhone 15 Pro',
  'Samsung Galaxy',
  'AirPods Pro',
  'MacBook Air',
  'PlayStation 5',
  'Робот-пылесос',
]

function SearchContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  
  const query = searchParams.get('q') || ''
  const page = parseInt(searchParams.get('page') || '1')
  
  const [filters, setFilters] = useState({
    marketplace_ids: [] as number[],
    min_price: undefined as number | undefined,
    max_price: undefined as number | undefined,
    in_stock: true,
    sort_by: 'relevance' as string,
  })

  const [showMobileFilters, setShowMobileFilters] = useState(false)
  const [searchInput, setSearchInput] = useState(query)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)

  // Update input when URL changes
  useEffect(() => {
    setSearchInput(query)
  }, [query])

  // Click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const { data: suggestions } = useSearchSuggestions(searchInput)
  
  const { data, isLoading, isError, refetch } = useSearch(
    query ? { q: query, ...filters, page, per_page: 20 } : null
  )

  const products = data?.products || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / 20)

  const handleSearch = (searchQuery?: string) => {
    const q = searchQuery || searchInput
    if (q.trim()) {
      router.push(`/search?q=${encodeURIComponent(q.trim())}`)
      setShowSuggestions(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleSearch()
  }

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set('page', String(newPage))
    router.push(`/search?${params.toString()}`)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Empty query - show search prompt
  if (!query) {
    return (
      <div className="min-h-screen py-16">
        <div className="container">
          <div className="max-w-2xl mx-auto text-center">
            <div className="w-20 h-20 bg-accent/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <Search className="w-10 h-10 text-accent-light" />
            </div>
            <h1 className="text-3xl font-bold text-txt-primary mb-3">Поиск товаров</h1>
            <p className="text-txt-secondary mb-8">
              Найдите лучшие цены на товары с Ozon, Wildberries, Яндекс Маркет и AliExpress
            </p>
            
            {/* Search form */}
            <form onSubmit={handleSubmit} className="relative mb-8" ref={searchRef}>
              <input
                type="text"
                value={searchInput}
                onChange={(e) => {
                  setSearchInput(e.target.value)
                  setShowSuggestions(true)
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder="Например: iPhone 15 Pro"
                className="input pr-14 text-lg py-4"
                autoFocus
              />
              <button 
                type="submit" 
                className="absolute right-2 top-2 bottom-2 px-5 bg-accent text-white rounded-xl hover:bg-accent-light transition-colors"
              >
                <Search className="w-5 h-5" />
              </button>
              
              {/* Suggestions dropdown */}
              {showSuggestions && suggestions?.suggestions && suggestions.suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-graphite-800 border border-graphite-600 rounded-xl shadow-card overflow-hidden z-50">
                  {suggestions.suggestions.map((s, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSearch(s)}
                      className="w-full px-4 py-3 text-left text-txt-secondary hover:bg-graphite-700 hover:text-txt-primary flex items-center gap-3 transition-colors"
                    >
                      <Search className="w-4 h-4 text-txt-muted" />
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </form>

            {/* Popular searches */}
            <div>
              <p className="text-sm text-txt-muted mb-3 flex items-center justify-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Популярные запросы
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {POPULAR_SEARCHES.map((term) => (
                  <button
                    key={term}
                    onClick={() => handleSearch(term)}
                    className="px-4 py-2 bg-graphite-800 border border-graphite-600 rounded-full text-sm text-txt-secondary hover:bg-graphite-700 hover:text-txt-primary hover:border-accent/30 transition-all"
                  >
                    {term}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Search bar */}
      <div className="bg-graphite-900 border-b border-graphite-600 py-4 sticky top-16 z-40">
        <div className="container">
          <form onSubmit={handleSubmit} className="relative max-w-2xl" ref={searchRef}>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value)
                setShowSuggestions(true)
              }}
              onFocus={() => setShowSuggestions(true)}
              placeholder="Искать товары..."
              className="input pr-14"
            />
            <button 
              type="submit" 
              className="absolute right-2 top-2 bottom-2 px-4 bg-accent text-white rounded-lg hover:bg-accent-light transition-colors"
            >
              <Search className="w-5 h-5" />
            </button>
            
            {/* Suggestions */}
            {showSuggestions && suggestions?.suggestions && suggestions.suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-graphite-800 border border-graphite-600 rounded-xl shadow-card overflow-hidden z-50">
                {suggestions.suggestions.map((s, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => handleSearch(s)}
                    className="w-full px-4 py-3 text-left text-txt-secondary hover:bg-graphite-700 hover:text-txt-primary flex items-center gap-3 transition-colors"
                  >
                    <Search className="w-4 h-4 text-txt-muted" />
                    {s}
                  </button>
                ))}
              </div>
            )}
          </form>
        </div>
      </div>

      <div className="container py-6">
        <div className="flex gap-6">
          {/* Desktop Filters */}
          <aside className="hidden lg:block w-64 flex-shrink-0">
            <div className="sticky top-36">
              <div className="card p-5">
                <FilterPanel 
                  facets={data?.facets || null} 
                  filters={filters} 
                  onFiltersChange={setFilters} 
                />
              </div>
            </div>
          </aside>

          {/* Results */}
          <div className="flex-1 min-w-0">
            {/* Results header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                {isLoading ? (
                  <div className="h-7 w-48 bg-graphite-800 rounded animate-pulse" />
                ) : (
                  <>
                    <h1 className="text-xl font-bold text-txt-primary">
                      {total > 0 ? `Найдено ${formatNumber(total)} товаров` : 'Ничего не найдено'}
                    </h1>
                    <p className="text-sm text-txt-muted">по запросу «{query}»</p>
                  </>
                )}
              </div>

              <button
                onClick={() => setShowMobileFilters(true)}
                className="lg:hidden flex items-center gap-2 px-4 py-2.5 bg-graphite-800 border border-graphite-600 rounded-xl font-medium text-txt-secondary hover:bg-graphite-700 transition-colors"
              >
                <SlidersHorizontal className="w-5 h-5" />
                Фильтры
              </button>
            </div>

            {/* Error */}
            {isError && (
              <div className="card p-12 text-center">
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <X className="w-8 h-8 text-red-500" />
                </div>
                <h3 className="text-lg font-semibold text-txt-primary mb-2">Ошибка загрузки</h3>
                <p className="text-txt-secondary mb-4">Не удалось загрузить результаты</p>
                <button onClick={() => refetch()} className="btn-primary">Попробовать снова</button>
              </div>
            )}

            {/* Loading */}
            {isLoading && (
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                {Array.from({ length: 8 }).map((_, i) => <ProductCardSkeleton key={i} />)}
              </div>
            )}

            {/* Results */}
            {!isLoading && !isError && products.length > 0 && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                  {products.map((product) => <ProductCard key={product.id} product={product} />)}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-8">
                    <button
                      onClick={() => handlePageChange(page - 1)}
                      disabled={page === 1}
                      className="p-2.5 rounded-xl border border-graphite-600 bg-graphite-800 disabled:opacity-50 hover:bg-graphite-700 text-txt-primary transition-colors"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum = i + 1
                        if (totalPages > 5) {
                          if (page <= 3) pageNum = i + 1
                          else if (page >= totalPages - 2) pageNum = totalPages - 4 + i
                          else pageNum = page - 2 + i
                        }
                        return (
                          <button
                            key={pageNum}
                            onClick={() => handlePageChange(pageNum)}
                            className={`w-10 h-10 rounded-xl font-medium transition-colors ${
                              pageNum === page
                                ? 'bg-accent text-white shadow-glow'
                                : 'bg-graphite-800 border border-graphite-600 hover:bg-graphite-700 text-txt-secondary'
                            }`}
                          >
                            {pageNum}
                          </button>
                        )
                      })}
                    </div>
                    <button
                      onClick={() => handlePageChange(page + 1)}
                      disabled={page === totalPages}
                      className="p-2.5 rounded-xl border border-graphite-600 bg-graphite-800 disabled:opacity-50 hover:bg-graphite-700 text-txt-primary transition-colors"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Empty results */}
            {!isLoading && !isError && products.length === 0 && query && (
              <div className="card p-12 text-center">
                <div className="w-16 h-16 bg-graphite-700 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Package className="w-8 h-8 text-txt-muted" />
                </div>
                <h3 className="text-lg font-semibold text-txt-primary mb-2">Товары не найдены</h3>
                <p className="text-txt-secondary mb-6">Попробуйте изменить запрос или фильтры</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {POPULAR_SEARCHES.slice(0, 4).map((term) => (
                    <button
                      key={term}
                      onClick={() => handleSearch(term)}
                      className="px-4 py-2 bg-graphite-700 rounded-full text-sm text-txt-secondary hover:bg-accent hover:text-white transition-colors"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile filters modal */}
      {showMobileFilters && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/70" onClick={() => setShowMobileFilters(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-graphite-800 border-l border-graphite-600 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-graphite-600">
              <h2 className="text-lg font-semibold text-txt-primary">Фильтры</h2>
              <button 
                onClick={() => setShowMobileFilters(false)} 
                className="p-2 text-txt-secondary hover:text-txt-primary transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              <FilterPanel 
                facets={data?.facets || null} 
                filters={filters} 
                onFiltersChange={(f) => { 
                  setFilters(f)
                  setShowMobileFilters(false) 
                }} 
              />
            </div>
            <div className="p-4 border-t border-graphite-600">
              <button 
                onClick={() => setShowMobileFilters(false)}
                className="btn-primary w-full justify-center"
              >
                Показать результаты
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen py-6">
        <div className="container">
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => <ProductCardSkeleton key={i} />)}
          </div>
        </div>
      </div>
    }>
      <SearchContent />
    </Suspense>
  )
}
