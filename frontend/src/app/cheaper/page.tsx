'use client'

import { useState, useEffect, useMemo, useRef } from 'react'
import { TrendingDown, Link2, Loader2, X, CheckCircle2, Circle, ExternalLink, Star, Sparkles, ShoppingBag, AlertCircle } from 'lucide-react'
import { createCheaperSearch, subscribeCheaper, type CheaperEvent, type CheaperOffer } from '@/lib/cheaper'

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
}

// ————— Mock data (based on real Alisa WS measurement 2026-04-14, pudding category) —————
const MOCK_URL = 'https://www.ozon.ru/product/puding-solenaya-karamel-4-7-200-g-grand-dessert-154340531/'
const MOCK_ORIG_PRICE = 223
const MOCK_PRODUCT_NAME = 'Пудинг "Солёная карамель" 4.7%, 200г, Grand Dessert'

const MOCK_PLANNED_SHOPS = [
  'ozon.ru', 'wildberries.ru', 'market.yandex.ru',
  'kuper.ru', 'lavka.yandex.ru', 'lenta.com', 'auchan.ru',
  'perekrestok.ru', 'dixy.ru', '5ka.ru', 'vkusvill.ru', 'okeydostavka.ru',
  'vodovoz.ru', 'av.ru', '3259404.ru', 'aliexpress.com', 'chipdip.ru',
  'onlinetrade.ru', 'partsdirect.ru', 'nbdoc.ru',
]

