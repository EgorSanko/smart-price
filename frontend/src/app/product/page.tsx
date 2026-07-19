'use client'

import { useEffect, useState, useRef, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Star, ThumbsUp, ThumbsDown, ExternalLink, Truck,
  TrendingDown, TrendingUp, Minus, Loader2, ArrowLeft,
  Package, Store, Award, Sparkles, BarChart3, MessageSquare,
  ChevronDown, ChevronUp, Info, Check, ShieldCheck,
  Scale, Bot, Send, X
} from 'lucide-react'
import { proxyImage } from '@/lib/api'

const API = process.env.NEXT_PUBLIC_API_URL || ''

interface Offer {
  seller: string
  shop_id: string
  price: number
  warranty: number
  delivery: string
  rating: number
  reviews_count: number
  logo: string
  url: string
}

interface Review {
  author: string
  rating: number
  date: string
  pros: string
  cons: string
  summary: string
  likes: number
  dislikes: number
}

interface PricePoint { date: string; price: number }

interface ExternalReviewSource {
  source: string
  source_label: string
  reviews: Review[]
  rating: number
  count: number
  product_name?: string
}

interface Digest {
  pros: string[]
  cons: string[]
  sources: string
  sources_count: number
  reviews_count: number
}

interface ConfigOption {
  name: string
  key: string
  selected: boolean
}

interface ProductData {
  key: string
  title: string
  name: string
  description: string
  long_description: string
  micro_description: string
  html_url: string
  image: string
  images: Record<string, string>
  rating: number
  reviews_count: number
  category: string
  category_key: string
  price_min: number
  price_max: number
  offers_count: number
  currency: string
  specs: Record<string, { label: string; value: string }[]>
  digest: Digest
  configurations: Record<string, ConfigOption[]>
  offers: Offer[]
  reviews: Review[]
  price_history: PricePoint[]
  price_stats?: { min: number; max: number; avg: number }
  best_price?: number
  best_seller?: string
  external_reviews?: ExternalReviewSource[]
}

