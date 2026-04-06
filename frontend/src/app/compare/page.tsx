'use client'

import { useState, useRef, useEffect } from 'react'
import { Search, Loader2, X, Scale, ArrowRight, Store, ExternalLink } from 'lucide-react'
import { searchProducts, compareProducts, proxyImage, type Product, type SearchStreamEvent } from '@/lib/api'

const MP_META: Record<string, { label: string; color: string; badge: string }> = {
  onliner:     { label: 'Onliner',       color: '#65cb02', badge: 'mp-badge-onliner' },
  yandex:      { label: 'Яндекс Маркет', color: '#ffcc00', badge: 'mp-badge-yandex' },
  wildberries: { label: 'Wildberries',    color: '#cb11ab', badge: 'mp-badge-wb' },
  citilink:    { label: 'Ситилинк',       color: '#ff6600', badge: 'mp-badge-citilink' },
  regard:      { label: 'Регард',         color: '#e53935', badge: 'mp-badge-regard' },
  aliexpress:  { label: 'AliExpress',     color: '#ff4747', badge: 'mp-badge-aliexpress' },
  worlddevices:{ label: 'World Devices',  color: '#2196f3', badge: 'mp-badge-worlddevices' },
}

const STORAGE_KEY = 'sp_compare_state_v1'

interface PersistedState {
  query: string
  region: 'BY' | 'RU' | 'all'
  searchResults: Product[]
  selected: Product[]
  compareText: string
  status: string
}

function loadPersisted(): PersistedState | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as PersistedState
  } catch {
    return null
  }
}