const MOCK_OFFERS: Offer[] = [
  { domain: 'kuper.ru',         price: 100, productName: 'Grand Dessert Солёная карамель 200г', rating: 4.8, reviewCnt: 342, url: '#' },
  { domain: 'lavka.yandex.ru',  price: 103, productName: 'Пудинг Grand Dessert Солёная карамель', rating: 4.7, reviewCnt: 891, url: '#' },
  { domain: 'auchan.ru',        price: 110, productName: 'Пудинг Солёная Карамель Grand Dessert 200 г', rating: 4.5, reviewCnt: 128, url: '#' },
  { domain: 'lenta.com',        price: 110, productName: 'Grand Dessert пудинг карамель 200 г', rating: 4.6, reviewCnt: 201, url: '#' },
  { domain: 'perekrestok.ru',   price: 118, productName: 'Пудинг Grand Dessert карамель 200г', rating: 4.5, reviewCnt: 567, url: '#' },
  { domain: 'dixy.ru',          price: 124, productName: 'Пудинг Grand Dessert 200г', rating: 4.4, reviewCnt: 89, url: '#' },
  { domain: '5ka.ru',           price: 127, productName: 'Grand Dessert Солёная карамель 200 г', rating: 4.6, reviewCnt: 412, url: '#' },
  { domain: 'vkusvill.ru',      price: 134, productName: 'Пудинг карамельный Grand Dessert', rating: 4.7, reviewCnt: 256, url: '#' },
  { domain: 'okeydostavka.ru',  price: 144, productName: 'Grand Dessert пудинг 200 г', rating: 4.3, reviewCnt: 67, url: '#' },
]

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
  const [shops, setShops] = useState<Shop[]>([])
  const [offers, setOffers] = useState<Offer[]>([])
  const [checkingIdx, setCheckingIdx] = useState(0)
  const [mode, setMode] = useState<'real' | 'mock'>('real')
  const [productName, setProductName] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const wsRef = useRef<{ close: () => void } | null>(null)
  const mockTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const detected = useMemo(() => detectUrl(input), [input])

  const cleanup = () => {
    wsRef.current?.close()
    wsRef.current = null
    if (mockTimerRef.current) { clearInterval(mockTimerRef.current); mockTimerRef.current = null }
  }

  const offerFromEvent = (data: CheaperOffer): Offer => ({
    domain: data.domain,
    price: data.price,
    productName: data.product_name || '',
    url: data.product_url || '#',
    imgUrl: data.img_url || undefined,
  })

  const handleRealEvent = (event: CheaperEvent) => {
    const d = event.data as Record<string, unknown> | undefined
    switch (event.type) {
      case 'snapshot': {
        const snap = d as unknown as { planned_shops?: { domain: string }[]; offers?: CheaperOffer[]; product_name?: string }
        if (snap.product_name) setProductName(snap.product_name)
        if (snap.planned_shops?.length) {
          setShops(snap.planned_shops.map(s => ({ domain: s.domain, state: 'waiting' as ShopState })))
          setStage('searching')
        }
        if (snap.offers?.length) {
          setOffers(snap.offers.map(offerFromEvent).sort((a, b) => a.price - b.price))
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
        setOffers(prev => {
          const filtered = prev.filter(o => o.domain !== offer.domain)
          return [...filtered, offer].sort((a, b) => a.price - b.price)
        })
        setShops(prev => prev.map(s => s.domain === offer.domain ? { ...s, state: 'found' } : s))
        break
      }
      case 'progress': {
        const checked = (d?.checked as number) ?? (d?.offers as number) ?? 0
        setCheckingIdx(checked)
        break
      }
      case 'done': {
        setShops(prev => prev.map(s => s.state === 'waiting' || s.state === 'checking'
          ? { ...s, state: (d?.offers as CheaperOffer[] | undefined)?.some(o => o.domain === s.domain) ? 'found' : 'done' }
          : s))
        setStage((d?.offers as CheaperOffer[] | undefined)?.length || offers.length ? 'results' : 'empty')
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

  const startMockSimulation = () => {
    setMode('mock')
    setStage('analyzing')
    setTimeout(() => {
      setShops(MOCK_PLANNED_SHOPS.map(d => ({ domain: d, state: 'waiting' as ShopState })))
      setStage('searching')
      let idx = 0
      mockTimerRef.current = setInterval(() => {
        setShops(prev => prev.map((s, i) => {
          if (i < idx) return { ...s, state: MOCK_OFFERS.find(o => o.domain === s.domain) ? 'found' : 'done' }
          if (i === idx) return { ...s, state: 'checking' }
          return s
        }))
        const current = MOCK_PLANNED_SHOPS[idx]
        const match = MOCK_OFFERS.find(o => o.domain === current)
        if (match) setOffers(prev => [...prev, match].sort((a, b) => a.price - b.price))
        setCheckingIdx(idx)
        idx++
        if (idx >= MOCK_PLANNED_SHOPS.length) {
          if (mockTimerRef.current) { clearInterval(mockTimerRef.current); mockTimerRef.current = null }
          setTimeout(() => {
            setShops(prev => prev.map(s => ({ ...s, state: MOCK_OFFERS.find(o => o.domain === s.domain) ? 'found' : 'done' })))
            setStage(MOCK_OFFERS.length ? 'results' : 'empty')
          }, 500)
        }
      }, 700)
    }, 1800)
  }

  const startSearch = async () => {
    if (!detected.isUrl) return
    cleanup()
    setOffers([])
    setShops([])
    setCheckingIdx(0)
    setProductName(null)
    setErrorMsg(null)
    setStage('analyzing')

    try {
      const { task_id } = await createCheaperSearch(input.trim())
      setMode('real')
      wsRef.current = subscribeCheaper(task_id, handleRealEvent, () => {
        // WS dropped — don't break: treat as silent timeout, user can reset
      })
    } catch (err) {
      console.warn('Backend unavailable, falling back to mock:', err)
      startMockSimulation()
    }
  }

  useEffect(() => () => cleanup(), [])

  const reset = () => {
    cleanup()
    setStage('idle')
    setInput('')
    setOffers([])
    setShops([])
    setProductName(null)
    setErrorMsg(null)
  }

  const foundCount = offers.length
  const plannedCount = shops.length
  const currentShop = shops[checkingIdx]?.domain

  return (
    <main className="min-h-[calc(100vh-3.5rem)] container py-10 md:py-16">
      {/* Hero */}
      {stage === 'idle' && (
        <div className="max-w-2xl mx-auto text-center mb-10 animate-fadeIn">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-amber-500/40 bg-amber-500/10 text-xs text-amber-400 mb-3">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>β-версия · если бэкенд недоступен — покажем реальный замер по пудингу</span>
          </div>
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

            {/* Demo hint */}
            <button
              onClick={() => setInput(MOCK_URL)}
              className="mt-2 text-xs text-[var(--tm)] hover:text-[var(--ac)] transition-colors px-1"
            >
              Попробовать на примере →
            </button>
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
              <div>
                <div className="text-xs text-[var(--tm)] mb-1">Ищем дешевле для</div>
                <div className="text-sm text-[var(--t)] font-semibold truncate max-w-[500px]">{MOCK_PRODUCT_NAME}</div>
                <div className="text-xs text-[var(--td)] mt-1">Исходная цена: <span className="text-[var(--t)] font-semibold">{MOCK_ORIG_PRICE}₽</span> · {detected.domain}</div>
              </div>
              <button onClick={reset} className="text-[var(--tm)] hover:text-[var(--t)] transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Progress header */}
            {stage === 'analyzing' ? (
              <div className="flex items-center gap-3 py-6 text-sm text-[var(--td)]">
                <Loader2 className="w-4 h-4 animate-spin text-[var(--ac)]" />
                <span>Анализируем товар и подбираем магазины...</span>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-3 text-sm">
                  <span className="text-[var(--td)]">
                    Проверено <span className="text-[var(--t)] font-semibold">{Math.min(checkingIdx + 1, plannedCount)}</span> из {plannedCount}
                    {foundCount > 0 && <> · нашли дешевле: <span className="text-green-500 font-semibold">{foundCount}</span></>}
                  </span>
                  {currentShop && (
                    <span className="text-xs text-[var(--tm)] flex items-center gap-1.5">
                      <Loader2 className="w-3 h-3 animate-spin text-[var(--ac)]" />
                      {currentShop}
                    </span>
                  )}
                </div>

                {/* Progress bar */}
                <div className="h-1.5 bg-[var(--c2)] rounded-full overflow-hidden mb-6">
                  <div
                    className="h-full bg-[var(--ac)] transition-all duration-500"
                    style={{ width: `${((checkingIdx + 1) / plannedCount) * 100}%` }}
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
                        <div key={o.domain} className="flex items-center justify-between text-sm px-2 py-1.5 rounded bg-[var(--c2)]">
                          <span className="text-[var(--t)] font-semibold">{o.price}₽</span>
                          <span className="text-[var(--td)] text-xs">{o.domain}</span>
                          <span className="text-green-500 text-xs font-semibold">
                            −{Math.round((1 - o.price / MOCK_ORIG_PRICE) * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            <div className="mt-5 pt-4 border-t border-[var(--bd)] text-xs text-[var(--tm)] flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Можете закрыть вкладку — пришлём результат в Telegram</span>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {stage === 'results' && (
        <ResultsView offers={offers} origPrice={MOCK_ORIG_PRICE} productName={MOCK_PRODUCT_NAME} onReset={reset} plannedCount={plannedCount} />
      )}

      {/* Empty (no cheaper found) */}
      {stage === 'empty' && (
        <EmptyView plannedCount={plannedCount} origPrice={MOCK_ORIG_PRICE} origDomain={detected.domain || 'ozon.ru'} onReset={reset} />
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

function ResultsView({ offers, origPrice, productName, plannedCount, onReset }:
  { offers: Offer[]; origPrice: number; productName: string; plannedCount: number; onReset: () => void }) {
  const best = offers[0]
  const savings = origPrice - best.price
  const savingsPct = Math.round((savings / origPrice) * 100)

  return (
    <div className="max-w-4xl mx-auto animate-fadeIn">
      {/* Hero result */}
      <div className="card p-6 md:p-8 mb-6 bg-gradient-to-br from-[var(--ac)]/10 to-transparent border-[var(--ac)]/30">
        <div className="flex items-center gap-2 text-sm text-[var(--ac)] mb-2">
          <Sparkles className="w-4 h-4" />
          <span className="font-semibold">Лучшая цена найдена</span>
        </div>
        <div className="flex flex-col md:flex-row md:items-end gap-4 md:gap-8">
          <div>
            <div className="text-4xl md:text-5xl font-extrabold">
              <span className="text-green-500">{best.price}₽</span>
              <span className="text-base text-[var(--td)] line-through ml-3">{origPrice}₽</span>
            </div>
            <div className="text-sm text-[var(--td)] mt-1">{productName}</div>
          </div>
          <div className="md:ml-auto text-right">
            <div className="text-2xl font-extrabold text-green-500">−{savings}₽</div>
            <div className="text-xs text-[var(--tm)]">выгода {savingsPct}%</div>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-2 items-center text-xs text-[var(--tm)]">
          <span>Проверили {plannedCount} магазинов · нашли дешевле в {offers.length}</span>
          <button onClick={onReset} className="ml-auto text-[var(--ac)] hover:underline">Новый поиск</button>
        </div>
      </div>

      {/* Top 3 */}
      <h2 className="text-lg font-bold mb-3 flex items-center gap-2">
        <span className="text-xl">🏆</span> Топ-3 предложения
      </h2>
      <div className="grid md:grid-cols-3 gap-3 mb-8">
        {offers.slice(0, 3).map((o, i) => <TopOfferCard key={o.domain} offer={o} rank={i + 1} origPrice={origPrice} />)}
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
                  <div className="text-xs text-green-500">−{Math.round((1 - o.price / origPrice) * 100)}%</div>
                </div>
                <a href={o.url} target="_blank" rel="noopener" className="text-[var(--ac)] hover:scale-110 transition-transform">
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="mt-8 text-xs text-[var(--tm)] text-center">
        Цены актуальны на момент проверки. Доставка не учитывается. Сохраняйте поиск, чтобы отследить изменения.
      </div>
    </div>
  )
}

function TopOfferCard({ offer, rank, origPrice }: { offer: Offer; rank: number; origPrice: number }) {
  const medals = ['🥇', '🥈', '🥉']
  const savings = Math.round((1 - offer.price / origPrice) * 100)
  return (
    <div className="card p-4 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{medals[rank - 1]}</span>
        <span className="text-xs px-2 py-0.5 rounded bg-green-500/15 text-green-500 font-semibold">−{savings}%</span>
      </div>
      <div className="text-2xl font-extrabold mb-1">{offer.price}₽</div>
      <div className="text-xs text-[var(--td)] line-clamp-2 mb-2 flex-1">{offer.productName}</div>
      <div className="flex items-center gap-2 text-xs text-[var(--tm)] mb-3">
        <span className="font-semibold text-[var(--t)]">{offer.domain}</span>
        {offer.rating && (
          <>
            <span>·</span>
            <span className="flex items-center gap-0.5"><Star className="w-3 h-3 fill-amber-400 text-amber-400" />{offer.rating}</span>
            <span className="text-[var(--tm)]">({offer.reviewCnt})</span>
          </>
        )}
      </div>
      <a href={offer.url} target="_blank" rel="noopener" className="btn-primary h-9 text-xs inline-flex items-center justify-center gap-1.5">
        В магазин <ExternalLink className="w-3.5 h-3.5" />
      </a>
    </div>
  )
}

function EmptyView({ plannedCount, origPrice, origDomain, onReset }:
  { plannedCount: number; origPrice: number; origDomain: string; onReset: () => void }) {
  return (
    <div className="max-w-xl mx-auto animate-fadeIn">
      <div className="card p-8 text-center">
        <div className="w-14 h-14 rounded-full bg-[var(--c2)] mx-auto mb-4 flex items-center justify-center">
          <CheckCircle2 className="w-7 h-7 text-[var(--ac)]" />
        </div>
        <h2 className="text-xl font-bold mb-2">Дешевле не нашли</h2>
        <p className="text-sm text-[var(--td)] mb-5">
          Проверили {plannedCount} магазинов — лучшая цена так и осталась <span className="text-[var(--t)] font-semibold">{origPrice}₽</span> на <span className="text-[var(--t)] font-semibold">{origDomain}</span>.
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
        <div className="text-sm font-bold mb-3 text-green-500">Хорошо ищется</div>
        <ul className="space-y-1.5 text-sm text-[var(--td)]">
          <li>· Электроника и бытовая техника</li>
          <li>· Смартфоны, ноутбуки, аксессуары</li>
          <li>· Инструмент, DIY, товары для дома</li>
          <li>· Детские товары и игрушки</li>
          <li>· Продукты и FMCG</li>
        </ul>
      </div>
      <div className="card p-5">
        <div className="text-sm font-bold mb-3 text-amber-500">Не ищется</div>
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
