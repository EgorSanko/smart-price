'use client'

import { useState, useRef, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Search, Loader2, ExternalLink, BarChart2, X, Scale, ChevronDown, ArrowUpDown, Store, Star, ShoppingBag, Eye, Sparkles } from 'lucide-react'
import { searchProducts, getPriceHistory, compareProducts, proxyImage, type Product, type SearchStreamEvent, type PriceHistoryResponse } from '@/lib/api'

const MP_META: Record<string, { label: string; color: string; badge: string }> = {
  onliner:     { label: 'Onliner',       color: '#65cb02', badge: 'mp-badge-onliner' },
  yandex:      { label: 'Яндекс Маркет', color: '#ffcc00', badge: 'mp-badge-yandex' },
  wildberries: { label: 'Wildberries',    color: '#cb11ab', badge: 'mp-badge-wb' },
  citilink:    { label: 'Ситилинк',       color: '#ff6600', badge: 'mp-badge-citilink' },
  regard:      { label: 'Регард',         color: '#e53935', badge: 'mp-badge-regard' },
  aliexpress:  { label: 'AliExpress',     color: '#ff4747', badge: 'mp-badge-aliexpress' },
  worlddevices:{ label: 'World Devices',  color: '#2196f3', badge: 'mp-badge-worlddevices' },
  oneclick:    { label: '1click',         color: '#0084ff', badge: 'mp-badge-oneclick' },
  biggeek:     { label: 'BigGeek',        color: '#7b1fa2', badge: 'mp-badge-biggeek' },
}

type SortMode = 'price_asc' | 'price_desc'