export default function ComparePage() {
  const [hydrated, setHydrated] = useState(false)
  const [query, setQuery] = useState('')
  const [region, setRegion] = useState<'BY' | 'RU' | 'all'>('BY')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<Product[]>([])
  const [status, setStatus] = useState('')

  const [selected, setSelected] = useState<Product[]>([])
  const [compareText, setCompareText] = useState('')
  const [isComparing, setIsComparing] = useState(false)

  const cleanupRef = useRef<(() => void) | null>(null)

  // Restore state from localStorage on mount
  useEffect(() => {
    const saved = loadPersisted()
    if (saved) {
      setQuery(saved.query || '')
      setRegion(saved.region || 'BY')
      setSearchResults(saved.searchResults || [])
      setSelected(saved.selected || [])
      setCompareText(saved.compareText || '')
      setStatus(saved.status || '')
    }
    setHydrated(true)
  }, [])

  // Persist state on every change (including during search — results stream in)
  useEffect(() => {
    if (!hydrated) return
    try {
      const data: PersistedState = { query, region, searchResults, selected, compareText, status }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch {
      /* storage full or disabled — ignore */
    }
  }, [hydrated, query, region, searchResults, selected, compareText, status])

  const resetAll = () => {
    cleanupRef.current?.()
    setQuery('')
    setSearchResults([])
    setSelected([])
    setCompareText('')
    setStatus('')
    setIsSearching(false)
    setIsComparing(false)
    try { localStorage.removeItem(STORAGE_KEY) } catch { /* ignore */ }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isSearching) return

    cleanupRef.current?.()
    setIsSearching(true)
    setSearchResults([])
    setStatus('Ищем...')

    cleanupRef.current = searchProducts(
      query.trim(), region,
      (event: SearchStreamEvent) => {
        if (event.status === 'parsing') {
          setStatus(`Сканируем ${event.name || event.source}...`)
        } else if (event.status === 'done' && event.products) {
          setSearchResults(prev => [...prev, ...event.products!])
        } else if (event.status === 'complete') {
          setStatus(`Найдено ${event.total} предложений`)
          setIsSearching(false)
        } else if (event.status === 'error') {
          setStatus(`Ошибка: ${event.error}`)
          setIsSearching(false)
        }
      },
      () => { setStatus('Ошибка подключения'); setIsSearching(false) }
    )
  }

  const toggleProduct = (product: Product) => {
    setSelected(prev => {
      const exists = prev.find(p => p.url === product.url)
      if (exists) return prev.filter(p => p.url !== product.url)
      if (prev.length >= 4) return prev
      return [...prev, product]
    })
  }

  const removeProduct = (product: Product) => {
    setSelected(prev => prev.filter(p => p.url !== product.url))
  }

  const runCompare = () => {
    if (selected.length < 2) return
    setCompareText('')
    setIsComparing(true)
    compareProducts(
      selected,
      (data) => {
        if (data.text) setCompareText(prev => prev + data.text)
        if (data.done) setIsComparing(false)
      },
      () => { setCompareText('Ошибка сравнения. Попробуйте ещё раз.'); setIsComparing(false) }
    )
  }

  // Cancel any in-flight search on unmount (state already persisted above)
  useEffect(() => { return () => cleanupRef.current?.() }, [])

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      <div className="container py-8">
        <div className="max-w-4xl mx-auto">
          {/* Title */}
          <div className="text-center mb-8 relative">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[var(--ac)] to-purple-600 flex items-center justify-center shadow-lg shadow-[var(--ac-glow)]">
              <Scale className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-[var(--t)] mb-2 tracking-tight">Сравнение товаров</h1>
            <p className="text-[var(--td)] text-sm">Найдите товары и получите AI-анализ с рекомендацией</p>
            {(searchResults.length > 0 || selected.length > 0 || compareText) && (
              <button
                onClick={resetAll}
                className="absolute top-0 right-0 px-3 py-1.5 rounded-lg text-xs font-semibold text-[var(--td)] hover:text-[var(--t)] hover:bg-[var(--c2)] border border-[var(--bd)] transition-all flex items-center gap-1.5"
                title="Очистить всё"
              >
                <X className="w-3.5 h-3.5" />
                Очистить
              </button>
            )}
          </div>

          {/* Search */}
          <form onSubmit={handleSearch} className="mb-8">
            <div className="flex justify-center gap-2 mb-4">
              {([
                { key: 'BY' as const, flag: '🇧🇾', label: 'Беларусь' },
                { key: 'RU' as const, flag: '🇷🇺', label: 'Россия' },
              ]).map(r => (
                <button
                  key={r.key}
                  type="button"
                  onClick={() => setRegion(r.key)}
                  className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all ${
                    region === r.key
                      ? 'bg-[var(--ac)] text-white shadow-lg shadow-[var(--ac-glow)]'
                      : 'bg-[var(--c2)] text-[var(--td)] hover:text-[var(--t)] border border-[var(--bd)]'
                  }`}
                >
                  <span className="text-base">{r.flag}</span>
                  {r.label}
                </button>
              ))}
            </div>

            <div className="relative max-w-xl mx-auto">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--tm)] pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Найти товар для сравнения..."
                className="input pl-12 pr-28 py-3.5 rounded-2xl bg-[var(--c1)] border-[var(--bd2)]"
                disabled={isSearching}
              />
              <button
                type="submit"
                disabled={isSearching || !query.trim()}
                className="absolute right-2 top-2 bottom-2 px-5 bg-[var(--ac)] text-white rounded-xl font-semibold text-sm hover:bg-[var(--ac2)] transition-all disabled:opacity-40 flex items-center gap-2"
              >
                {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Найти'}
              </button>
            </div>

            {status && (
              <div className="flex items-center justify-center gap-2 mt-3">
                {isSearching && <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--ac)]" />}
                <p className="text-[var(--td)] text-sm">{status}</p>
              </div>
            )}
          </form>

          {/* Selected products */}
          {selected.length > 0 && (
            <div className="mb-8 animate-fadeIn">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-xs font-bold text-[var(--td)] uppercase tracking-wider">
                  Выбрано для сравнения ({selected.length}/4)
                </h2>
                <button
                  onClick={runCompare}
                  disabled={selected.length < 2 || isComparing}
                  className="btn-primary text-xs py-2"
                >
                  {isComparing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Scale className="w-4 h-4" />
                      Сравнить с AI
                    </>
                  )}
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {selected.map((product, idx) => {
                  const mp = MP_META[product.marketplace] || { label: product.marketplace, color: '#888', badge: '' }
                  return (
                    <div key={idx} className="card p-0 overflow-hidden relative group">
                      <button
                        onClick={() => removeProduct(product)}
                        className="absolute top-2 right-2 z-10 w-6 h-6 rounded-lg bg-black/50 text-white/70 hover:text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>

                      <div className="aspect-square bg-white overflow-hidden">
                        {product.image ? (
                          <img src={proxyImage(product.image)} alt={product.title} className="w-full h-full object-contain p-2" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Store className="w-8 h-8 text-gray-300" />
                          </div>
                        )}
                      </div>
                      <div className="p-2.5">
                        <p className="text-[11px] text-[var(--t2)] line-clamp-2 font-medium mb-1">{product.title}</p>
                        <p className="text-sm font-extrabold text-[var(--t)]">{product.price}</p>
                        <span className={`badge text-[9px] mt-1 ${mp.badge}`}>{mp.label}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* AI comparison result */}
          {(compareText || isComparing) && (
            <div className="mb-8 card-glass p-6 animate-fadeIn">
              <h2 className="text-base font-bold text-[var(--t)] mb-4 flex items-center gap-2">
                <Scale className="w-5 h-5 text-[var(--ac)]" />
                AI Сравнение
              </h2>

              {isComparing && !compareText && (
                <div className="flex items-center gap-3 text-[var(--td)]">
                  <Loader2 className="w-5 h-5 animate-spin text-[var(--ac)]" />
                  Анализирую товары...
                </div>
              )}

              <div className="text-[var(--t2)] whitespace-pre-wrap text-sm leading-relaxed">
                {compareText}
              </div>
            </div>
          )}

          {/* Search results */}
          {searchResults.length > 0 && (
            <div>
              <h2 className="text-xs font-bold text-[var(--td)] uppercase tracking-wider mb-3">
                Результаты поиска
              </h2>

              <div className="space-y-1.5">
                {searchResults.map((product, idx) => {
                  const isSelected = selected.some(p => p.url === product.url)
                  const mp = MP_META[product.marketplace] || { label: product.marketplace, color: '#888', badge: '' }

                  return (
                    <div
                      key={idx}
                      className={`flex items-center gap-3 p-3 rounded-xl border transition-all cursor-pointer animate-fadeIn ${
                        isSelected
                          ? 'border-[var(--ac)] bg-[var(--ac-glow2)]'
                          : 'border-[var(--bd)] bg-[var(--c1)] hover:border-[var(--bd2)] hover:bg-[var(--c2)]'
                      }`}
                      style={{ animationDelay: `${Math.min(idx * 20, 200)}ms` }}
                      onClick={() => toggleProduct(product)}
                    >
                      {product.image ? (
                        <img src={proxyImage(product.image)} alt={product.title} className="w-13 h-13 object-contain bg-white rounded-lg p-0.5 shrink-0" style={{ width: 52, height: 52 }} />
                      ) : (
                        <div className="bg-white rounded-lg flex items-center justify-center shrink-0" style={{ width: 52, height: 52 }}>
                          <Store className="w-6 h-6 text-gray-300" />
                        </div>
                      )}

                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-[var(--t)] line-clamp-1 font-medium">{product.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-[var(--tm)]">{product.shop}</span>
                          <span className={`badge text-[9px] py-0 px-1.5 ${mp.badge}`}>{mp.label}</span>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <p className="font-extrabold text-[var(--t)]">{product.price}</p>
                      </div>

                      <div className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center shrink-0 transition-all ${
                        isSelected
                          ? 'border-[var(--ac)] bg-[var(--ac)] text-white'
                          : 'border-[var(--bd2)]'
                      }`}>
                        {isSelected && <Scale className="w-3 h-3" />}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!isSearching && searchResults.length === 0 && selected.length === 0 && !compareText && (
            <div className="text-center py-12">
              <p className="text-[var(--td)] text-sm mb-8 max-w-md mx-auto">
                Найдите товары через поиск, выберите от 2 до 4 и получите AI-анализ
              </p>
              <div className="flex flex-wrap justify-center gap-4 text-sm text-[var(--td)]">
                {[
                  { n: '1', label: 'Найдите товары' },
                  { n: '2', label: 'Выберите 2-4' },
                  { n: '3', label: 'AI сравнит' },
                ].map((step, i) => (
                  <div key={step.n} className="flex items-center gap-2">
                    {i > 0 && <ArrowRight className="w-4 h-4 text-[var(--tm)] mr-2" />}
                    <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                      step.n === '3'
                        ? 'bg-[var(--ac)] text-white'
                        : 'bg-[var(--c2)] border border-[var(--bd)] text-[var(--td)]'
                    }`}>
                      {step.n}
                    </span>
                    {step.label}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