function formatPrice(p: number) {
  return p.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function StarsRow({ rating, size = 16 }: { rating: number; size?: number }) {
  return (
    <div style={{ display: 'flex', gap: 2 }}>
      {[1, 2, 3, 4, 5].map(i => (
        <Star
          key={i}
          className={i <= Math.round(rating) ? 'sp-star-filled' : 'sp-star-empty'}
          size={size}
        />
      ))}
    </div>
  )
}

function ProductContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const key = searchParams.get('key') || ''
  const [product, setProduct] = useState<ProductData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'reviews' | 'specs' | 'description' | 'history'>('reviews')
  const [showAllOffers, setShowAllOffers] = useState(false)
  const [reviewSource, setReviewSource] = useState<string>('onliner')
  const [extReviews, setExtReviews] = useState<ExternalReviewSource[]>([])
  const [extLoading, setExtLoading] = useState(false)

  // AI Chat state
  const [showChat, setShowChat] = useState(false)
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Compare state
  const [addedToCompare, setAddedToCompare] = useState(false)

  useEffect(() => {
    if (!key) { setError('Ключ товара не указан'); setLoading(false); return }
    const isConfigSwitch = !!product
    if (!isConfigSwitch) {
      setLoading(true)
    }
    setError('')
    setExtReviews([])
    const minDelay = isConfigSwitch
      ? Promise.resolve()
      : new Promise(r => setTimeout(r, 1200))
    const dataFetch = fetch(`${API}/api/v1/onliner/product/${encodeURIComponent(key)}`)
      .then(r => { if (!r.ok) throw new Error('Not found'); return r.json() })
    Promise.all([dataFetch, minDelay])
      .then(([data]) => setProduct(data))
      .catch(() => { setProduct(null); setError('Товар не найден') })
      .finally(() => setLoading(false))
  }, [key])

  // Fetch external reviews in background after product loads
  useEffect(() => {
    if (!product?.title) return
    setExtLoading(true)
    // Strip color/variant in parentheses for better cross-platform search
    const cleanName = product.title.replace(/\s*\([^)]*\)\s*$/, '').trim()
    fetch(`${API}/api/v1/onliner/external-reviews?product_name=${encodeURIComponent(cleanName)}&limit=8`)
      .then(r => r.json())
      .then(data => setExtReviews(data.sources || []))
      .catch(() => {})
      .finally(() => setExtLoading(false))
  }, [product?.title])

  // Scroll chat to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, chatLoading])

  const sendChatMessage = async (msg?: string) => {
    const text = msg || chatInput.trim()
    if (!text || chatLoading || !product) return
    setChatInput('')
    const userMsg = { role: 'user' as const, content: text }
    setChatMessages(prev => [...prev, userMsg])
    setChatLoading(true)

    const productContext = `Товар: ${product.title}\nЦена: от ${formatPrice(product.price_min)} до ${formatPrice(product.price_max)} BYN\nРейтинг: ${product.rating}/5 (${product.reviews_count} отзывов)\nОписание: ${product.micro_description || product.description}`

    try {
      const resp = await fetch(`${API}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: chatMessages.slice(-8),
          products_context: productContext,
        }),
      })
      const reader = resp.body?.getReader()
      if (!reader) return

      let assistantText = ''
      setChatMessages(prev => [...prev, { role: 'assistant', content: '' }])

      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue
          try {
            const d = JSON.parse(line.slice(6))
            if (d.text) {
              assistantText += d.text
              setChatMessages(prev => {
                const updated = [...prev]
                updated[updated.length - 1] = { role: 'assistant', content: assistantText }
                return updated
              })
            }
          } catch {}
        }
      }
    } catch {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Ошибка подключения к AI' }])
    } finally {
      setChatLoading(false)
    }
  }

  const addToCompare = () => {
    if (!product) return
    const stored = JSON.parse(sessionStorage.getItem('sp_compare') || '[]')
    if (stored.length >= 4) return
    if (stored.some((p: { title: string }) => p.title === product.title)) {
      setAddedToCompare(true)
      return
    }
    stored.push({
      title: product.title,
      price: formatPrice(product.price_min) + ' BYN',
      price_num: product.price_min,
      url: product.html_url,
      marketplace: 'onliner',
      image: product.image,
      shop: product.offers[0]?.seller || 'Onliner',
      specs: product.micro_description || '',
      onliner_key: product.key,
    })
    sessionStorage.setItem('sp_compare', JSON.stringify(stored))
    setAddedToCompare(true)
  }

  if (loading) {
    return (
      <>
        <div className="sp-loader-fullscreen">
          <div className="sp-loader-bg-glow" />
          <div className="sp-loader-bg-glow sp-glow-2" />
          <div className="sp-loader-content">
            <div className="sp-loader-orb">
              <div className="sp-loader-orbit" />
              <div className="sp-loader-orbit sp-orbit-2" />
              <div className="sp-loader-orbit sp-orbit-3" />
              <div className="sp-loader-core">SP</div>
            </div>
            <div className="sp-loader-title">Smart Price</div>
            <div className="sp-loader-bar-track">
              <div className="sp-loader-bar-glow" />
            </div>
            <div className="sp-loader-dots">
              <span className="sp-loader-dot" />
              <span className="sp-loader-dot" />
              <span className="sp-loader-dot" />
            </div>
            <p className="sp-loader-sub">Собираем цены и отзывы</p>
          </div>
        </div>
        <style jsx global>{`
          :root {
            --sp-bg: #0A0B0F;
            --sp-card: #181922;
            --sp-border: #2A2B3D;
            --sp-t1: #F0F0F5;
            --sp-t3: #5D5F78;
            --sp-accent: #6C5CE7;
            --sp-accent-glow: rgba(108,92,231,0.25);
            --sp-green: #00D26A;
            --sp-orange: #FF9F43;
          }
          .sp-loader-fullscreen {
            position: fixed; inset: 0; z-index: 100;
            display: flex; align-items: center; justify-content: center;
            background: var(--sp-bg);
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
          }
          .sp-loader-bg-glow {
            position: absolute; top: 30%; left: 50%;
            width: 500px; height: 500px;
            transform: translate(-50%, -50%);
            border-radius: 50%;
            background: radial-gradient(circle, rgba(108,92,231,.15), transparent 70%);
            filter: blur(60px);
            animation: spGlowPulse 3s ease-in-out infinite;
          }
          .sp-glow-2 {
            top: 60%; width: 400px; height: 400px;
            background: radial-gradient(circle, rgba(0,210,106,.1), transparent 70%);
            animation-delay: 1.5s;
          }
          @keyframes spGlowPulse {
            0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1.15); }
          }
          .sp-loader-content {
            position: relative; z-index: 1;
            display: flex; flex-direction: column; align-items: center;
          }
          .sp-loader-orb {
            position: relative; width: 120px; height: 120px; margin-bottom: 40px;
          }
          .sp-loader-orbit {
            position: absolute; inset: 0; border-radius: 50%;
            border: 2px solid transparent;
            border-top-color: var(--sp-accent);
            animation: spOrbitSpin 1.4s linear infinite;
          }
          .sp-orbit-2 {
            inset: 12px;
            border-top-color: transparent;
            border-right-color: var(--sp-green);
            border-bottom-color: var(--sp-green);
            animation-duration: 2s;
            animation-direction: reverse;
          }
          .sp-orbit-3 {
            inset: 24px;
            border-top-color: var(--sp-orange);
            border-left-color: var(--sp-orange);
            border-right-color: transparent;
            border-bottom-color: transparent;
            animation-duration: 2.8s;
          }
          @keyframes spOrbitSpin { to { transform: rotate(360deg); } }
          .sp-loader-core {
            position: absolute; inset: 32px;
            display: flex; align-items: center; justify-content: center;
            font-size: 28px; font-weight: 800; letter-spacing: -1px;
            color: var(--sp-t1);
            background: radial-gradient(circle, var(--sp-card) 60%, transparent);
            border-radius: 50%;
            animation: spCorePulse 2s ease-in-out infinite;
          }
          @keyframes spCorePulse {
            0%, 100% { text-shadow: 0 0 12px var(--sp-accent-glow); }
            50% { text-shadow: 0 0 28px var(--sp-accent-glow), 0 0 60px rgba(108,92,231,.15); }
          }
          .sp-loader-title {
            font-size: 32px; font-weight: 800; letter-spacing: 2px;
            color: var(--sp-t1); margin-bottom: 28px;
            background: linear-gradient(135deg, var(--sp-t1), var(--sp-accent));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
          }
          .sp-loader-bar-track {
            width: 260px; height: 3px; border-radius: 3px;
            background: var(--sp-border); overflow: hidden; margin-bottom: 24px;
            position: relative;
          }
          .sp-loader-bar-glow {
            position: absolute; top: 0; left: 0;
            width: 40%; height: 100%; border-radius: 3px;
            background: linear-gradient(90deg, var(--sp-accent), var(--sp-green), var(--sp-accent));
            box-shadow: 0 0 12px var(--sp-accent-glow);
            animation: spBarSlide 1.8s ease-in-out infinite;
          }
          @keyframes spBarSlide {
            0% { left: -40%; }
            100% { left: 100%; }
          }
          .sp-loader-dots { display: flex; gap: 8px; margin-bottom: 20px; }
          .sp-loader-dot {
            width: 6px; height: 6px; border-radius: 50%;
            background: var(--sp-accent);
            animation: spDotBounce 1.2s ease-in-out infinite;
          }
          .sp-loader-dot:nth-child(2) { animation-delay: 0.15s; }
          .sp-loader-dot:nth-child(3) { animation-delay: 0.3s; }
          @keyframes spDotBounce {
            0%, 80%, 100% { opacity: 0.3; transform: scale(1); }
            40% { opacity: 1; transform: scale(1.5); }
          }
          .sp-loader-sub {
            font-size: 14px; color: var(--sp-t3); letter-spacing: 0.5px;
            animation: spSubFade 2s ease-in-out infinite;
          }
          @keyframes spSubFade {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
          }
        `}</style>
      </>
    )
  }

  if (error || !product) {
    return (
      <div className="sp-error">
        <p>{error || 'Ошибка загрузки'}</p>
        <Link href="/">← Вернуться к поиску</Link>
      </div>
    )
  }

  const configEntries = Object.entries(product.configurations || {})
  const hasConfigs = configEntries.length > 0

  const bestOffer = product.offers[0]
  const otherOffers = product.offers.slice(1)
  const displayOffers = showAllOffers ? otherOffers : otherOffers.slice(0, 5)
  const specsGroups = Object.entries(product.specs)
  const hasHistory = product.price_history.length > 0
  const digest = product.digest || {} as Digest
  const hasPros = digest.pros?.length > 0
  const hasCons = digest.cons?.length > 0
  const hasDigest = hasPros || hasCons
  // Fallback: extract from reviews if no digest
  const reviewPros = product.reviews.filter(r => r.pros).map(r => r.pros).slice(0, 4)
  const reviewCons = product.reviews.filter(r => r.cons).map(r => r.cons).slice(0, 4)
  const hasLongDesc = !!product.long_description
  const extSources = extReviews
  const totalExtReviews = extSources.reduce((a, s) => a + s.count, 0)
  const totalReviewsAll = product.reviews_count + totalExtReviews

  const tabs = [
    { id: 'reviews' as const, label: `Отзывы покупателей`, count: totalReviewsAll || product.reviews_count, icon: MessageSquare },
    { id: 'specs' as const, label: 'Характеристики', count: specsGroups.reduce((a, [, v]) => a + v.length, 0) || null, icon: Info },
    { id: 'history' as const, label: 'История цен', count: hasHistory ? product.price_history.length : 0, icon: BarChart3 },
    { id: 'description' as const, label: 'Описание', count: null, icon: Package },
  ]

  return (
    <div className="sp-product-page">
      {/* Back button + Breadcrumbs */}
      <div className="sp-top-bar fade-up" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 4 }}>
        <button
          onClick={() => {
            const hasPrev = sessionStorage.getItem('sp_search')
            if (hasPrev) router.back()
            else router.push('/')
          }}
          className="sp-back-btn"
          style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px',
            borderRadius: 12, border: '1px solid var(--bd)', background: 'var(--c2)',
            color: 'var(--t2)', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            transition: 'all .15s', whiteSpace: 'nowrap',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--ac)'; e.currentTarget.style.color = 'var(--ac)' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--bd)'; e.currentTarget.style.color = 'var(--t2)' }}
        >
          <ArrowLeft size={15} />
          Назад к поиску
        </button>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={addToCompare}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px',
              borderRadius: 12, border: addedToCompare ? '1px solid var(--ac)' : '1px solid var(--bd)',
              background: addedToCompare ? 'rgba(99,102,241,.12)' : 'var(--c2)',
              color: addedToCompare ? 'var(--ac)' : 'var(--t2)', fontSize: 13, fontWeight: 600,
              cursor: 'pointer', transition: 'all .15s', whiteSpace: 'nowrap',
            }}
          >
            <Scale size={15} />
            {addedToCompare ? 'Добавлено' : 'Сравнить'}
          </button>
          <button
            onClick={() => setShowChat(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px',
              borderRadius: 12, border: '1px solid var(--bd)', background: 'var(--c2)',
              color: 'var(--t2)', fontSize: 13, fontWeight: 600,
              cursor: 'pointer', transition: 'all .15s', whiteSpace: 'nowrap',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--ac)'; e.currentTarget.style.color = 'var(--ac)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--bd)'; e.currentTarget.style.color = 'var(--t2)' }}
          >
            <Bot size={15} />
            AI-помощник
          </button>
        </div>
      </div>
      <nav className="sp-breadcrumbs fade-up">
        <Link href="/" className="sp-crumb-link">SmartPrice</Link>
        <span className="sp-crumb-sep">›</span>
        {product.category && (
          <>
            <span className="sp-crumb-text">{product.category}</span>
            <span className="sp-crumb-sep">›</span>
          </>
        )}
        <span className="sp-crumb-current">{product.name || product.title}</span>
        <span className="sp-onliner-badge">
          <span className="sp-onliner-dot" />
          Onliner.by
        </span>
      </nav>

      {/* Title + meta */}
      <h1 className="sp-title fade-up delay-1">{product.title}</h1>
      <div className="sp-meta-code fade-up delay-1">
        Код товара: <span>{product.key}</span>
      </div>

      {/* Rating bar */}
      <div className="sp-rating-bar fade-up delay-2">
        <StarsRow rating={product.rating} size={18} />
        <span className="sp-rating-num">{product.rating || '—'}</span>
        <button className="sp-rating-link" onClick={() => setActiveTab('reviews')}>
          {product.reviews_count} отзывов
        </button>
        <span className="sp-divider" />
        <span className="sp-offers-count">{product.offers_count} предложений</span>
        <a href={product.html_url} target="_blank" rel="noopener noreferrer" className="sp-onliner-link">
          Открыть на Onliner <ExternalLink size={13} />
        </a>
      </div>

      {/* === MAIN GRID === */}
      <div className="sp-main-grid">

        {/* LEFT: Product image */}
        <div className="sp-image-col fade-up delay-2">
          <div className="sp-image-card">
            <div className="sp-image-glow" />
            {product.image ? (
              <img src={proxyImage(product.image)} alt={product.title} className="sp-product-img" />
            ) : (
              <Package size={80} className="sp-img-placeholder" />
            )}
          </div>
        </div>

        {/* CENTER: Configuration */}
        <div className="sp-config-col fade-up delay-3">
          {/* Short specs */}
          {product.micro_description && (
            <div className="sp-short-specs">
              {product.micro_description}
            </div>
          )}

          {/* Configurations (storage, color, revision) */}
          {hasConfigs && (
            <div className="sp-configs">
              {configEntries.map(([label, options]) => (
                <div key={label} className="sp-config-group">
                  <div className="sp-config-label">{label}</div>
                  <div className="sp-config-chips">
                    {options.map((opt, i) => (
                      <Link
                        key={i}
                        href={opt.key ? `/product?key=${encodeURIComponent(opt.key)}` : '#'}
                        className={`sp-config-chip ${opt.selected ? 'sp-config-active' : ''}`}
                      >
                        {opt.selected && <Check size={12} />}
                        {opt.name}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Quick specs preview */}
          {specsGroups.length > 0 && (
            <div className="sp-quick-specs">
              <div className="sp-section-label">ОСНОВНЫЕ ХАРАКТЕРИСТИКИ</div>
              <div className="sp-specs-preview-grid">
                {specsGroups[0]?.[1]?.slice(0, 6).map((s, i) => (
                  <div key={i} className="sp-spec-row">
                    <span className="sp-spec-label">{s.label}</span>
                    <span className="sp-spec-value">{s.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Summary — from Onliner digest or fallback from reviews */}
          {(hasDigest || reviewPros.length > 0 || reviewCons.length > 0) && (
            <div className="sp-ai-section">
              <div className="sp-ai-badge">
                <Sparkles size={13} />
                {hasDigest
                  ? <>ИИ-ВЫЖИМКА · {digest.sources_count || ''} источников</>
                  : <>ИИ-ВЫЖИМКА ИЗ {product.reviews_count} ОТЗЫВОВ</>
                }
              </div>
              {hasDigest && digest.sources && (
                <div className="sp-ai-sources">
                  Источники: {digest.sources}
                </div>
              )}
              <div className="sp-ai-grid">
                {(hasPros ? digest.pros : reviewPros).length > 0 && (
                  <div className="sp-ai-card sp-ai-positive">
                    <div className="sp-ai-card-header">
                      <span className="sp-ai-icon sp-ai-icon-pos">👍</span>
                      Хвалят
                    </div>
                    {(hasPros ? digest.pros : reviewPros).map((p, i) => (
                      <div key={i} className="sp-ai-item">
                        <span className="sp-ai-dot sp-ai-dot-pos" />
                        <span>{p}</span>
                      </div>
                    ))}
                  </div>
                )}
                {(hasCons ? digest.cons : reviewCons).length > 0 && (
                  <div className="sp-ai-card sp-ai-negative">
                    <div className="sp-ai-card-header">
                      <span className="sp-ai-icon sp-ai-icon-neg">👎</span>
                      Критикуют
                    </div>
                    {(hasCons ? digest.cons : reviewCons).map((p, i) => (
                      <div key={i} className="sp-ai-item">
                        <span className="sp-ai-dot sp-ai-dot-neg" />
                        <span>{p}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Offers panel */}
        <div className="sp-offers-col fade-up delay-4">
          {/* Best price */}
          {bestOffer && (
            <div className="sp-best-price-card">
              <div className="sp-best-topbar" />
              <div className="sp-best-badge">
                <Check size={14} />
                ЛУЧШАЯ ЦЕНА
              </div>
              <div className="sp-best-price-row">
                <span className="sp-best-price">{formatPrice(bestOffer.price)}</span>
                <span className="sp-best-currency">BYN</span>
              </div>
              <div className="sp-best-seller">
                <Store size={14} />
                <span className="sp-best-seller-name">{bestOffer.seller}</span>
                {bestOffer.rating > 0 && (
                  <span className="sp-best-seller-rating">★ {bestOffer.rating}</span>
                )}
                {bestOffer.warranty > 0 && (
                  <span className="sp-best-seller-warranty">· {bestOffer.warranty} мес.</span>
                )}
              </div>
              {bestOffer.delivery && (
                <div className="sp-best-delivery">
                  <Truck size={13} />
                  {bestOffer.delivery}
                </div>
              )}
              <a href={product.html_url} target="_blank" rel="noopener noreferrer" className="sp-best-btn">
                В магазин →
              </a>
            </div>
          )}

          {/* Other offers */}
          {otherOffers.length > 0 && (
            <div className="sp-offers-list">
              <div className="sp-offers-header">
                <span>Все предложения</span>
                <span className="sp-offers-count-badge">{product.offers.length}</span>
              </div>
              {displayOffers.map((offer, i) => (
                <a key={i} href={product.html_url} target="_blank" rel="noopener noreferrer" className="sp-offer-row">
                  <div className="sp-offer-left">
                    <div className="sp-offer-seller">{offer.seller}</div>
                    <div className="sp-offer-meta">
                      {offer.rating > 0 && <span>★ {offer.rating}</span>}
                      {offer.warranty > 0 && <><span className="sp-dot">·</span><span>{offer.warranty} мес.</span></>}
                    </div>
                  </div>
                  <div className="sp-offer-right">
                    <div className="sp-offer-price">{formatPrice(offer.price)}</div>
                    {offer.delivery && <div className="sp-offer-delivery">{offer.delivery}</div>}
                  </div>
                </a>
              ))}
              {otherOffers.length > 5 && (
                <button onClick={() => setShowAllOffers(!showAllOffers)} className="sp-offers-toggle">
                  {showAllOffers ? <>Скрыть <ChevronUp size={14} /></> : <>Ещё {otherOffers.length - 5} магазинов <ChevronDown size={14} /></>}
                </button>
              )}
            </div>
          )}

          {/* Price range */}
          {product.price_stats && (
            <div className="sp-price-range">
              <div className="sp-section-label">ДИАПАЗОН ЦЕН</div>
              <div className="sp-range-row">
                <div className="sp-range-item">
                  <TrendingDown size={14} className="sp-c-green" />
                  <span className="sp-range-label">Мин:</span>
                  <span className="sp-range-val sp-c-green">{formatPrice(product.price_stats.min)}</span>
                </div>
                <div className="sp-range-item">
                  <TrendingUp size={14} className="sp-c-red" />
                  <span className="sp-range-label">Макс:</span>
                  <span className="sp-range-val sp-c-red">{formatPrice(product.price_stats.max)}</span>
                </div>
              </div>
              <div className="sp-range-item sp-range-avg">
                <Minus size={14} className="sp-c-orange" />
                <span className="sp-range-label">Средняя:</span>
                <span className="sp-range-val sp-c-orange">{formatPrice(product.price_stats.avg)}</span>
                <span className="sp-range-curr">BYN</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* === TABS === */}
      <div className="sp-tabs-section fade-up">
        <div className="sp-tabs-nav">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`sp-tab-btn ${activeTab === t.id ? 'sp-tab-active' : ''}`}
            >
              <t.icon size={15} />
              {t.label}
              {t.count !== null && t.count > 0 && (
                <span className="sp-tab-badge">{t.count}</span>
              )}
              {activeTab === t.id && <span className="sp-tab-indicator" />}
            </button>
          ))}
        </div>

        <div className="sp-tab-content">
          {/* Reviews — multi-source */}
          {activeTab === 'reviews' && (() => {
            const allSources = [
              { key: 'onliner', label: 'Onliner', color: '#65cb02', reviews: product.reviews, count: product.reviews_count, rating: product.rating },
              ...extSources.map(s => ({
                key: s.source,
                label: s.source_label,
                color: s.source === 'wildberries' ? '#cb11ab' : s.source === 'otzovik' ? '#4A90D9' : '#FF6B35',
                reviews: s.reviews,
                count: s.count,
                rating: s.rating,
              })),
            ]
            const activeSource = allSources.find(s => s.key === reviewSource) || allSources[0]
            const activeReviews = activeSource?.reviews || []

            return (
              <div className="sp-reviews-list">
                {/* Source selector tabs */}
                <div className="sp-review-sources">
                  {allSources.map(src => (
                    <button
                      key={src.key}
                      onClick={() => setReviewSource(src.key)}
                      className={`sp-review-source-btn ${reviewSource === src.key ? 'sp-rsrc-active' : ''}`}
                      style={{ '--src-color': src.color } as React.CSSProperties}
                    >
                      <span className="sp-rsrc-dot" style={{ background: src.color }} />
                      <span className="sp-rsrc-name">{src.label}</span>
                      {src.count > 0 && <span className="sp-rsrc-count">{src.count}</span>}
                      {src.rating > 0 && <span className="sp-rsrc-rating">★ {src.rating}</span>}
                    </button>
                  ))}
                  {extLoading && (
                    <span className="sp-review-source-btn" style={{ opacity: 0.5, cursor: 'default' }}>
                      <Loader2 size={14} className="animate-spin" style={{ marginRight: 4 }} />
                      <span className="sp-rsrc-name">Загрузка...</span>
                    </span>
                  )}
                </div>

                {/* Reviews list */}
                {activeReviews.length === 0 ? (
                  <p className="sp-empty">
                    {activeSource?.count ? `${activeSource.count} отзывов на ${activeSource?.label}` : 'Отзывов пока нет'}
                  </p>
                ) : activeReviews.map((r, i) => (
                  <div key={`${reviewSource}-${i}`} className="sp-review-card">
                    <div className="sp-review-header">
                      <div className="sp-review-author-row">
                        <span className="sp-review-author">{r.author}</span>
                        <span className="sp-review-src-badge" style={{ color: activeSource?.color, background: `${activeSource?.color}15` }}>
                          {activeSource?.label}
                        </span>
                      </div>
                      <span className="sp-review-date">{r.date}</span>
                    </div>
                    <div className="sp-review-stars"><StarsRow rating={r.rating} size={14} /></div>
                    {r.pros && (
                      <div className="sp-review-section">
                        <span className="sp-review-label sp-c-green">ДОСТОИНСТВА</span>
                        <p>{r.pros}</p>
                      </div>
                    )}
                    {r.cons && (
                      <div className="sp-review-section">
                        <span className="sp-review-label sp-c-red">НЕДОСТАТКИ</span>
                        <p>{r.cons}</p>
                      </div>
                    )}
                    {r.summary && (
                      <div className="sp-review-section">
                        <span className="sp-review-label sp-c-muted">КОММЕНТАРИЙ</span>
                        <p>{r.summary}</p>
                      </div>
                    )}
                    {(r.likes > 0 || r.dislikes > 0) && (
                      <div className="sp-review-actions">
                        <button className="sp-review-action"><ThumbsUp size={14} /> {r.likes}</button>
                        <button className="sp-review-action"><ThumbsDown size={14} /> {r.dislikes}</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )
          })()}

          {/* Specs */}
          {activeTab === 'specs' && (
            <div className="sp-specs-full">
              {specsGroups.length === 0 ? (
                <p className="sp-empty">Характеристики недоступны</p>
              ) : specsGroups.map(([group, items]) => (
                <div key={group} className="sp-specs-group">
                  <h3 className="sp-specs-group-title">{group}</h3>
                  {items.map((s, i) => (
                    <div key={i} className="sp-specs-row">
                      <span className="sp-specs-label">{s.label}</span>
                      <span className="sp-specs-value">{s.value}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* History */}
          {activeTab === 'history' && (
            <div className="sp-history">
              {!hasHistory ? (
                <p className="sp-empty">История цен недоступна</p>
              ) : (
                <>
                  {product.price_stats && (
                    <div className="sp-history-stats">
                      <div className="sp-history-stat">
                        <div className="sp-history-stat-label">Минимум</div>
                        <div className="sp-history-stat-val sp-c-green">{formatPrice(product.price_stats.min)} BYN</div>
                      </div>
                      <div className="sp-history-stat">
                        <div className="sp-history-stat-label">Средняя</div>
                        <div className="sp-history-stat-val sp-c-orange">{formatPrice(product.price_stats.avg)} BYN</div>
                      </div>
                      <div className="sp-history-stat">
                        <div className="sp-history-stat-label">Максимум</div>
                        <div className="sp-history-stat-val sp-c-red">{formatPrice(product.price_stats.max)} BYN</div>
                      </div>
                    </div>
                  )}
                  <div className="sp-history-list">
                    {product.price_history.slice(-20).reverse().map((p, i) => (
                      <div key={i} className="sp-history-row">
                        <span className="sp-history-date">{p.date}</span>
                        <span className="sp-history-price">{formatPrice(p.price)} BYN</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Description */}
          {activeTab === 'description' && (
            <div className="sp-description">
              {hasLongDesc ? (
                <div className="sp-long-desc">
                  {(() => {
                    // Split on emoji markers (✅, 🔹, etc.) to create sections
                    const text = product.long_description
                    const sections = text.split(/(?=✅|🔹|📌|⭐|🔥|💡)/).filter(s => s.trim())
                    // If no emoji markers found, fall back to paragraph splitting
                    const blocks = sections.length > 1
                      ? sections
                      : text.split('\n\n').filter(s => s.trim())

                    return blocks.map((block, i) => {
                      const trimmed = block.trim()
                      if (!trimmed) return null
                      let title = ''
                      let body = trimmed
                      const emojiM = trimmed.match(/^[^\s\w\u0400-\u04FF]+\s*/)
                      if (emojiM) {
                        const afterEmoji = trimmed.slice(emojiM[0].length)
                        // Detect smashed word boundary: lowercase directly followed by Cyrillic uppercase
                        // e.g. "зарядкаНовые", "IntelligenceСистема", "SiriТеперь"
                        const smashed = afterEmoji.search(/[a-zа-яё][А-ЯЁ]/)
                        if (smashed >= 0) {
                          title = (emojiM[0] + afterEmoji.slice(0, smashed + 1)).trim()
                          body = afterEmoji.slice(smashed + 1).trim()
                        } else {
                          // Title = consecutive Russian Cyrillic words
                          const cyrTitle = afterEmoji.match(/^(?:[а-яА-ЯёЁ]+\s*)+/)
                          if (cyrTitle && cyrTitle[0].trim().length > 0) {
                            title = (emojiM[0] + cyrTitle[0]).trim()
                            body = afterEmoji.slice(cyrTitle[0].length).trim()
                          } else {
                            // Latin-prefixed title (e.g. "Apple Intelligence")
                            const latTitle = afterEmoji.match(/^[A-Za-z]+(?:\s+[A-Za-z]+)*/)
                            if (latTitle) {
                              title = (emojiM[0] + latTitle[0]).trim()
                              body = afterEmoji.slice(latTitle[0].length).trim()
                            }
                          }
                        }
                      }
                      if (title) {
                        return (
                          <div key={i} className="sp-desc-block">
                            <h3 className="sp-desc-heading">{title}</h3>
                            {body && <p>{body}</p>}
                          </div>
                        )
                      }
                      return (
                        <div key={i} className="sp-desc-block">
                          {trimmed.split('\n').map((line, j) => {
                            const l = line.trim()
                            if (!l) return null
                            return <p key={j}>{l}</p>
                          })}
                        </div>
                      )
                    })
                  })()}
                </div>
              ) : (
                <p>{product.description || 'Описание недоступно'}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Back */}
      <div className="sp-back fade-up">
        <Link href="/" className="sp-back-link">
          <ArrowLeft size={16} /> Вернуться к поиску
        </Link>
      </div>

      <style jsx global>{`
        /* ═══════════════════════════════════════════════════
           SmartPrice Premium Product Page — Dark Theme
           ═══════════════════════════════════════════════════ */

        :root {
          --sp-bg: #0A0B0F;
          --sp-bg2: #12131A;
          --sp-card: #181922;
          --sp-card-hover: #1E2030;
          --sp-elevated: #222338;
          --sp-border: #2A2B3D;
          --sp-border-s: #1E1F30;
          --sp-t1: #F0F0F5;
          --sp-t2: #9496AD;
          --sp-t3: #5D5F78;
          --sp-accent: #6C5CE7;
          --sp-accent-glow: rgba(108,92,231,0.25);
          --sp-accent-s: rgba(108,92,231,0.12);
          --sp-green: #00D26A;
          --sp-green-s: rgba(0,210,106,0.12);
          --sp-green-glow: rgba(0,210,106,0.3);
          --sp-orange: #FF9F43;
          --sp-orange-s: rgba(255,159,67,0.12);
          --sp-red: #FF6B6B;
          --sp-red-s: rgba(255,107,107,0.12);
          --sp-yellow: #FECA57;
        }

        .sp-product-page {
          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
          max-width: 1360px;
          margin: 0 auto;
          padding: 24px 20px 80px;
          color: var(--sp-t1);
        }

        /* ── Animations ── */
        @keyframes spFadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes spPulseGlow {
          0%, 100% { box-shadow: 0 0 8px var(--sp-green-glow), inset 0 0 0 1px var(--sp-green); }
          50% { box-shadow: 0 0 24px var(--sp-green-glow), inset 0 0 0 1px var(--sp-green); }
        }
        .fade-up { animation: spFadeUp 0.5s ease forwards; opacity: 0; }
        .delay-1 { animation-delay: 0.1s; }
        .delay-2 { animation-delay: 0.2s; }
        .delay-3 { animation-delay: 0.3s; }
        .delay-4 { animation-delay: 0.4s; }

        /* ── Stars ── */
        .sp-star-filled { color: var(--sp-yellow); fill: var(--sp-yellow); }
        .sp-star-empty { color: var(--sp-t3); }

        /* ── Color utils ── */
        .sp-c-green { color: var(--sp-green) !important; }
        .sp-c-red { color: var(--sp-red) !important; }
        .sp-c-orange { color: var(--sp-orange) !important; }
        .sp-c-muted { color: var(--sp-t2) !important; }

        /* ── Fullscreen Loading Animation ── */
        .sp-loader-fullscreen {
          position: fixed; inset: 0; z-index: 100;
          display: flex; align-items: center; justify-content: center;
          background: var(--sp-bg);
          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
        }
        .sp-loader-bg-glow {
          position: absolute; top: 30%; left: 50%;
          width: 500px; height: 500px;
          transform: translate(-50%, -50%);
          border-radius: 50%;
          background: radial-gradient(circle, rgba(108,92,231,.15), transparent 70%);
          filter: blur(60px);
          animation: spGlowPulse 3s ease-in-out infinite;
        }
        .sp-glow-2 {
          top: 60%; width: 400px; height: 400px;
          background: radial-gradient(circle, rgba(0,210,106,.1), transparent 70%);
          animation-delay: 1.5s;
        }
        @keyframes spGlowPulse {
          0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: 1; transform: translate(-50%, -50%) scale(1.15); }
        }

        .sp-loader-content {
          position: relative; z-index: 1;
          display: flex; flex-direction: column; align-items: center;
        }

        /* Orb with orbiting rings */
        .sp-loader-orb {
          position: relative; width: 120px; height: 120px; margin-bottom: 40px;
        }
        .sp-loader-orbit {
          position: absolute; inset: 0; border-radius: 50%;
          border: 2px solid transparent;
          border-top-color: var(--sp-accent);
          animation: spOrbitSpin 1.4s linear infinite;
        }
        .sp-orbit-2 {
          inset: 12px;
          border-top-color: transparent;
          border-right-color: var(--sp-green);
          border-bottom-color: var(--sp-green);
          animation-duration: 2s;
          animation-direction: reverse;
        }
        .sp-orbit-3 {
          inset: 24px;
          border-top-color: var(--sp-orange);
          border-left-color: var(--sp-orange);
          border-right-color: transparent;
          border-bottom-color: transparent;
          animation-duration: 2.8s;
        }
        @keyframes spOrbitSpin { to { transform: rotate(360deg); } }

        .sp-loader-core {
          position: absolute; inset: 32px;
          display: flex; align-items: center; justify-content: center;
          font-size: 28px; font-weight: 800; letter-spacing: -1px;
          color: var(--sp-t1);
          background: radial-gradient(circle, var(--sp-card) 60%, transparent);
          border-radius: 50%;
          animation: spCorePulse 2s ease-in-out infinite;
        }
        @keyframes spCorePulse {
          0%, 100% { text-shadow: 0 0 12px var(--sp-accent-glow); }
          50% { text-shadow: 0 0 28px var(--sp-accent-glow), 0 0 60px rgba(108,92,231,.15); }
        }

        /* Title */
        .sp-loader-title {
          font-size: 32px; font-weight: 800; letter-spacing: 2px;
          color: var(--sp-t1); margin-bottom: 28px;
          background: linear-gradient(135deg, var(--sp-t1), var(--sp-accent));
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        /* Progress bar */
        .sp-loader-bar-track {
          width: 260px; height: 3px; border-radius: 3px;
          background: var(--sp-border); overflow: hidden; margin-bottom: 24px;
          position: relative;
        }
        .sp-loader-bar-glow {
          position: absolute; top: 0; left: 0;
          width: 40%; height: 100%; border-radius: 3px;
          background: linear-gradient(90deg, var(--sp-accent), var(--sp-green), var(--sp-accent));
          box-shadow: 0 0 12px var(--sp-accent-glow);
          animation: spBarSlide 1.8s ease-in-out infinite;
        }
        @keyframes spBarSlide {
          0% { left: -40%; }
          100% { left: 100%; }
        }

        /* Bouncing dots */
        .sp-loader-dots {
          display: flex; gap: 8px; margin-bottom: 20px;
        }
        .sp-loader-dot {
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--sp-accent);
          animation: spDotBounce 1.2s ease-in-out infinite;
        }
        .sp-loader-dot:nth-child(2) { animation-delay: 0.15s; }
        .sp-loader-dot:nth-child(3) { animation-delay: 0.3s; }
        @keyframes spDotBounce {
          0%, 80%, 100% { opacity: 0.3; transform: scale(1); }
          40% { opacity: 1; transform: scale(1.5); }
        }

        /* Subtitle */
        .sp-loader-sub {
          font-size: 14px; color: var(--sp-t3); letter-spacing: 0.5px;
          animation: spSubFade 2s ease-in-out infinite;
        }
        @keyframes spSubFade {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }
        .sp-error {
          text-align: center; padding: 80px 0;
          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
        }
        .sp-error p { color: var(--sp-red); font-size: 18px; margin-bottom: 16px; }
        .sp-error a { color: var(--sp-accent); text-decoration: none; }
        .sp-error a:hover { text-decoration: underline; }

        /* ── Breadcrumbs ── */
        .sp-breadcrumbs {
          display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
          font-size: 13px; color: var(--sp-t3); margin-bottom: 20px;
        }
        .sp-crumb-link { color: var(--sp-t3); text-decoration: none; transition: color 0.2s; }
        .sp-crumb-link:hover { color: var(--sp-accent); }
        .sp-crumb-sep { opacity: 0.4; }
        .sp-crumb-text { color: var(--sp-t3); }
        .sp-crumb-current { color: var(--sp-t2); }
        .sp-onliner-badge {
          margin-left: auto;
          display: inline-flex; align-items: center; gap: 6px;
          padding: 4px 12px; border-radius: 100px;
          font-size: 11px; font-weight: 700; text-transform: uppercase;
          letter-spacing: 0.5px;
          background: var(--sp-orange-s); color: var(--sp-orange);
        }
        .sp-onliner-dot {
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--sp-orange);
        }

        /* ── Title ── */
        .sp-title {
          font-size: 28px; font-weight: 700; letter-spacing: -0.5px;
          line-height: 1.25; margin: 0 0 6px;
          color: var(--sp-t1);
        }
        .sp-meta-code {
          font-size: 13px; color: var(--sp-t3); margin-bottom: 16px;
        }
        .sp-meta-code span {
          font-family: 'JetBrains Mono', monospace; color: var(--sp-t2);
        }

        /* ── Rating bar ── */
        .sp-rating-bar {
          display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
          margin-bottom: 28px; padding-bottom: 24px;
          border-bottom: 1px solid var(--sp-border-s);
        }
        .sp-rating-num { font-size: 15px; font-weight: 700; color: var(--sp-t1); }
        .sp-rating-link {
          background: none; border: none; cursor: pointer;
          font-size: 14px; color: var(--sp-accent); font-family: inherit;
          padding: 0; text-decoration: none;
        }
        .sp-rating-link:hover { text-decoration: underline; }
        .sp-divider { width: 1px; height: 16px; background: var(--sp-border); }
        .sp-offers-count { font-size: 14px; color: var(--sp-t2); }
        .sp-onliner-link {
          margin-left: auto;
          display: inline-flex; align-items: center; gap: 5px;
          font-size: 13px; color: var(--sp-accent); text-decoration: none;
          transition: color 0.2s;
        }
        .sp-onliner-link:hover { color: #8B7CF7; text-decoration: underline; }

        /* ═══ MAIN GRID ═══ */
        .sp-main-grid {
          display: grid;
          grid-template-columns: 420px 1fr 340px;
          gap: 32px;
          align-items: start;
        }
        @media (max-width: 1100px) {
          .sp-main-grid { grid-template-columns: 360px 1fr; }
          .sp-offers-col { grid-column: 1 / -1; }
        }
        @media (max-width: 768px) {
          .sp-main-grid { grid-template-columns: 1fr; }
        }

        /* ── Image column ── */
        .sp-image-col { position: sticky; top: 24px; }
        @media (max-width: 768px) { .sp-image-col { position: static; } }
        .sp-image-card {
          background: var(--sp-card);
          border: 1px solid var(--sp-border-s);
          border-radius: 20px; padding: 40px;
          aspect-ratio: 1; display: flex;
          align-items: center; justify-content: center;
          position: relative; overflow: hidden;
        }
        .sp-image-glow {
          position: absolute; inset: 0;
          background: radial-gradient(ellipse at 30% 30%, var(--sp-accent-s), transparent 70%);
          pointer-events: none;
        }
        .sp-product-img {
          width: 100%; height: 100%; object-fit: contain;
          position: relative; z-index: 1;
          filter: drop-shadow(0 20px 40px rgba(0,0,0,0.4));
        }
        .sp-img-placeholder { color: var(--sp-t3); opacity: 0.3; }

        /* ── Config column (center) ── */
        .sp-config-col { min-width: 0; }

        .sp-short-specs {
          background: var(--sp-card); border: 1px solid var(--sp-border-s);
          border-radius: 12px; padding: 16px 20px;
          font-size: 14px; color: var(--sp-t2); line-height: 1.7;
          margin-bottom: 24px;
        }

        .sp-section-label {
          font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
          text-transform: uppercase; color: var(--sp-t3); margin-bottom: 12px;
        }

        .sp-quick-specs { margin-bottom: 24px; }
        .sp-specs-preview-grid {
          display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px;
        }
        @media (max-width: 640px) { .sp-specs-preview-grid { grid-template-columns: 1fr; } }
        .sp-spec-row {
          display: flex; justify-content: space-between; align-items: baseline;
          padding: 8px 0; border-bottom: 1px solid var(--sp-border-s); font-size: 13px;
        }
        .sp-spec-label { color: var(--sp-t3); }
        .sp-spec-value { color: var(--sp-t1); font-weight: 500; text-align: right; margin-left: 12px; }

        /* AI section */
        .sp-ai-section { margin-top: 28px; }
        .sp-ai-badge {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 5px 14px; border-radius: 100px;
          font-size: 11px; font-weight: 700; letter-spacing: 0.8px;
          background: var(--sp-accent-s); color: var(--sp-accent);
          margin-bottom: 16px;
        }
        .sp-ai-sources { font-size: 11px; color: var(--sp-t3); margin-bottom: 12px; letter-spacing: 0.3px; }
        .sp-ai-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        @media (max-width: 640px) { .sp-ai-grid { grid-template-columns: 1fr; } }

        .sp-ai-card {
          padding: 20px; border-radius: 16px;
        }
        .sp-ai-positive {
          background: linear-gradient(135deg, rgba(0,210,106,0.04), transparent);
          border: 1px solid rgba(0,210,106,0.15);
        }
        .sp-ai-negative {
          background: linear-gradient(135deg, rgba(255,107,107,0.04), transparent);
          border: 1px solid rgba(255,107,107,0.15);
        }
        .sp-ai-card-header {
          display: flex; align-items: center; gap: 8px;
          font-size: 15px; font-weight: 700; margin-bottom: 12px;
          color: var(--sp-t1);
        }
        .sp-ai-icon {
          width: 28px; height: 28px; border-radius: 8px;
          display: flex; align-items: center; justify-content: center;
          font-size: 14px;
        }
        .sp-ai-icon-pos { background: var(--sp-green-s); }
        .sp-ai-icon-neg { background: var(--sp-red-s); }

        .sp-ai-item {
          display: flex; gap: 10px; align-items: flex-start;
          padding: 8px 0; border-bottom: 1px solid var(--sp-border-s);
          font-size: 13px; color: var(--sp-t2); line-height: 1.6;
        }
        .sp-ai-item:last-child { border-bottom: none; }
        .sp-ai-dot {
          width: 6px; height: 6px; border-radius: 50%;
          margin-top: 7px; flex-shrink: 0;
        }
        .sp-ai-dot-pos { background: var(--sp-green); }
        .sp-ai-dot-neg { background: var(--sp-red); }

        /* ═══ OFFERS PANEL (right) ═══ */
        .sp-offers-col { position: sticky; top: 24px; }
        @media (max-width: 1100px) { .sp-offers-col { position: static; } }

        /* Best price card */
        .sp-best-price-card {
          position: relative; border-radius: 16px; padding: 24px;
          margin-bottom: 16px; overflow: hidden;
          background: linear-gradient(135deg, var(--sp-card), var(--sp-elevated));
          border: 1px solid var(--sp-green);
          animation: spPulseGlow 3s ease-in-out infinite;
        }
        .sp-best-topbar {
          position: absolute; top: 0; left: 0; right: 0; height: 3px;
          background: linear-gradient(90deg, var(--sp-green), var(--sp-accent));
        }
        .sp-best-badge {
          display: flex; align-items: center; gap: 6px;
          font-size: 11px; font-weight: 700; text-transform: uppercase;
          letter-spacing: 1.5px; color: var(--sp-green); margin-bottom: 12px;
        }
        .sp-best-price-row { margin-bottom: 8px; }
        .sp-best-price {
          font-family: 'JetBrains Mono', monospace;
          font-size: 36px; font-weight: 800; color: var(--sp-t1);
          letter-spacing: -1px;
        }
        .sp-best-currency {
          font-size: 20px; font-weight: 600; color: var(--sp-t2); margin-left: 6px;
        }
        .sp-best-seller {
          display: flex; align-items: center; gap: 8px;
          font-size: 14px; color: var(--sp-t2);
        }
        .sp-best-seller-name { font-weight: 600; color: var(--sp-t1); }
        .sp-best-seller-rating { color: var(--sp-yellow); font-weight: 600; font-size: 13px; }
        .sp-best-seller-warranty { color: var(--sp-t3); }
        .sp-best-delivery {
          display: flex; align-items: center; gap: 6px;
          font-size: 13px; color: var(--sp-green); margin-top: 6px;
        }
        .sp-best-btn {
          display: block; width: 100%; margin-top: 16px;
          padding: 14px; border-radius: 12px;
          background: var(--sp-green); color: #000;
          text-align: center; font-weight: 700; font-size: 15px;
          text-decoration: none;
          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
          transition: all 0.2s;
        }
        .sp-best-btn:hover {
          background: #00E676;
          box-shadow: 0 4px 24px var(--sp-green-glow);
          transform: translateY(-1px);
        }

        /* Offers list */
        .sp-offers-list { margin-bottom: 16px; }
        .sp-offers-header {
          display: flex; justify-content: space-between; align-items: center;
          margin-bottom: 12px;
          font-size: 14px; font-weight: 600; color: var(--sp-t2);
        }
        .sp-offers-count-badge {
          background: var(--sp-accent-s); color: var(--sp-accent);
          font-size: 12px; font-weight: 700;
          padding: 2px 10px; border-radius: 100px;
        }
        .sp-offer-row {
          display: flex; justify-content: space-between; align-items: center;
          padding: 14px 16px; margin-bottom: 8px;
          background: var(--sp-card); border: 1px solid var(--sp-border-s);
          border-radius: 12px; text-decoration: none;
          transition: all 0.2s;
        }
        .sp-offer-row:hover {
          border-color: var(--sp-accent);
          background: var(--sp-card-hover);
          transform: translateX(2px);
        }
        .sp-offer-left {}
        .sp-offer-seller { font-size: 14px; font-weight: 600; color: var(--sp-t1); }
        .sp-offer-row:hover .sp-offer-seller { color: var(--sp-accent); }
        .sp-offer-meta { font-size: 12px; color: var(--sp-t3); display: flex; gap: 6px; }
        .sp-dot { opacity: 0.4; }
        .sp-offer-right { text-align: right; }
        .sp-offer-price {
          font-family: 'JetBrains Mono', monospace;
          font-size: 18px; font-weight: 700; color: var(--sp-t1);
        }
        .sp-offer-delivery { font-size: 11px; color: var(--sp-green); font-weight: 500; }
        .sp-offers-toggle {
          display: flex; align-items: center; justify-content: center; gap: 4px;
          width: 100%; padding: 10px; border: none; background: none;
          font-size: 13px; font-weight: 500; color: var(--sp-accent);
          cursor: pointer; font-family: inherit; transition: color 0.2s;
        }
        .sp-offers-toggle:hover { color: #8B7CF7; }

        /* Price range */
        .sp-price-range {
          padding: 16px; background: var(--sp-card);
          border: 1px solid var(--sp-border-s); border-radius: 12px;
        }
        .sp-range-row { display: flex; justify-content: space-between; }
        .sp-range-item { display: flex; align-items: center; gap: 6px; font-size: 14px; }
        .sp-range-label { color: var(--sp-t2); }
        .sp-range-val { font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .sp-range-avg { margin-top: 8px; }
        .sp-range-curr { color: var(--sp-t3); font-size: 13px; }

        /* ═══ TABS ═══ */
        .sp-tabs-section { margin-top: 48px; }
        .sp-tabs-nav {
          display: flex; gap: 0; border-bottom: 1px solid var(--sp-border);
          margin-bottom: 32px; overflow-x: auto;
        }
        .sp-tab-btn {
          display: flex; align-items: center; gap: 8px;
          padding: 14px 24px; border: none; background: none;
          font-size: 14px; font-weight: 600; color: var(--sp-t3);
          cursor: pointer; position: relative; white-space: nowrap;
          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
          transition: color 0.2s;
        }
        .sp-tab-btn:hover { color: var(--sp-t2); }
        .sp-tab-active { color: var(--sp-accent) !important; }
        .sp-tab-indicator {
          position: absolute; bottom: 0; left: 0; right: 0;
          height: 2px; background: var(--sp-accent); border-radius: 2px 2px 0 0;
        }
        .sp-tab-badge {
          background: var(--sp-elevated); color: var(--sp-t3);
          font-size: 11px; font-weight: 700;
          padding: 2px 8px; border-radius: 8px;
        }
        .sp-tab-active .sp-tab-badge { background: var(--sp-accent-s); color: var(--sp-accent); }

        .sp-tab-content { max-width: 780px; }
        .sp-empty { color: var(--sp-t3); text-align: center; padding: 48px 0; }

        /* Reviews */
        .sp-review-card {
          background: var(--sp-card); border: 1px solid var(--sp-border-s);
          border-radius: 16px; padding: 24px; margin-bottom: 12px;
          transition: border-color 0.2s;
        }
        .sp-review-card:hover { border-color: var(--sp-border); }
        .sp-review-header {
          display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
        }
        .sp-review-author { font-size: 15px; font-weight: 700; color: var(--sp-t1); }
        .sp-review-date { font-size: 13px; color: var(--sp-t3); }
        .sp-review-stars { margin-bottom: 12px; }
        .sp-review-section { margin-bottom: 10px; }
        .sp-review-label {
          font-size: 11px; font-weight: 700; letter-spacing: 0.8px;
          text-transform: uppercase; display: block; margin-bottom: 4px;
        }
        .sp-review-section p {
          font-size: 14px; color: var(--sp-t2); line-height: 1.8; margin: 0;
        }
        .sp-review-actions {
          display: flex; gap: 16px; margin-top: 12px; padding-top: 12px;
          border-top: 1px solid var(--sp-border-s);
        }
        .sp-review-action {
          display: flex; align-items: center; gap: 6px;
          background: none; border: none; cursor: pointer;
          font-size: 13px; color: var(--sp-t3); font-family: inherit;
          transition: color 0.2s;
        }
        .sp-review-action:hover { color: var(--sp-t2); }

        /* Review source tabs */
        .sp-review-sources {
          display: flex; flex-wrap: wrap; gap: 8px;
          margin-bottom: 24px; padding: 16px;
          background: var(--sp-card); border-radius: 16px;
          border: 1px solid var(--sp-border-s);
        }
        .sp-review-source-btn {
          display: flex; align-items: center; gap: 8px;
          padding: 10px 16px; border-radius: 12px;
          border: 1px solid var(--sp-border);
          background: transparent; cursor: pointer;
          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
          font-size: 13px; font-weight: 600;
          color: var(--sp-t2); transition: all 0.25s;
        }
        .sp-review-source-btn:hover {
          border-color: var(--src-color);
          background: rgba(255,255,255,.03);
        }
        .sp-rsrc-active {
          border-color: var(--src-color) !important;
          background: rgba(255,255,255,.05) !important;
          color: var(--sp-t1) !important;
          box-shadow: 0 0 16px rgba(108,92,231,.15);
        }
        .sp-rsrc-dot {
          width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
        }
        .sp-rsrc-active .sp-rsrc-dot {
          box-shadow: 0 0 8px currentColor;
        }
        .sp-rsrc-name { white-space: nowrap; }
        .sp-rsrc-count {
          font-size: 11px; font-weight: 700;
          padding: 2px 8px; border-radius: 8px;
          background: var(--sp-elevated); color: var(--sp-t3);
        }
        .sp-rsrc-active .sp-rsrc-count {
          background: rgba(108,92,231,.15); color: var(--sp-accent);
        }
        .sp-rsrc-rating {
          font-size: 12px; color: var(--sp-yellow); font-weight: 600;
        }
        .sp-review-author-row {
          display: flex; align-items: center; gap: 8px;
        }
        .sp-review-src-badge {
          font-size: 10px; font-weight: 700; text-transform: uppercase;
          letter-spacing: 0.5px; padding: 2px 8px; border-radius: 6px;
        }

        /* Specs */
        .sp-specs-group { margin-bottom: 32px; }
        .sp-specs-group-title {
          font-size: 16px; font-weight: 700; color: var(--sp-t1);
          margin: 0 0 12px; padding-bottom: 8px;
          border-bottom: 1px solid var(--sp-border);
        }
        .sp-specs-row {
          display: flex; padding: 10px 0;
          border-bottom: 1px solid var(--sp-border-s); font-size: 14px;
        }
        .sp-specs-row:last-child { border-bottom: none; }
        .sp-specs-label { width: 220px; flex-shrink: 0; color: var(--sp-t3); }
        .sp-specs-value { color: var(--sp-t1); font-weight: 500; }

        /* History */
        .sp-history-stats {
          display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;
          margin-bottom: 24px;
        }
        @media (max-width: 640px) { .sp-history-stats { grid-template-columns: 1fr; } }
        .sp-history-stat {
          background: var(--sp-card); border: 1px solid var(--sp-border-s);
          border-radius: 12px; padding: 16px; text-align: center;
        }
        .sp-history-stat-label {
          font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px;
          color: var(--sp-t3); margin-bottom: 4px;
        }
        .sp-history-stat-val {
          font-family: 'JetBrains Mono', monospace;
          font-size: 18px; font-weight: 700;
        }
        .sp-history-row {
          display: flex; justify-content: space-between;
          padding: 10px 12px; border-radius: 8px;
          transition: background 0.2s;
        }
        .sp-history-row:hover { background: var(--sp-card); }
        .sp-history-date {
          font-family: 'JetBrains Mono', monospace;
          font-size: 13px; color: var(--sp-t3);
        }
        .sp-history-price {
          font-family: 'JetBrains Mono', monospace;
          font-size: 14px; font-weight: 700; color: var(--sp-t1);
        }

        /* Description */
        .sp-description { max-width: 800px; }
        .sp-description p { font-size: 15px; color: var(--sp-t2); line-height: 1.8; margin: 0 0 8px 0; }
        .sp-long-desc { display: flex; flex-direction: column; gap: 0; }
        .sp-desc-block { margin-bottom: 16px; padding: 16px 20px; background: var(--sp-card); border-radius: 12px; border: 1px solid var(--sp-border-s); }
        .sp-desc-block li { font-size: 15px; color: var(--sp-t2); line-height: 1.8; margin: 0 0 6px 20px; list-style: disc; }
        .sp-desc-heading { font-size: 18px; font-weight: 700; color: var(--sp-t1); margin: 24px 0 12px 0; }
        .sp-desc-heading:first-child { margin-top: 0; }
        .sp-desc-accent { color: var(--sp-accent); font-weight: 600; }

        /* Configurations */
        .sp-configs { margin-bottom: 24px; }
        .sp-config-group { margin-bottom: 16px; }
        .sp-config-label {
          font-size: 12px; font-weight: 700; text-transform: uppercase;
          letter-spacing: 1px; color: var(--sp-t3); margin-bottom: 10px;
        }
        .sp-config-chips { display: flex; flex-wrap: wrap; gap: 8px; }
        .sp-config-chip {
          display: inline-flex; align-items: center; gap: 5px;
          padding: 8px 16px; border-radius: 10px;
          font-size: 13px; font-weight: 600; text-decoration: none;
          background: var(--sp-card); border: 1px solid var(--sp-border);
          color: var(--sp-t2); transition: all 0.2s; cursor: pointer;
        }
        .sp-config-chip:hover {
          border-color: var(--sp-accent); color: var(--sp-accent);
          background: var(--sp-accent-s);
        }
        .sp-config-active {
          background: var(--sp-accent-s) !important;
          border-color: var(--sp-accent) !important;
          color: var(--sp-accent) !important;
          box-shadow: 0 0 12px var(--sp-accent-glow);
        }

        /* Back */
        .sp-back { margin-top: 48px; }
        .sp-back-link {
          display: inline-flex; align-items: center; gap: 8px;
          font-size: 14px; color: var(--sp-accent); text-decoration: none;
          transition: color 0.2s;
        }
        .sp-back-link:hover { color: #8B7CF7; }
      `}</style>

      {/* Floating AI button (mobile-friendly) */}
      {!showChat && (
        <button
          onClick={() => setShowChat(true)}
          style={{
            position: 'fixed', bottom: 24, right: 24, zIndex: 45,
            width: 56, height: 56, borderRadius: '50%',
            background: 'var(--ac)', color: 'white', border: 'none',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', boxShadow: '0 4px 20px rgba(99,102,241,.4)',
            transition: 'transform .15s',
          }}
          onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.1)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
        >
          <Bot size={24} />
        </button>
      )}

      {/* AI Chat Drawer */}
      {showChat && (
        <div style={{
          position: 'fixed', bottom: 0, right: 0, zIndex: 50,
          width: '100%', maxWidth: 420, height: '70vh', maxHeight: 600,
          display: 'flex', flexDirection: 'column',
          background: 'var(--c1)', border: '1px solid var(--bd)',
          borderRadius: '16px 16px 0 0', boxShadow: '0 -8px 40px rgba(0,0,0,.4)',
          overflow: 'hidden',
        }}>
          {/* Chat header */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '14px 18px', borderBottom: '1px solid var(--bd)',
            background: 'rgba(99,102,241,.06)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Bot size={20} style={{ color: 'var(--ac)' }} />
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--t)' }}>AI-помощник</div>
                <div style={{ fontSize: 11, color: 'var(--td)' }}>{product?.title?.slice(0, 40)}{(product?.title?.length || 0) > 40 ? '...' : ''}</div>
              </div>
            </div>
            <button onClick={() => setShowChat(false)} style={{ background: 'none', border: 'none', color: 'var(--td)', cursor: 'pointer', padding: 4 }}>
              <X size={20} />
            </button>
          </div>

          {/* Chat messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {chatMessages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '24px 12px' }}>
                <Bot size={36} style={{ color: 'var(--ac)', margin: '0 auto 12px', opacity: 0.5 }} />
                <p style={{ fontSize: 14, color: 'var(--t2)', fontWeight: 600, marginBottom: 8 }}>
                  Спросите что угодно про этот товар
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {[
                    'Чем этот товар лучше конкурентов?',
                    'Стоит ли покупать?',
                    'Какие есть альтернативы дешевле?',
                  ].map(q => (
                    <button
                      key={q}
                      onClick={() => sendChatMessage(q)}
                      style={{
                        padding: '8px 12px', borderRadius: 10,
                        border: '1px solid var(--bd)', background: 'var(--c2)',
                        color: 'var(--td)', fontSize: 12, cursor: 'pointer',
                        textAlign: 'left', transition: 'all .15s',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--ac)'; e.currentTarget.style.color = 'var(--ac)' }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--bd)'; e.currentTarget.style.color = 'var(--td)' }}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%', padding: '10px 14px', borderRadius: 14,
                  background: msg.role === 'user' ? 'var(--ac)' : 'var(--c2)',
                  color: msg.role === 'user' ? 'white' : 'var(--t2)',
                  fontSize: 13, lineHeight: 1.5, whiteSpace: 'pre-wrap',
                  border: msg.role === 'assistant' ? '1px solid var(--bd)' : 'none',
                }}
              >
                {msg.content || ''}
              </div>
            ))}
            {chatLoading && (chatMessages.length === 0 || chatMessages[chatMessages.length - 1].role === 'user' || (chatMessages[chatMessages.length - 1].role === 'assistant' && !chatMessages[chatMessages.length - 1].content)) && (
              <div className="ai-thinking-card" style={{ alignSelf: 'flex-start', maxWidth: '85%' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 10, background: 'rgba(99,102,241,.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Bot size={16} style={{ color: 'var(--ac)', animation: 'aiIconBounce 1.2s ease-in-out infinite' }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 13, color: 'var(--td)' }}>Анализирую</span>
                    <div className="ai-search-dots" style={{ display: 'flex', gap: 4 }}>
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat input */}
          <form
            onSubmit={e => { e.preventDefault(); sendChatMessage() }}
            style={{
              display: 'flex', gap: 8, padding: '12px 16px',
              borderTop: '1px solid var(--bd)', background: 'var(--c1)',
            }}
          >
            <input
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder="Спросите про товар..."
              disabled={chatLoading}
              style={{
                flex: 1, padding: '10px 14px', borderRadius: 12,
                border: '1px solid var(--bd)', background: 'var(--c2)',
                color: 'var(--t)', fontSize: 13, outline: 'none',
              }}
            />
            <button
              type="submit"
              disabled={chatLoading || !chatInput.trim()}
              style={{
                padding: '10px 14px', borderRadius: 12,
                background: 'var(--ac)', color: 'white', border: 'none',
                cursor: 'pointer', opacity: chatLoading || !chatInput.trim() ? 0.4 : 1,
                display: 'flex', alignItems: 'center',
              }}
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default function ProductPage() {
  return (
    <Suspense fallback={
      <div style={{
        position: 'fixed', inset: 0, zIndex: 100,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        background: '#0A0B0F', fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}>
        <div style={{ fontSize: 32, fontWeight: 800, letterSpacing: 2, marginBottom: 24, background: 'linear-gradient(135deg, #F0F0F5, #6C5CE7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Smart Price</div>
        <div style={{ width: 260, height: 3, borderRadius: 3, background: '#2A2B3D', overflow: 'hidden' }}>
          <div style={{ width: '40%', height: '100%', borderRadius: 3, background: 'linear-gradient(90deg, #6C5CE7, #00D26A, #6C5CE7)', animation: 'spBarSlide 1.8s ease-in-out infinite', position: 'relative' }} />
        </div>
      </div>
    }>
      <ProductContent />
    </Suspense>
  )
}
