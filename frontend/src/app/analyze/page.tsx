'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Sparkles,
  BarChart3,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Info,
  ShieldAlert,
  Loader2,
  Search,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Store,
} from 'lucide-react'
import {
  analyzePrice,
  proxyImage,
  type AnalyzeResult,
  type AnalyzeStreamEvent,
  type OfferLite,
  type RedFlag,
} from '@/lib/api'

// ── Helpers ──────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'sp_analyze_state_v1'

interface PersistedState {
  query: string
  region: 'BY' | 'RU'
  result: AnalyzeResult
  ts: number
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

function formatPrice(num: number, currency: string): string {
  return `${num.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ${currency}`
}

const MP_META: Record<string, { label: string; color: string }> = {
  onliner:     { label: 'Onliner',        color: '#65cb02' },
  yandex:      { label: 'Яндекс Маркет',  color: '#ffcc00' },
  wildberries: { label: 'Wildberries',     color: '#cb11ab' },
  ozon:        { label: 'Ozon',            color: '#005bff' },
  citilink:    { label: 'Ситилинк',        color: '#ff6600' },
  regard:      { label: 'Регард',          color: '#e53935' },
  aliexpress:  { label: 'AliExpress',      color: '#ff4747' },
}

// ── Sub-components ───────────────────────────────────────────────────────────

function MarketplaceBadge({ marketplace }: { marketplace: string }) {
  const meta = MP_META[marketplace] || { label: marketplace, color: '#888' }
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold"
      style={{ background: `${meta.color}22`, color: meta.color }}
    >
      {meta.label}
    </span>
  )
}

