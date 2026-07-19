'use client'

import { useState, useEffect, useMemo, useRef } from 'react'
import { TrendingDown, Link2, Loader2, X, CheckCircle2, Circle, ExternalLink, Star, Sparkles, ShoppingBag, AlertCircle } from 'lucide-react'
import { createCheaperSearch, subscribeCheaper, type CheaperEvent, type CheaperOffer } from '@/lib/cheaper'
import { PiggyBank, RollingCart, HappyCoin, CheckCoin, CrossedTag, SadPanda } from '@/components/smart-icons'

// ————— Types —————
type ShopState = 'waiting' | 'checking' | 'done' | 'found'
interface Shop { domain: string; state: ShopState }
interface Offer {
  domain: string
  price: number
  productName: string
  rating?: number
  reviewCnt?: number
  url: string
  imgUrl?: string
  oldPrice?: number
  discountPct?: number
  discountEndTs?: number
  shopText?: string
  deliveryMethods?: string[]
  hasSplit?: boolean
  hasYaPay?: boolean
  isAdv?: boolean
}

// ————— URL detection —————
function detectUrl(input: string): { isUrl: boolean; domain?: string } {
  const trimmed = input.trim()
  if (!trimmed) return { isUrl: false }
  try {
    const u = new URL(trimmed.startsWith('http') ? trimmed : 'https://' + trimmed)
    if (!u.hostname.includes('.')) return { isUrl: false }
    return { isUrl: true, domain: u.hostname.replace(/^www\./, '') }
  } catch {
    return { isUrl: false }
  }
}