function HomePageInner() {
  const searchParams = useSearchParams()
  const [query, setQuery] = useState('')
  const [region, setRegion] = useState<'BY' | 'RU' | 'all'>('BY')
  const [isLoading, setIsLoading] = useState(false)
  const [products, setProducts] = useState<Product[]>([])
  const [statusText, setStatusText] = useState('')
  const [sort, setSort] = useState<SortMode>('price_asc')
  const [mpStatus, setMpStatus] = useState<Record<string, { name: string; count: number; status: 'pending' | 'loading' | 'done' }>>({})

  // Query correction
  const [correctedQuery, setCorrectedQuery] = useState<string | null>(null)
  const [originalQuery, setOriginalQuery] = useState<string | null>(null)

  // Compare
  const [compareList, setCompareList] = useState<Product[]>([])
  const [showCompare, setShowCompare] = useState(false)
  const [compareText, setCompareText] = useState('')
  const [isComparing, setIsComparing] = useState(false)

  // History
  const [historyProduct, setHistoryProduct] = useState<Product | null>(null)
  const [historyData, setHistoryData] = useState<PriceHistoryResponse | null>(null)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  const cleanupRef = useRef<(() => void) | null>(null)

  const startSearch = useCallback((searchQuery: string, searchRegion: string) => {
    if (!searchQuery.trim()) return

    cleanupRef.current?.()
    setIsLoading(true)
    setProducts([])
    setMpStatus({})
    setCorrectedQuery(null)
    setOriginalQuery(null)
    setStatusText('Подключаемся к маркетплейсам...')

    cleanupRef.current = searchProducts(
      searchQuery.trim(),
      searchRegion,
      (event: SearchStreamEvent) => {
        if (event.status === 'start') {
          setStatusText(`Поиск "${event.query}"...`)
          const initial: typeof mpStatus = {}
          for (const src of (event.sources || [])) {
            const meta = MP_META[src]
            initial[src] = { name: meta?.label || src, count: 0, status: 'pending' }
          }
          setMpStatus(initial)
        } else if (event.status === 'corrected') {
          setCorrectedQuery(event.corrected || null)
          setOriginalQuery(event.original || null)
          setStatusText(`Исправлено: "${event.corrected}"`)
        } else if (event.status === 'parsing') {
          setStatusText(`Сканируем ${event.name || event.source}...`)
          setMpStatus(prev => ({ ...prev, [event.source!]: { ...prev[event.source!], status: 'loading' } }))
        } else if (event.status === 'done') {
          setMpStatus(prev => ({ ...prev, [event.source!]: { name: event.name || event.source!, count: event.count || 0, status: 'done' } }))
        } else if (event.status === 'complete') {
          const count = event.total || 0
          // Replace the accumulated per-source list with the backend's
          // final filtered list. Per-source `done` events only passed
          // through the fast regex filter — cluster/category/AI filters
          // run on the combined pool at the end and their verdict only
          // arrives here. Without this replace, games/accessories leak
          // into the UI for queries like "PlayStation 5".
          if (event.products) {
            setProducts(event.products)
            // Recalculate per-source badge counts from the FINAL filtered
            // list. Otherwise the sidebar keeps showing raw counts from
            // the `done` events (pre cluster/category/AI), so the user
            // sees "BigGeek 12" in the badge but can't find any BigGeek
            // items in the scrollable list because all 12 were dropped
            // by downstream filters. Keep `status: 'done'` for sources
            // that reported in but now have 0 items, so they still show
            // as "finished" (greyed out) rather than "loading".
            const finalCounts: Record<string, number> = {}
            for (const p of event.products) {
              finalCounts[p.marketplace] = (finalCounts[p.marketplace] || 0) + 1
            }
            setMpStatus(prev => {
              const next: typeof prev = {}
              for (const key of Object.keys(prev)) {
                next[key] = { ...prev[key], count: finalCounts[key] || 0 }
              }
              return next
            })
          }
          setStatusText(count > 0 ? `Найдено ${count} предложений` : 'Ничего не найдено')
          setIsLoading(false)
        } else if (event.status === 'error') {
          setStatusText(`Ошибка: ${event.error}`)
          setIsLoading(false)
        }
      },
      () => {
        setStatusText('Ошибка подключения к серверу')
        setIsLoading(false)
      }
    )
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isLoading) return
    startSearch(query, region)
  }

  // Auto-search from URL params (e.g. from catalog page)
  const autoSearchDone = useRef(false)
  useEffect(() => {
    const q = searchParams.get('q')
    if (q && !autoSearchDone.current) {
      autoSearchDone.current = true
      setQuery(q)
      setRegion('all')
      startSearch(q, 'all')
    }
  }, [searchParams, startSearch])

  const sortedProducts = [...products].sort((a, b) =>
    sort === 'price_asc' ? a.price_num - b.price_num : b.price_num - a.price_num
  )

  const toggleCompare = (product: Product) => {
    setCompareList(prev => {
      const exists = prev.find(p => p.url === product.url)
      if (exists) return prev.filter(p => p.url !== product.url)
      if (prev.length >= 4) return prev
      return [...prev, product]
    })
  }

  const runCompare = () => {
    if (compareList.length < 2) return
    setShowCompare(true)
    setCompareText('')
    setIsComparing(true)
    compareProducts(compareList, (d) => {
      if (d.text) setCompareText(p => p + d.text)
      if (d.done) setIsComparing(false)
    }, () => { setCompareText('Ошибка сравнения'); setIsComparing(false) })
  }

  const loadHistory = async (product: Product) => {
    if (!product.onliner_key) return
    setHistoryProduct(product)
    setHistoryData(null)
    setIsLoadingHistory(true)
    const data = await getPriceHistory(product.onliner_key)
    setHistoryData(data)
    setIsLoadingHistory(false)
  }

  // Save search state to sessionStorage so back button restores it
  useEffect(() => {
    if (!isLoading && products.length > 0) {
      sessionStorage.setItem('sp_search', JSON.stringify({ query, region, products }))
    }
  }, [products, isLoading, query, region])

  // Restore search state from sessionStorage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem('sp_search')
    if (saved && !searchParams.get('q')) {
      try {
        const { query: sq, region: sr, products: sp } = JSON.parse(saved)
        if (sp?.length > 0) {
          setQuery(sq || '')
          setRegion(sr || 'BY')
          setProducts(sp)
          setStatusText(`Найдено ${sp.length} предложений`)
        }
      } catch {}
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { return () => cleanupRef.current?.() }, [])

  const bestPrice = sortedProducts.length > 0 ? sortedProducts[0] : null


  return (
    <div className="min-h-[calc(100vh-7rem)]">
      {/* Hero search */}
      <section className="relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full opacity-20 blur-[120px] pointer-events-none" style={{ background: 'radial-gradient(var(--ac), transparent)' }} />

        <div className="container relative z-10 pt-12 pb-8">
          {products.length === 0 && !isLoading && (
            <div className="text-center mb-8">
              <h1 className="text-3xl sm:text-4xl font-extrabold mb-3 tracking-tight">
                Лучшие цены на <span className="gradient-text">одном экране</span>
              </h1>
              <p className="text-[var(--td)] text-base max-w-md mx-auto">
                Мгновенный поиск по маркетплейсам Беларуси и России
              </p>
            </div>
          )}

          {/* Region + Search */}
          <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
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

            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--tm)] pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="iPhone 16 Pro, Samsung Galaxy S25, Xiaomi 14..."
                className="input pl-12 pr-28 py-4 text-base rounded-2xl bg-[var(--c1)] border-[var(--bd2)]"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !query.trim()}
                className="absolute right-2 top-2 bottom-2 px-6 bg-[var(--ac)] text-white rounded-xl font-semibold text-sm hover:bg-[var(--ac2)] transition-all disabled:opacity-40 flex items-center gap-2"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Найти'}
              </button>
            </div>

            {correctedQuery && originalQuery && (
              <div className="flex items-center justify-center gap-2 mt-3 text-sm">
                <span className="text-[var(--td)]">Исправлено:</span>
                <span className="line-through text-[var(--tm)]">{originalQuery}</span>
                <span className="text-[var(--t)]">→</span>
                <span className="font-semibold text-[var(--ac)]">{correctedQuery}</span>
              </div>
            )}

            {statusText && (
              <div className="flex items-center justify-center gap-2 mt-3">
                {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--ac)]" />}
                <p className="text-[var(--td)] text-sm">{statusText}</p>
              </div>
            )}

            {/* Per-marketplace status badges */}
            {Object.keys(mpStatus).length > 0 && (
              <div className="flex flex-wrap justify-center gap-2 mt-3">
                {Object.entries(mpStatus).map(([key, mp]) => {
                  const meta = MP_META[key]
                  return (
                    <div
                      key={key}
                      className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                        mp.status === 'done' && mp.count > 0
                          ? 'border-[var(--g)] bg-[rgba(34,197,94,.08)] text-[var(--g)]'
                          : mp.status === 'done' && mp.count === 0
                          ? 'border-[var(--bd)] bg-[var(--c2)] text-[var(--tm)]'
                          : mp.status === 'loading'
                          ? 'border-[var(--ac)] bg-[rgba(99,102,241,.08)] text-[var(--ac)]'
                          : 'border-[var(--bd)] bg-[var(--c2)] text-[var(--td)]'
                      }`}
                    >
                      {mp.status === 'loading' && <Loader2 className="w-3 h-3 animate-spin" />}
                      {mp.status === 'done' && mp.count > 0 && <span className="w-1.5 h-1.5 rounded-full bg-[var(--g)]" />}
                      {mp.status === 'done' && mp.count === 0 && <span className="w-1.5 h-1.5 rounded-full bg-[var(--tm)]" />}
                      <span style={meta ? { color: mp.status === 'done' && mp.count > 0 ? undefined : meta.color } : undefined}>
                        {mp.name}
                      </span>
                      {mp.status === 'done' && <span className="opacity-70">{mp.count}</span>}
                    </div>
                  )
                })}
              </div>
            )}
          </form>
        </div>
      </section>

      <div className="container pb-8">
        {/* Best price highlight */}
        {bestPrice && !isLoading && (
          <div className="mb-6 p-4 rounded-2xl border animate-slideUp" style={{
            background: 'linear-gradient(135deg, rgba(34,197,94,.06), transparent 60%)',
            borderColor: 'rgba(34,197,94,.2)',
          }}>
            <div className="flex items-center gap-4">
              {bestPrice.image && (
                <div className="w-16 h-16 rounded-xl bg-white p-1 shrink-0">
                  <img src={proxyImage(bestPrice.image)} alt={bestPrice.title} className="w-full h-full object-contain" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-[var(--g)] uppercase tracking-wider mb-0.5">Лучшая цена</p>
                <p className="text-sm text-[var(--t)] font-medium line-clamp-1">{bestPrice.title}</p>
                <p className="text-xs text-[var(--td)]">{bestPrice.shop}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xl font-extrabold text-[var(--g)]">{bestPrice.price}</p>
              </div>
              <a href={bestPrice.url} target="_blank" rel="noopener noreferrer" className="btn-primary text-xs py-2 px-4 shrink-0">
                Купить
              </a>
            </div>
          </div>
        )}

        {/* Results toolbar */}
        {products.length > 0 && (
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-[var(--td)]">
              <span className="text-[var(--t)] font-semibold">{products.length}</span> предложений
            </p>
            <button
              onClick={() => setSort(s => s === 'price_asc' ? 'price_desc' : 'price_asc')}
              className="btn-secondary text-xs"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              {sort === 'price_asc' ? 'Сначала дешёвые' : 'Сначала дорогие'}
            </button>
          </div>
        )}

        {/* Products grid */}
        {sortedProducts.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {sortedProducts.map((product, idx) => {
              const mp = MP_META[product.marketplace] || { label: product.marketplace, color: '#888', badge: '' }
              const isInCompare = compareList.some(p => p.url === product.url)

              return (
                <div
                  key={product.url || idx}
                  className="card p-0 overflow-hidden flex flex-col animate-fadeIn"
                  style={{ animationDelay: `${Math.min(idx * 30, 300)}ms` }}
                >
                  {/* Image */}
                  <div className="relative bg-white aspect-[4/3] overflow-hidden">
                    {product.image ? (
                      <img src={proxyImage(product.image)} alt={product?.title || ''} className="w-full h-full object-contain p-3" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-[var(--tm)] text-2xl">
                        <Store className="w-10 h-10 opacity-30" />
                      </div>
                    )}

                    {/* Rank badge */}
                    {idx < 3 && sort === 'price_asc' && (
                      <div className={`absolute top-2 left-2 w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold text-white ${
                        idx === 0 ? 'bg-[var(--g)]' : idx === 1 ? 'bg-[var(--o)]' : 'bg-[var(--ac)]'
                      }`}>
                        {idx + 1}
                      </div>
                    )}

                    {/* MP badge */}
                    <div className="absolute bottom-2 right-2">
                      <span className={`badge ${mp.badge || ''}`} style={!mp.badge ? { background: `${mp.color}15`, color: mp.color } : undefined}>
                        {mp.label}
                      </span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex flex-col flex-1 p-3.5">
                    <p className="text-[13px] text-[var(--t2)] font-medium line-clamp-2 mb-1.5 leading-snug min-h-[36px]">
                      {product.title}
                    </p>

                    {product.specs && (
                      <p className="text-[11px] text-[var(--tm)] line-clamp-1 mb-2">{product.specs}</p>
                    )}

                    <div className="mt-auto">
                      <div className="flex items-baseline gap-2 mb-1">
                        <span className="text-lg font-extrabold text-[var(--t)]">{product.price}</span>
                      </div>
                      <p className="text-xs text-[var(--td)] flex items-center gap-1">
                        <Store className="w-3 h-3" />
                        {product.shop}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-1.5 mt-3">
                      {product.onliner_key ? (
                        <Link
                          href={`/product?key=${encodeURIComponent(product.onliner_key)}`}
                          className="flex-1 btn-primary text-xs py-2"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Подробнее
                        </Link>
                      ) : (
                        <a
                          href={product.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-1 btn-primary text-xs py-2"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          В магазин
                        </a>
                      )}

                      <Link
                        href={`/analyze?q=${encodeURIComponent(product.title)}&region=${region === 'all' ? 'RU' : region}&auto=1`}
                        className="p-2 rounded-xl border border-[var(--bd)] text-[var(--td)] hover:border-[var(--ac)] hover:text-[var(--ac)] transition-all"
                        title="Анализ цены"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                      </Link>

                      <button
                        onClick={() => toggleCompare(product)}
                        className={`p-2 rounded-xl border transition-all ${
                          isInCompare
                            ? 'bg-[var(--ac)] border-[var(--ac)] text-white'
                            : 'border-[var(--bd)] text-[var(--td)] hover:border-[var(--ac)] hover:text-[var(--ac)]'
                        }`}
                        title="Сравнить"
                      >
                        <Scale className="w-3.5 h-3.5" />
                      </button>

                      {product.onliner_key && (
                        <button
                          onClick={() => loadHistory(product)}
                          className="p-2 rounded-xl border border-[var(--bd)] text-[var(--td)] hover:border-[var(--ac)] hover:text-[var(--ac)] transition-all"
                          title="История цен"
                        >
                          <BarChart2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Loading skeleton */}
        {isLoading && products.length === 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 mt-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="card overflow-hidden">
                <div className="aspect-[4/3] shimmer" />
                <div className="p-4 space-y-3">
                  <div className="h-4 shimmer rounded w-3/4" />
                  <div className="h-3 shimmer rounded w-1/2" />
                  <div className="h-6 shimmer rounded w-1/3" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && products.length === 0 && !statusText && (
          <div className="text-center py-16">
            <div className="w-20 h-20 mx-auto mb-5 rounded-2xl bg-[var(--c2)] flex items-center justify-center">
              <Search className="w-8 h-8 text-[var(--tm)]" />
            </div>
            <p className="text-[var(--td)] text-sm max-w-sm mx-auto">
              Введите название товара, чтобы найти лучшие цены на маркетплейсах
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-6">
              {['iPhone 16 Pro', 'Samsung Galaxy S25', 'MacBook Air M3', 'PlayStation 5'].map(q => (
                <button
                  key={q}
                  onClick={() => setQuery(q)}
                  className="px-4 py-2 rounded-xl bg-[var(--c2)] border border-[var(--bd)] text-xs text-[var(--td)] hover:text-[var(--t)] hover:border-[var(--bd2)] transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Compare floating bar */}
      {compareList.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--bd)] animate-slideUp" style={{ background: 'rgba(10,10,15,.92)', backdropFilter: 'blur(20px)' }}>
          <div className="container py-3 flex items-center gap-3">
            <div className="flex gap-2 flex-1 overflow-x-auto">
              {compareList.map((p, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-1.5 bg-[var(--c2)] rounded-lg border border-[var(--bd)] shrink-0">
                  <span className="text-xs text-[var(--t)] max-w-[100px] truncate">{p.title}</span>
                  <button onClick={() => toggleCompare(p)} className="text-[var(--tm)] hover:text-[var(--r)]">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
            <button onClick={runCompare} disabled={compareList.length < 2} className="btn-primary text-xs py-2">
              <Scale className="w-3.5 h-3.5" />
              Сравнить ({compareList.length})
            </button>
          </div>
        </div>
      )}

      {/* Compare modal */}
      {showCompare && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/80" onClick={() => setShowCompare(false)} />
          <div className="relative card-glass w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-[rgba(255,255,255,.06)]">
              <h2 className="font-bold text-[var(--t)] flex items-center gap-2">
                <Scale className="w-5 h-5 text-[var(--ac)]" />
                AI Сравнение
              </h2>
              <button onClick={() => setShowCompare(false)} className="p-1 text-[var(--td)] hover:text-[var(--t)]">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-5">
              {isComparing && !compareText && (
                <div className="flex items-center gap-3 text-[var(--td)]">
                  <Loader2 className="w-5 h-5 animate-spin text-[var(--ac)]" />
                  Анализирую товары...
                </div>
              )}
              <div className="text-[var(--t2)] whitespace-pre-wrap text-sm leading-relaxed">{compareText}</div>
            </div>
          </div>
        </div>
      )}

      {/* History modal */}
      {historyProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/80" onClick={() => setHistoryProduct(null)} />
          <div className="relative card-glass w-full max-w-lg overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-[rgba(255,255,255,.06)]">
              <h2 className="font-bold text-[var(--t)] flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-[var(--ac)]" />
                История цен
              </h2>
              <button onClick={() => setHistoryProduct(null)} className="p-1 text-[var(--td)] hover:text-[var(--t)]">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5">
              <p className="text-sm text-[var(--td)] mb-4 line-clamp-2">{historyProduct.title}</p>

              {isLoadingHistory && (
                <div className="flex items-center justify-center gap-3 text-[var(--td)] py-8">
                  <Loader2 className="w-5 h-5 animate-spin text-[var(--ac)]" />
                </div>
              )}

              {historyData && !historyData.has_data && (
                <p className="text-center text-[var(--tm)] py-8 text-sm">Нет данных об истории цен</p>
              )}

              {historyData?.has_data && (
                <>
                  <div className="grid grid-cols-3 gap-2 mb-4">
                    {[
                      { label: 'Мин', value: historyData.stats.min, color: 'var(--g)' },
                      { label: 'Средняя', value: historyData.stats.avg, color: 'var(--t)' },
                      { label: 'Макс', value: historyData.stats.max, color: 'var(--r)' },
                    ].map(s => (
                      <div key={s.label} className="bg-[var(--c2)] rounded-xl p-3 text-center border border-[var(--bd)]">
                        <p className="text-[10px] text-[var(--tm)] uppercase tracking-wider">{s.label}</p>
                        <p className="text-base font-bold mt-0.5" style={{ color: s.color }}>{s.value.toFixed(0)}</p>
                      </div>
                    ))}
                  </div>
                  {historyData.stats.current && historyData.stats.current > 0 && (
                    <p className="text-center text-sm mb-3 text-[var(--td)]">
                      Сейчас: <span className="font-bold text-[var(--ac)]">{historyData.stats.current.toFixed(0)} BYN</span>
                    </p>
                  )}
                  <div className="max-h-48 overflow-y-auto space-y-1">
                    {historyData.history.slice(-15).reverse().map((h, i) => (
                      <div key={i} className="flex items-center justify-between py-2 px-2 rounded-lg hover:bg-[var(--c2)]">
                        <span className="text-xs text-[var(--tm)]">{new Date(h.date).toLocaleDateString('ru-RU')}</span>
                        <span className="text-sm font-medium text-[var(--t)]">{h.price.toFixed(0)} {h.currency}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function HomePage() {
  return (
    <Suspense>
      <HomePageInner />
    </Suspense>
  )
}