function OfferCard({ offer, highlight }: { offer: OfferLite; highlight?: boolean }) {
  return (
    <a
      href={offer.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`flex items-center gap-3 p-3 rounded-xl border transition-all hover:border-[var(--bd2)] hover:bg-[var(--c3)] group ${
        highlight
          ? 'border-emerald-500/40 bg-emerald-500/5'
          : 'border-[var(--bd)] bg-[var(--c2)]'
      }`}
    >
      {offer.image ? (
        <img
          src={proxyImage(offer.image)}
          alt={offer.title}
          className="w-12 h-12 object-contain bg-white rounded-lg p-1 shrink-0"
        />
      ) : (
        <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center shrink-0">
          <Store className="w-5 h-5 text-gray-300" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-xs text-[var(--t)] font-medium line-clamp-2 leading-snug">{offer.title}</p>
        <div className="flex items-center gap-1.5 mt-1 flex-wrap">
          {offer.shop && <span className="text-[10px] text-[var(--tm)]">{offer.shop}</span>}
          <MarketplaceBadge marketplace={offer.marketplace} />
        </div>
      </div>
      <div className="text-right shrink-0 ml-1">
        <p className="font-extrabold text-sm text-[var(--t)] whitespace-nowrap">
          {formatPrice(offer.price_num, offer.currency)}
        </p>
        <ExternalLink className="w-3 h-3 text-[var(--tm)] group-hover:text-[var(--ac)] mt-1 ml-auto transition-colors" />
      </div>
    </a>
  )
}

function RedFlagItem({ flag }: { flag: RedFlag }) {
  const configs = {
    info:   { Icon: Info,          cls: 'border-blue-500/30 bg-blue-500/5 text-blue-400' },
    warn:   { Icon: AlertTriangle, cls: 'border-amber-500/30 bg-amber-500/5 text-amber-400' },
    danger: { Icon: ShieldAlert,   cls: 'border-red-500/30 bg-red-500/5 text-red-400' },
  }
  const { Icon, cls } = configs[flag.severity]
  return (
    <div className={`flex items-start gap-2.5 p-3 rounded-xl border ${cls}`}>
      <Icon className="w-4 h-4 shrink-0 mt-0.5" />
      <p className="text-sm leading-snug">{flag.text}</p>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

interface Progress {
  sources: string[]
  total: number
  phase: string
}

export default function AnalyzePage() {
  const [hydrated, setHydrated] = useState(false)
  const [query, setQuery] = useState('')
  const [region, setRegion] = useState<'BY' | 'RU'>('RU')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<Progress>({ sources: [], total: 0, phase: '' })
  const [correction, setCorrection] = useState<{ original: string; corrected: string } | null>(null)
  const [result, setResult] = useState<AnalyzeResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const cleanupRef = useRef<(() => void) | null>(null)
  const autoRunRef = useRef(false)

  const runAnalyze = useCallback((q: string, r: 'BY' | 'RU') => {
    if (q.trim().length < 2) return
    cleanupRef.current?.()
    setLoading(true)
    setResult(null)
    setError(null)
    setCorrection(null)
    setProgress({ sources: [], total: 0, phase: 'start' })

    const cleanup = analyzePrice(
      q.trim(),
      r,
      (ev: AnalyzeStreamEvent) => {
        if (ev.status === 'corrected') {
          setCorrection({ original: ev.original, corrected: ev.corrected })
        }
        if (ev.status === 'parsing') {
          const sources = ev.sources ?? (ev.source ? [ev.source] : [])
          setProgress(p => ({ ...p, sources, phase: 'parsing' }))
        }
        if (ev.status === 'scraped') {
          setProgress(p => ({ ...p, total: ev.total, phase: 'scraped' }))
        }
        if (ev.status === 'analyzing') {
          setProgress(p => ({ ...p, phase: 'analyzing' }))
        }
        if (ev.status === 'result') {
          setResult(ev.payload)
          setLoading(false)
          cleanupRef.current?.()
          // persist
          try {
            const data: PersistedState = { query: q.trim(), region: r, result: ev.payload, ts: Date.now() }
            localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
          } catch { /* ignore */ }
        }
        if (ev.status === 'error') {
          setError(ev.message)
          setLoading(false)
          cleanupRef.current?.()
        }
      },
      (err: string) => {
        setError(err)
        setLoading(false)
      }
    )
    cleanupRef.current = cleanup
  }, [])

  // Mount: read URL params or restore localStorage
  useEffect(() => {
    if (autoRunRef.current) return
    autoRunRef.current = true

    const params = new URLSearchParams(window.location.search)
    const urlQ = params.get('q')
    const urlRegion = params.get('region') as 'BY' | 'RU' | null
    const urlAuto = params.get('auto')

    if (urlQ) {
      setQuery(urlQ)
      if (urlRegion === 'BY' || urlRegion === 'RU') setRegion(urlRegion)
      if (urlAuto === '1') {
        const r = (urlRegion === 'BY' || urlRegion === 'RU') ? urlRegion : 'RU'
        runAnalyze(urlQ, r)
      }
    } else {
      const saved = loadPersisted()
      if (saved) {
        setQuery(saved.query)
        setRegion(saved.region)
        setResult(saved.result)
      }
    }
    setHydrated(true)
  }, [runAnalyze])

  useEffect(() => { return () => cleanupRef.current?.() }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    runAnalyze(query, region)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') runAnalyze(query, region)
  }

  // Progress phase label
  const phaseLabel = (() => {
    if (progress.phase === 'start') return 'Подключаемся к маркетплейсам...'
    if (progress.phase === 'parsing') return 'Ищем предложения...'
    if (progress.phase === 'scraped') return `Обработано ${progress.total} товаров`
    if (progress.phase === 'analyzing') return 'AI анализирует предложения...'
    return ''
  })()

  // Verdict config
  const verdictConfig = result ? {
    good: { bg: 'bg-emerald-500', text: 'Отличная цена!', Icon: CheckCircle2 },
    fair: { bg: 'bg-amber-500',   text: 'Средняя цена',  Icon: AlertTriangle },
    bad:  { bg: 'bg-red-500',     text: 'Завышенная цена', Icon: XCircle },
  }[result.verdict] : null

  // Price bar position for best_offer
  const bestOfferPos = result && result.stats.max > result.stats.min
    ? ((result.best_offer.price_num - result.stats.min) / (result.stats.max - result.stats.min)) * 100
    : 0

  return (
    <div className="min-h-[calc(100vh-7rem)]">
      {/* Header */}
      <section className="relative overflow-hidden">
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full opacity-20 blur-[120px] pointer-events-none"
          style={{ background: 'radial-gradient(var(--ac), transparent)' }}
        />
        <div className="container relative z-10 pt-10 pb-6">
          {!result && !loading && (
            <div className="text-center mb-6">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[var(--ac)] to-purple-500 flex items-center justify-center shadow-lg shadow-[var(--ac-glow)]">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold mb-2 tracking-tight">
                Анализ цены
              </h1>
              <p className="text-[var(--td)] text-sm max-w-md mx-auto">
                AI проверит, честная ли цена на товар по всем маркетплейсам
              </p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
            {/* Region switcher */}
            <div className="flex justify-center gap-2 mb-4">
              {([
                { key: 'BY' as const, flag: '🇧🇾', label: 'Беларусь (BYN)' },
                { key: 'RU' as const, flag: '🇷🇺', label: 'Россия (RUB)' },
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
                  <span className="hidden sm:inline">{r.label}</span>
                  <span className="sm:hidden">{r.key}</span>
                </button>
              ))}
            </div>

            {/* Search input */}
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--tm)] pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Например: iPhone 15 Pro 256GB"
                className="input pl-12 pr-36 py-4 text-base rounded-2xl bg-[var(--c1)] border-[var(--bd2)] w-full"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || query.trim().length < 2}
                className="absolute right-2 top-2 bottom-2 px-4 bg-[var(--ac)] text-white rounded-xl font-semibold text-sm hover:bg-[var(--ac2)] transition-all disabled:opacity-40 flex items-center gap-1.5"
              >
                {loading
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Sparkles className="w-4 h-4" />
                }
                <span className="hidden sm:inline">{loading ? 'Анализ...' : 'Анализировать'}</span>
              </button>
            </div>
          </form>
        </div>
      </section>

      <div className="container pb-10">
        {/* Query correction notice */}
        {correction && (
          <div className="max-w-2xl mx-auto mb-4 animate-fadeIn">
            <div className="card p-3 flex items-center gap-2 text-sm">
              <Sparkles className="w-4 h-4 text-[var(--ac)] shrink-0" />
              <span className="text-[var(--tm)]">Поняли как:</span>
              <span className="font-medium text-[var(--t)]">«{correction.corrected}»</span>
              <span className="text-[var(--tm)] text-xs ml-auto">
                вы искали: «{correction.original}»
              </span>
            </div>
          </div>
        )}

        {/* Progress */}
        {loading && (
          <div className="max-w-2xl mx-auto mb-8 animate-fadeIn">
            <div className="card p-5">
              <div className="flex items-center gap-3 mb-4">
                <Loader2 className="w-5 h-5 animate-spin text-[var(--ac)] shrink-0" />
                <p className="text-sm font-medium text-[var(--t)]">{phaseLabel || 'Загружаем...'}</p>
              </div>
              {progress.sources.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {progress.sources.map(src => {
                    const meta = MP_META[src] || { label: src, color: '#888' }
                    return (
                      <span
                        key={src}
                        className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border"
                        style={{
                          borderColor: `${meta.color}44`,
                          background: `${meta.color}11`,
                          color: meta.color,
                        }}
                      >
                        <Loader2 className="w-3 h-3 animate-spin" />
                        {meta.label}
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="max-w-2xl mx-auto mb-8 animate-fadeIn">
            <div className="p-5 rounded-2xl border border-red-500/30 bg-red-500/5">
              <div className="flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-red-400 mb-1">Не удалось выполнить анализ</p>
                  <p className="text-sm text-[var(--td)]">{error}</p>
                  {error.toLowerCase().includes('5') && (
                    <p className="text-xs text-[var(--tm)] mt-2">
                      Для анализа нужно минимум 5 предложений. Попробуйте более конкретный запрос или другой регион.
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => runAnalyze(query, region)}
                disabled={query.trim().length < 2}
                className="mt-4 btn-primary text-xs py-2"
              >
                Попробовать снова
              </button>
            </div>
          </div>
        )}

        {/* Result */}
        {result && !loading && (
          <div className="max-w-2xl mx-auto space-y-5 animate-fadeIn">
            {/* Verdict hero */}
            {verdictConfig && (
              <div className={`${verdictConfig.bg} rounded-2xl p-5 flex items-center justify-between shadow-lg`}>
                <div className="flex items-center gap-3">
                  <verdictConfig.Icon className="w-8 h-8 text-white shrink-0" />
                  <div>
                    <p className="text-xl font-extrabold text-white">{verdictConfig.text}</p>
                    <p className="text-white/70 text-sm mt-0.5 truncate max-w-[200px] sm:max-w-xs">
                      {result.query}
                    </p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-5xl font-black text-white leading-none">{result.score}</p>
                  <p className="text-white/70 text-xs mt-1">из 100</p>
                </div>
              </div>
            )}

            {/* Best offer */}
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-bold text-[var(--t)]">Лучшее предложение</h2>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-xl border-2 border-emerald-500/40 bg-emerald-500/5">
                {result.best_offer.image ? (
                  <img
                    src={proxyImage(result.best_offer.image)}
                    alt={result.best_offer.title}
                    className="w-16 h-16 object-contain bg-white rounded-xl p-1.5 shrink-0"
                  />
                ) : (
                  <div className="w-16 h-16 bg-white rounded-xl flex items-center justify-center shrink-0">
                    <Store className="w-7 h-7 text-gray-300" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[var(--t)] font-medium line-clamp-2 leading-snug">
                    {result.best_offer.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    {result.best_offer.shop && (
                      <span className="text-xs text-[var(--td)]">{result.best_offer.shop}</span>
                    )}
                    <MarketplaceBadge marketplace={result.best_offer.marketplace} />
                  </div>
                  <p className="text-lg font-extrabold text-emerald-400 mt-1">
                    {formatPrice(result.best_offer.price_num, result.best_offer.currency)}
                  </p>
                </div>
                <a
                  href={result.best_offer.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary text-xs py-2 px-3 shrink-0"
                >
                  Купить
                </a>
              </div>
            </div>

            {/* Price distribution bar */}
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-4 h-4 text-[var(--ac)]" />
                <h2 className="text-sm font-bold text-[var(--t)]">Распределение цен</h2>
              </div>

              <div className="relative">
                {/* Bar track */}
                <div className="h-3 rounded-full bg-gradient-to-r from-emerald-500/40 via-amber-500/40 to-red-500/40 relative">
                  {/* Best offer dot */}
                  <div
                    className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-[var(--ac)] border-2 border-white shadow-md"
                    style={{ left: `${Math.max(2, Math.min(98, bestOfferPos))}%` }}
                    title={`Лучшее: ${formatPrice(result.best_offer.price_num, result.currency)}`}
                  />
                </div>

                {/* Labels */}
                <div className="flex justify-between mt-3 text-xs text-[var(--td)]">
                  <div className="text-left">
                    <p className="font-semibold text-emerald-400">{formatPrice(result.stats.min, result.currency)}</p>
                    <p className="text-[10px]">мин</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-[var(--t)]">{formatPrice(result.stats.median, result.currency)}</p>
                    <p className="text-[10px]">медиана</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-red-400">{formatPrice(result.stats.max, result.currency)}</p>
                    <p className="text-[10px]">макс</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-3 pt-3 border-t border-[var(--bd)] text-xs text-[var(--tm)]">
                <span>{result.stats.count} предложений проанализировано</span>
                <span>разброс: ±{formatPrice(Math.round(result.stats.stdev), result.currency)}</span>
              </div>
            </div>

            {/* Red flags */}
            {result.red_flags.length > 0 && (
              <div className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <h2 className="text-sm font-bold text-[var(--t)]">На что обратить внимание</h2>
                </div>
                <div className="space-y-2">
                  {result.red_flags.map((flag, i) => (
                    <RedFlagItem key={i} flag={flag} />
                  ))}
                </div>
              </div>
            )}

            {/* Value analysis */}
            {result.value_analysis && (
              <div className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Info className="w-4 h-4 text-blue-400" />
                  <h2 className="text-sm font-bold text-[var(--t)]">Что получаешь за эти деньги</h2>
                </div>
                <div className="chat-md text-sm text-[var(--t2)] leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.value_analysis}</ReactMarkdown>
                </div>
              </div>
            )}

            {/* Alternatives */}
            {(result.alternatives.cheaper.length > 0 || result.alternatives.pricier.length > 0) && (
              <div>
                <h2 className="text-sm font-bold text-[var(--t)] mb-3">Альтернативы</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {/* Cheaper */}
                  {result.alternatives.cheaper.length > 0 && (
                    <div className="card p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <TrendingDown className="w-4 h-4 text-emerald-400" />
                        <h3 className="text-xs font-bold text-[var(--td)] uppercase tracking-wider">Дешевле</h3>
                      </div>
                      <div className="space-y-2">
                        {result.alternatives.cheaper.slice(0, 4).map((offer, i) => (
                          <OfferCard key={i} offer={offer} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Pricier */}
                  {result.alternatives.pricier.length > 0 && (
                    <div className="card p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <TrendingUp className="w-4 h-4 text-amber-400" />
                        <h3 className="text-xs font-bold text-[var(--td)] uppercase tracking-wider">Дороже, но может стоить</h3>
                      </div>
                      <div className="space-y-2">
                        {result.alternatives.pricier.slice(0, 4).map((offer, i) => (
                          <OfferCard key={i} offer={offer} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Footer */}
            <p className="text-center text-[10px] text-[var(--tm)] pb-2">
              AI-анализ от {new Date(result.generated_at).toLocaleString('ru-RU')}, регион {result.region}
            </p>
          </div>
        )}

        {/* Empty state */}
        {!loading && !result && !error && hydrated && (
          <div className="text-center py-12 max-w-md mx-auto">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--c2)] border border-[var(--bd)] flex items-center justify-center">
              <BarChart3 className="w-7 h-7 text-[var(--tm)]" />
            </div>
            <p className="text-[var(--td)] text-sm mb-6">
              Введите название товара — AI проанализирует цены со всех маркетплейсов и скажет, стоит ли покупать
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {['iPhone 15 Pro', 'Samsung Galaxy S24', 'MacBook Air M3', 'AirPods Pro 2'].map(q => (
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
    </div>
  )
}