// ————— Page —————
export default function CheaperPage() {
  const [input, setInput] = useState('')
  const [stage, setStage] = useState<'idle' | 'analyzing' | 'searching' | 'results' | 'empty'>('idle')
  const [searchFinished, setSearchFinished] = useState(false)
  const resumingRef = useRef(false)
  const [shops, setShops] = useState<Shop[]>([])
  const [offers, setOffers] = useState<Offer[]>([])
  const [checkingIdx, setCheckingIdx] = useState(0)
  const [elapsedSec, setElapsedSec] = useState(0)
  const [productName, setProductName] = useState<string | null>(null)
  const [sourceOffer, setSourceOffer] = useState<Offer | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const wsRef = useRef<{ close: () => void } | null>(null)

  const detected = useMemo(() => detectUrl(input), [input])
  // Ref kept in sync with detected.domain so handleRealEvent (captured by WS once) always
  // sees the current value, including after resume when input is populated from snapshot.url
  const sourceDomainRef = useRef<string>('')
  useEffect(() => { sourceDomainRef.current = detected.domain || '' }, [detected.domain])

  const cleanup = () => {
    wsRef.current?.close()
    wsRef.current = null
  }

  const offerFromEvent = (data: CheaperOffer): Offer => ({
    domain: data.domain,
    price: data.price,
    productName: data.product_name || '',
    url: data.product_url || '#',
    imgUrl: data.img_url || undefined,
    rating: data.rating ?? undefined,
    reviewCnt: data.review_cnt ?? undefined,
    oldPrice: data.old_price ?? undefined,
    discountPct: data.discount_pct ?? undefined,
    discountEndTs: data.discount_end_ts ?? undefined,
    shopText: data.shop_text ?? undefined,
    deliveryMethods: data.delivery_methods ?? undefined,
    hasSplit: data.has_split ?? undefined,
    hasYaPay: data.has_yapay ?? undefined,
    isAdv: data.is_adv ?? undefined,
  })

  const handleRealEvent = (event: CheaperEvent) => {
    const d = event.data as Record<string, unknown> | undefined
    switch (event.type) {
      case 'snapshot': {
        const snap = d as unknown as { planned_shops?: { domain: string }[]; offers?: CheaperOffer[]; product_name?: string; status?: string; error?: string; url?: string; orig_domain?: string }
        // On resume, input state is empty — restore it from snapshot so detected.domain populates
        if (snap.url && !input) setInput(snap.url)
        // Resolve the source domain from the snapshot (resume case) or live `detected` (fresh search)
        const sourceDomain = (snap.orig_domain || '').replace(/^www\./, '').toLowerCase()
          || detected.domain
          || (snap.url ? (() => { try { return new URL(snap.url).hostname.replace(/^www\./, '') } catch { return '' } })() : '')
        if (snap.product_name) setProductName(snap.product_name)
        if (snap.planned_shops?.length) {
          setShops(snap.planned_shops.map(s => ({ domain: s.domain, state: 'waiting' as ShopState })))
          setStage('searching')
        }
        const allSnapOffers = snap.offers?.length ? snap.offers.map(offerFromEvent) : []
        const src = allSnapOffers.find(o => sourceDomain && o.domain === sourceDomain)
        if (src) {
          setSourceOffer(src)
          if (src.productName && !snap.product_name) setProductName(src.productName)
        }
        const snapOffers = allSnapOffers
          .filter(o => !sourceDomain || o.domain !== sourceDomain)
          .sort((a, b) => a.price - b.price)
        if (snapOffers.length) setOffers(snapOffers)

        if (snap.status === 'completed' || snap.status === 'failed' || snap.status === 'cancelled') {
          // If we're resuming from localStorage and the task is already finished,
          // don't show stale state — clear storage and stay idle.
          if (resumingRef.current) {
            resumingRef.current = false
            try { localStorage.removeItem('cheaper_task_id') } catch { /* ignore */ }
            setStage('idle')
            setOffers([])
            setShops([])
            cleanup()
            break
          }
          if (snap.error) setErrorMsg(snap.error)
          setStage(snapOffers.length ? 'results' : 'empty')
          setSearchFinished(true)
          if (snap.planned_shops?.length) {
            setShops(snap.planned_shops.map(s => ({
              domain: s.domain,
              state: snapOffers.some(o => o.domain === s.domain) ? 'found' : 'done' as ShopState,
            })))
          }
        } else {
          resumingRef.current = false
        }
        break
      }
      case 'started':
        setStage('analyzing')
        break
      case 'planned_shops': {
        const list = (d?.shops as string[]) || []
        setShops(list.map(domain => ({ domain, state: 'waiting' as ShopState })))
        setStage('searching')
        break
      }
      case 'product_name':
        if (d?.name) setProductName(d.name as string)
        break
      case 'offer': {
        const offer = offerFromEvent(d as unknown as CheaperOffer)
        const srcDom = sourceDomainRef.current
        // Source offer (user's own link) — use as "your product" card, don't list as cheaper
        if (srcDom && offer.domain === srcDom) {
          setSourceOffer(offer)
          if (offer.productName) setProductName(offer.productName)
          setShops(prev => prev.map(s => s.domain === offer.domain ? { ...s, state: 'done' } : s))
          break
        }
        setOffers(prev => {
          const filtered = prev.filter(o => o.domain !== offer.domain)
          return [...filtered, offer].sort((a, b) => a.price - b.price)
        })
        setShops(prev => {
          if (prev.some(s => s.domain === offer.domain)) {
            return prev.map(s => s.domain === offer.domain ? { ...s, state: 'found' } : s)
          }
          return [...prev, { domain: offer.domain, state: 'found' as ShopState }]
        })
        // Show results view as soon as the first cheaper offer arrives — no need to wait for 'done'
        setStage(prev => prev === 'idle' ? prev : 'results')
        break
      }
      case 'progress': {
        const checked = (d?.checked as number) ?? (d?.offers as number) ?? 0
        setCheckingIdx(checked)
        if (typeof d?.elapsed_sec === 'number') setElapsedSec(d.elapsed_sec)
        // Do NOT promote stage here. Backend's offer count includes the source-domain
        // offer, which we keep in `sourceOffer` (not in `offers[]`). Stage → 'results'
        // only when a genuine *cheaper* offer arrives (handled in 'offer' case).
        break
      }
      case 'dialog_closed':
        // Alisa's `update_time_last_read` fires between batches too, not only at end.
        // We used to mark search finished here, but that made the "still searching" banner
        // disappear while Alisa was actually still streaming. Only the backend's `done`
        // event (after stable_finish / hard_timeout) is authoritative.
        break
      case 'done': {
        const srcDom = sourceDomainRef.current
        const doneOffers = ((d?.offers as CheaperOffer[] | undefined) || [])
          .filter(o => !srcDom || o.domain !== srcDom)
          .map(offerFromEvent)
          .sort((a, b) => a.price - b.price)
        // Merge with already-received live offers — don't drop them if 'done' payload is stale.
        setOffers(prev => {
          const byDomain = new Map<string, Offer>()
          for (const o of [...prev, ...doneOffers]) {
            const existing = byDomain.get(o.domain)
            if (!existing || o.price < existing.price) byDomain.set(o.domain, o)
          }
          return Array.from(byDomain.values()).sort((a, b) => a.price - b.price)
        })
        setShops(prev => prev.map(s => s.state === 'waiting' || s.state === 'checking'
          ? { ...s, state: doneOffers.some(o => o.domain === s.domain) ? 'found' : 'done' }
          : s))
        // Use functional setStage so we base the decision on *merged* offers count,
        // not the possibly-stale doneOffers or prior 'empty' state.
        setStage(prev => {
          const hasAny = prev === 'results' || doneOffers.length > 0 || offers.length > 0
          return hasAny ? 'results' : 'empty'
        })
        setSearchFinished(true)
        try { localStorage.removeItem('cheaper_task_id') } catch { /* ignore */ }
        cleanup()
        break
      }
      case 'error':
        setErrorMsg((d?.message as string) || 'Поиск завершился с ошибкой')
        setStage('empty')
        cleanup()
        break
    }
  }

  const startSearch = async () => {
    if (!detected.isUrl) return
    cleanup()
    setOffers([])
    setShops([])
    setCheckingIdx(0)
    setElapsedSec(0)
    setProductName(null)
    setSourceOffer(null)
    setErrorMsg(null)
    setSearchFinished(false)
    setStage('analyzing')

    try {
      const { task_id } = await createCheaperSearch(input.trim())
      try { localStorage.setItem('cheaper_task_id', task_id) } catch { /* ignore */ }
      wsRef.current = subscribeCheaper(task_id, handleRealEvent, () => {
        // WS dropped — don't break: treat as silent timeout, user can reset
      })
    } catch (err) {
      console.warn('Search failed:', err)
      setErrorMsg('Не удалось запустить поиск. Попробуйте ещё раз.')
      setStage('empty')
    }
  }

  // Resume an in-flight search on mount (localStorage survives reloads/tab-close)
  useEffect(() => {
    let taskId: string | null = null
    try { taskId = localStorage.getItem('cheaper_task_id') } catch { /* ignore */ }
    if (!taskId) return
    resumingRef.current = true
    setStage('analyzing')
    setSearchFinished(false)
    wsRef.current = subscribeCheaper(taskId, handleRealEvent)
    // on unmount cleans up
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => () => cleanup(), [])

  const reset = () => {
    cleanup()
    setStage('idle')
    setInput('')
    setOffers([])
    setShops([])
    setProductName(null)
    setSourceOffer(null)
    setErrorMsg(null)
    setSearchFinished(false)
    try { localStorage.removeItem('cheaper_task_id') } catch { /* ignore */ }
  }

  const foundCount = offers.length
  const plannedCount = shops.length
  const currentShop = shops[checkingIdx]?.domain

  return (
    <main className="min-h-[calc(100vh-3.5rem)] container py-10 md:py-16">
      {/* Hero */}
      {stage === 'idle' && (
        <div className="max-w-2xl mx-auto text-center mb-10 animate-fadeIn">
          <PiggyBank className="mb-2" />
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[var(--bd)] text-xs text-[var(--tm)] mb-5">
            <Sparkles className="w-3.5 h-3.5 text-[var(--ac)]" />
            <span>Работает на AI-агенте</span>
          </div>
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight mb-4">
            Найдём <span className="gradient-text">дешевле</span><br />в десятках магазинов
          </h1>
          <p className="text-[var(--td)] text-base md:text-lg mb-8 max-w-xl mx-auto">
            Вставьте ссылку на любой товар — проверим цену на ту же модель во всех подходящих магазинах России.
          </p>
        </div>
      )}

      {/* Smart input */}
      {stage === 'idle' && (
        <div className="max-w-2xl mx-auto">
          <div className="card p-3 md:p-4">
            <div className="flex flex-col md:flex-row gap-2.5 items-stretch">
              <div className="relative flex-1">
                <Link2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--tm)]" />
                <input
                  type="url"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && startSearch()}
                  placeholder="Вставьте ссылку на товар (например, с ozon.ru)"
                  className="w-full bg-[var(--c2)] border border-[var(--bd)] rounded-lg pl-10 pr-3 h-11 text-sm outline-none focus:border-[var(--ac)] transition-colors"
                  autoFocus
                />
              </div>
              <button
                onClick={startSearch}
                disabled={!detected.isUrl}
                className="btn-primary h-11 px-5 text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
              >
                <TrendingDown className="w-4 h-4" />
                Найти дешевле
              </button>
            </div>

            {/* URL preview */}
            {input.trim() && (
              <div className="mt-3 text-xs flex items-center gap-2 px-1">
                {detected.isUrl ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                    <span className="text-[var(--td)]">Магазин определён: <span className="text-[var(--t)] font-semibold">{detected.domain}</span></span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                    <span className="text-[var(--tm)]">Похоже, это не ссылка — нужна прямая ссылка на товар</span>
                  </>
                )}
              </div>
            )}

          </div>

          {/* Instructions section */}
          <InstructionsSection />
        </div>
      )}

      {/* Loading / searching modal */}
      {(stage === 'analyzing' || stage === 'searching') && (
        <div className="max-w-3xl mx-auto animate-fadeIn">
          <div className="card p-5 md:p-7">
            <div className="flex items-start justify-between mb-5">
              <div className="flex-1 min-w-0">
                <div className="text-xs text-[var(--tm)] mb-1">Ищем дешевле для</div>
                <div className="text-sm text-[var(--t)] font-semibold truncate">{productName || 'Определяем товар…'}</div>
                <div className="text-xs text-[var(--td)] mt-1">{detected.domain}</div>
              </div>
              <button onClick={reset} className="text-[var(--tm)] hover:text-[var(--t)] transition-colors ml-3">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Source product card — shown as soon as Alisa recognizes the item */}
            {sourceOffer && (
              <div className="mb-5 p-3 rounded-lg bg-[var(--c2)] border border-[var(--bd)] flex gap-3 items-start animate-fadeIn">
                {sourceOffer.imgUrl && (
                  <div className="w-14 h-14 shrink-0 rounded bg-[var(--c)] overflow-hidden">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={sourceOffer.imgUrl.startsWith('//') ? 'https:' + sourceOffer.imgUrl : sourceOffer.imgUrl}
                      alt=""
                      className="w-full h-full object-contain"
                    />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] uppercase tracking-wider text-[var(--tm)] mb-0.5">Ваш товар</div>
                  <div className="text-sm text-[var(--t)] line-clamp-2 leading-snug">{sourceOffer.productName || productName}</div>
                  <div className="flex items-center gap-2 mt-1.5 text-xs">
                    <span className="font-extrabold text-[var(--t)] text-base">{sourceOffer.price.toLocaleString('ru-RU')}₽</span>
                    <span className="text-[var(--tm)]">·</span>
                    <span className="text-[var(--td)]">{sourceOffer.shopText || sourceOffer.domain}</span>
                    {sourceOffer.rating && (
                      <>
                        <span className="text-[var(--tm)]">·</span>
                        <span className="flex items-center gap-0.5 text-[var(--tm)]">
                          <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                          {sourceOffer.rating.toFixed(1)}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Progress header */}
            {stage === 'analyzing' ? (
              <div className="flex flex-col items-center gap-2 py-4 text-sm text-[var(--td)]">
                <RollingCart />
                <span>Анализируем товар и подбираем магазины...</span>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-3 text-sm">
                  <span className="text-[var(--td)]">
                    Обходим <span className="text-[var(--t)] font-semibold">{plannedCount}</span> магазинов
                    {foundCount > 0 && <> · нашли дешевле: <span className="text-green-500 font-semibold">{foundCount}</span></>}
                  </span>
                  <span className="text-xs text-[var(--tm)] flex items-center gap-1.5">
                    <Loader2 className="w-3 h-3 animate-spin text-[var(--ac)]" />
                    {Math.floor(elapsedSec / 60)}:{String(elapsedSec % 60).padStart(2, '0')} / ~15:00
                  </span>
                </div>

                {/* Progress bar — by elapsed time, capped at 95% so it never looks "done" while still running */}
                <div className="h-1.5 bg-[var(--c2)] rounded-full overflow-hidden mb-6">
                  <div
                    className="h-full bg-[var(--ac)] transition-all duration-500"
                    style={{ width: `${Math.min(95, (elapsedSec / 900) * 100)}%` }}
                  />
                </div>

                {/* Shop grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 mb-6">
                  {shops.map(shop => (
                    <ShopTile key={shop.domain} shop={shop} />
                  ))}
                </div>

                {/* Live offer feed */}
                {offers.length > 0 && (
                  <div className="border-t border-[var(--bd)] pt-4">
                    <div className="text-xs text-[var(--tm)] mb-2">Найденные предложения:</div>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {offers.slice(0, 5).map(o => (
                        <a key={o.domain} href={o.url} target="_blank" rel="noopener"
                           className="flex items-center justify-between text-sm px-2 py-1.5 rounded bg-[var(--c2)] hover:bg-[var(--c3)] transition-colors">
                          <span className="text-[var(--t)] font-semibold">{o.price}₽</span>
                          <span className="text-[var(--td)] text-xs flex items-center gap-1.5">
                            {o.domain}
                            <ExternalLink className="w-3 h-3" />
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

          </div>
        </div>
      )}

      {/* Results */}
      {stage === 'results' && (
        <ResultsView offers={offers} productName={productName || ''} onReset={reset} plannedCount={plannedCount} searching={!searchFinished} elapsedSec={elapsedSec} sourceOffer={sourceOffer} />
      )}

      {/* Empty (no cheaper found) */}
      {stage === 'empty' && (
        <EmptyView plannedCount={plannedCount} origDomain={detected.domain || ''} errorMsg={errorMsg} onReset={reset} />
      )}
    </main>
  )
}

// ————— Subcomponents —————
function ShopTile({ shop }: { shop: Shop }) {
  const iconColor = {
    waiting:  'text-[var(--tm)]',
    checking: 'text-[var(--ac)]',
    done:     'text-[var(--td)]',
    found:    'text-green-500',
  }[shop.state]

  const bg = shop.state === 'found' ? 'bg-green-500/10 border-green-500/30'
    : shop.state === 'checking' ? 'bg-[var(--ac)]/10 border-[var(--ac)]/30'
    : 'bg-[var(--c2)] border-[var(--bd)]'

  return (
    <div className={`flex items-center gap-2 px-2.5 py-2 rounded-md border text-xs transition-all ${bg}`}>
      {shop.state === 'checking' ? <Loader2 className={`w-3.5 h-3.5 animate-spin shrink-0 ${iconColor}`} />
       : shop.state === 'found'  ? <CheckCircle2 className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
       : shop.state === 'done'   ? <Circle className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
       :                           <Circle className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />}
      <span className={`truncate ${shop.state === 'found' ? 'text-[var(--t)] font-semibold' : 'text-[var(--td)]'}`}>{shop.domain}</span>
    </div>
  )
}

function ResultsView({ offers, productName, plannedCount, onReset, searching, elapsedSec, sourceOffer }:
  { offers: Offer[]; productName: string; plannedCount: number; onReset: () => void; searching: boolean; elapsedSec: number; sourceOffer: Offer | null }) {
  if (!offers.length) {
    return (
      <div className="py-16 text-center text-[var(--td)]">
        <p className="mb-4">Не нашли вариантов дешевле</p>
        <button onClick={onReset} className="text-[var(--t)] underline">Попробовать ещё раз</button>
      </div>
    )
  }
  const best = offers[0]
  // Prefer "экономия vs твой магазин" when we know the source price (same semantics as Alisa).
  // Fall back to max-min spread across competitors only if we never captured source.
  const hasSource = !!(sourceOffer && sourceOffer.price > best.price)
  const baseline = hasSource ? sourceOffer!.price : Math.max(...offers.map(o => o.price))
  const savings = Math.max(0, baseline - best.price)
  const savingsPct = baseline > 0 ? Math.round((savings / baseline) * 100) : 0
  const savingsLabel = hasSource
    ? `дешевле, чем на ${sourceOffer!.domain}`
    : `разброс цен ${savingsPct}%`

  return (
    <div className="max-w-4xl mx-auto animate-fadeIn">
      {/* Top: ETA plaque */}
      {searching && (
        <div className="card p-3 mb-4 bg-[var(--ac)]/5 border-[var(--ac)]/30 flex items-center gap-3">
          <Loader2 className="w-4 h-4 animate-spin text-[var(--ac)] shrink-0" />
          <div className="text-sm text-[var(--t)] font-semibold">
            Ищем лучшую цену — это занимает примерно 10 минут
          </div>
        </div>
      )}

      {/* Hero result */}
      <div className="card p-6 md:p-8 mb-6 bg-gradient-to-br from-[var(--ac)]/10 to-transparent border-[var(--ac)]/30">
        <div className="flex items-center gap-2 text-sm text-[var(--ac)] mb-2">
          <Sparkles className="w-4 h-4" />
          <span className="font-semibold">
            {searching ? (savings > 0 ? 'Пока лучшее предложение — поиск ещё идёт' : 'Пока ничего дешевле не нашли — продолжаем') : 'Лучшая цена найдена'}
          </span>
        </div>
        <div className="flex flex-col md:flex-row md:items-end gap-4 md:gap-8">
          <div>
            <div className="text-4xl md:text-5xl font-extrabold">
              <span className="text-green-500">{best.price.toLocaleString('ru-RU')}₽</span>
            </div>
            {productName && <div className="text-sm text-[var(--td)] mt-1">{productName}</div>}
          </div>
          {savings > 0 && (
            <div className="md:ml-auto text-right flex items-center gap-3">
              {!searching && <HappyCoin />}
              <div>
                <div className="text-2xl font-extrabold text-green-500">−{savings.toLocaleString('ru-RU')}₽</div>
                <div className="text-xs text-[var(--tm)]">{savingsLabel}</div>
              </div>
            </div>
          )}
        </div>
        <div className="mt-5 flex flex-wrap gap-2 items-center text-xs text-[var(--tm)]">
          <span>
            {searching
              ? <>Уже нашли в <span className="text-[var(--t)] font-semibold">{offers.length}</span> из {plannedCount} магазинов · проверка продолжается</>
              : <>Проверили {plannedCount} магазинов · нашли предложения в {offers.length}</>}
          </span>
          <button onClick={onReset} className="ml-auto text-[var(--ac)] hover:underline">Новый поиск</button>
        </div>
      </div>

      {/* Top 3 */}
      <h2 className="text-lg font-bold mb-3 flex items-center gap-2">
        <span className="text-xl">🏆</span>
        {searching
          ? (offers.length >= 3 ? <>Пока топ-3 <span className="text-xs font-normal text-[var(--tm)]">· поиск продолжается</span></> : <>Найденные варианты <span className="text-xs font-normal text-[var(--tm)]">· поиск продолжается</span></>)
          : <>Топ-3 предложения</>}
      </h2>
      <div className="grid md:grid-cols-3 gap-3 mb-8">
        {offers.slice(0, 3).map((o, i) => <TopOfferCard key={o.domain} offer={o} rank={i + 1} />)}
      </div>

      {/* Rest */}
      {offers.length > 3 && (
        <>
          <h2 className="text-sm font-bold mb-3 text-[var(--td)]">Остальные магазины</h2>
          <div className="card p-2 divide-y divide-[var(--bd)]">
            {offers.slice(3).map(o => (
              <div key={o.domain} className="flex items-center gap-3 px-3 py-2.5 hover:bg-[var(--c2)] transition-colors">
                <ShoppingBag className="w-4 h-4 text-[var(--tm)] shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-[var(--t)] font-semibold truncate">{o.domain}</div>
                  <div className="text-xs text-[var(--tm)] truncate">{o.productName}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-extrabold">{o.price}₽</div>
                </div>
                <a href={o.url} target="_blank" rel="noopener" className="text-[var(--ac)] hover:scale-110 transition-transform">
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            ))}
          </div>
        </>
      )}

      {searching && (
        <div className="mt-6 card p-3 bg-[var(--ac)]/5 border-[var(--ac)]/30 flex items-center gap-3">
          <Loader2 className="w-4 h-4 animate-spin text-[var(--ac)] shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-sm text-[var(--t)] font-semibold">Поиск ещё идёт — можете вернуться позже</div>
            <div className="text-xs text-[var(--tm)] mt-0.5">
              Прошло {Math.floor(elapsedSec / 60)}:{String(elapsedSec % 60).padStart(2, '0')} · результаты сохранятся автоматически
            </div>
          </div>
        </div>
      )}

      <div className="mt-8 text-xs text-[var(--tm)] text-center">
        Цены актуальны на момент проверки. Доставка не учитывается. Сохраняйте поиск, чтобы отследить изменения.
      </div>
    </div>
  )
}

function TopOfferCard({ offer, rank }: { offer: Offer; rank: number }) {
  const medals = ['🥇', '🥈', '🥉']
  const img = offer.imgUrl ? (offer.imgUrl.startsWith('//') ? 'https:' + offer.imgUrl : offer.imgUrl) : null
  const priceLabel = offer.price.toLocaleString('ru-RU')
  const oldLabel = offer.oldPrice ? offer.oldPrice.toLocaleString('ru-RU') : null
  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-start gap-3">
        {img && (
          <div className="w-16 h-16 shrink-0 rounded bg-[var(--c2)] overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={img} alt="" className="w-full h-full object-contain" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 text-xs text-[var(--tm)] mb-0.5">
            <span>{medals[rank - 1]}</span>
            <span className="font-semibold text-[var(--t)] truncate">{offer.shopText || offer.domain}</span>
            {offer.isAdv && <span className="px-1 py-0.5 text-[10px] rounded bg-[var(--c2)] text-[var(--tm)]">Промо</span>}
          </div>
          <div className="text-xs text-[var(--td)] line-clamp-2">{offer.productName}</div>
        </div>
      </div>

      <div>
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="text-2xl font-extrabold text-[var(--t)]">{priceLabel}₽</span>
          {offer.discountPct && offer.discountPct > 0 && (
            <span className="px-1.5 py-0.5 text-xs font-bold rounded bg-red-500/15 text-red-500">
              −{offer.discountPct}%
            </span>
          )}
        </div>
        {oldLabel && (
          <div className="text-xs text-[var(--tm)] line-through mt-0.5">{oldLabel}₽</div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--tm)]">
        {offer.rating && (
          <span className="flex items-center gap-0.5">
            <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
            <span className="text-[var(--t)] font-semibold">{offer.rating.toFixed(1)}</span>
            {offer.reviewCnt ? <span>({offer.reviewCnt > 999 ? (offer.reviewCnt / 1000).toFixed(1) + 'K' : offer.reviewCnt})</span> : null}
          </span>
        )}
        {offer.hasSplit && <span className="text-[var(--t)]">Сплит</span>}
        {offer.hasYaPay && <span className="text-[var(--ac)]">Я.Пэй</span>}
        {offer.deliveryMethods?.includes('COURIER') && <span>Курьер</span>}
        {offer.deliveryMethods?.includes('PICKUP_POINT') && <span>Самовывоз</span>}
      </div>

      <a href={offer.url} target="_blank" rel="noopener" className="btn-primary h-9 text-xs inline-flex items-center justify-center gap-1.5">
        В магазин <ExternalLink className="w-3.5 h-3.5" />
      </a>
    </div>
  )
}

function EmptyView({ plannedCount, origDomain, errorMsg, onReset }:
  { plannedCount: number; origDomain: string; errorMsg: string | null; onReset: () => void }) {
  return (
    <div className="max-w-xl mx-auto animate-fadeIn">
      <div className="card p-8 text-center">
        <SadPanda className="mb-5" />
        <h2 className="text-xl font-bold mb-2">{errorMsg ? 'Такой товар пока не умеем искать' : 'Дешевле не нашли'}</h2>
        <p className="text-sm text-[var(--td)] mb-5">
          {errorMsg
            ? <>Попробуйте ссылку на другой товар — электронику, технику, аксессуары, товары для дома.</>
            : <>Проверили {plannedCount} магазинов — лучшего предложения не нашлось{origDomain && <> по сравнению с <span className="text-[var(--t)] font-semibold">{origDomain}</span></>}.</>}
        </p>
        <button onClick={onReset} className="btn-primary h-10 px-5 text-sm">Новый поиск</button>
      </div>
    </div>
  )
}

function InstructionsSection() {
  return (
    <div className="mt-12 grid md:grid-cols-2 gap-4">
      <div className="card p-5">
        <div className="text-sm font-bold mb-3 text-green-500 flex items-center gap-2"><CheckCoin />Хорошо ищется</div>
        <ul className="space-y-1.5 text-sm text-[var(--td)]">
          <li>· Электроника и бытовая техника</li>
          <li>· Смартфоны, ноутбуки, аксессуары</li>
          <li>· Инструмент, DIY, товары для дома</li>
          <li>· Детские товары и игрушки</li>
          <li>· Продукты и FMCG</li>
        </ul>
      </div>
      <div className="card p-5">
        <div className="text-sm font-bold mb-3 text-amber-500 flex items-center gap-2"><CrossedTag />Не ищется</div>
        <ul className="space-y-1.5 text-sm text-[var(--td)]">
          <li>· Одежда, обувь (размеры)</li>
          <li>· Автомобили, автозапчасти</li>
          <li>· Услуги и сертификаты</li>
          <li>· Товары 18+</li>
          <li>· Скоропортящиеся продукты</li>
        </ul>
      </div>
    </div>
  )
}
