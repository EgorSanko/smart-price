/**
 * Product detail page with mock data
 */

'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useState } from 'react'
import { 
  ArrowLeft, 
  Heart, 
  Bell, 
  ExternalLink, 
  Star, 
  TrendingDown, 
  TrendingUp,
  Check,
  Share2,
  ShoppingCart
} from 'lucide-react'
import { MOCK_PRODUCTS } from '@/lib/api'
import { formatPrice } from '@/lib/utils'

// Extended product data for detail page
const PRICE_COMPARISONS: Record<number, { marketplace: string; price: number; original: number | null; url: string; color: string; available: boolean }[]> = {
  1: [
    { marketplace: 'Ozon', price: 94990, original: 109990, url: 'https://ozon.ru', color: '#005bff', available: true },
    { marketplace: 'Wildberries', price: 97500, original: 109990, url: 'https://wildberries.ru', color: '#cb11ab', available: true },
    { marketplace: 'Яндекс Маркет', price: 99990, original: 109990, url: 'https://market.yandex.ru', color: '#ffcc00', available: true },
    { marketplace: 'AliExpress', price: 89990, original: null, url: 'https://aliexpress.ru', color: '#ff4747', available: false },
  ],
  // Default for other products
}

const SPECS: Record<number, Record<string, string>> = {
  1: {
    'Дисплей': '6.1" Super Retina XDR',
    'Процессор': 'Apple A17 Pro',
    'Память': '256 GB',
    'Камера': '48 Мп + 12 Мп + 12 Мп',
    'Батарея': '3274 мАч',
    'ОС': 'iOS 17',
  },
  3: {
    'Дисплей': '6.8" Dynamic AMOLED 2X',
    'Процессор': 'Snapdragon 8 Gen 3',
    'Память': '256 GB',
    'Камера': '200 Мп + 12 Мп + 50 Мп + 10 Мп',
    'Батарея': '5000 мАч',
    'ОС': 'Android 14',
  },
  4: {
    'Тип': 'TWS (полностью беспроводные)',
    'Активное шумоподавление': 'Да',
    'Время работы': 'до 6 часов',
    'Разъём зарядки': 'USB-C / MagSafe',
    'Защита': 'IP54',
  },
}

export default function ProductPage() {
  const params = useParams()
  const productId = parseInt(params.id as string)
  
  const [isLiked, setIsLiked] = useState(false)
  const [showAlert, setShowAlert] = useState(false)
  
  // Find product from mock data
  const product = MOCK_PRODUCTS.find(p => p.id === productId)
  
  if (!product) {
    return (
      <div className="min-h-screen py-16">
        <div className="container text-center">
          <h1 className="text-2xl font-bold text-txt-primary mb-4">Товар не найден</h1>
          <Link href="/search" className="btn-primary">
            Вернуться к поиску
          </Link>
        </div>
      </div>
    )
  }

  // Get prices for this product or generate based on current price
  const prices = PRICE_COMPARISONS[productId] || [
    { marketplace: 'Ozon', price: product.current_price, original: product.original_price, url: 'https://ozon.ru', color: '#005bff', available: true },
    { marketplace: 'Wildberries', price: Math.round(product.current_price * 1.03), original: product.original_price, url: 'https://wildberries.ru', color: '#cb11ab', available: true },
    { marketplace: 'Яндекс Маркет', price: Math.round(product.current_price * 1.05), original: product.original_price, url: 'https://market.yandex.ru', color: '#ffcc00', available: true },
  ]

  const specs = SPECS[productId] || {
    'Бренд': product.brand || 'Не указан',
    'Артикул': product.external_id,
  }

  const bestPrice = Math.min(...prices.filter(p => p.available).map(p => p.price))
  const bestOffer = prices.find(p => p.price === bestPrice && p.available)
  
  const priceHistory = {
    min: Math.round(bestPrice * 0.85),
    max: Math.round(bestPrice * 1.2),
    avg: Math.round(bestPrice * 1.05),
    trend: 'down' as const,
  }

  return (
    <div className="min-h-screen py-8">
      <div className="container">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link href="/search" className="inline-flex items-center gap-2 text-txt-secondary hover:text-accent-light transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Назад к поиску
          </Link>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Image */}
          <div className="space-y-4">
            <div className="card aspect-square flex items-center justify-center overflow-hidden bg-graphite-900">
              {product.image_url ? (
                <img 
                  src={product.image_url} 
                  alt={product.title} 
                  className="max-w-full max-h-full object-contain p-8"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none'
                  }}
                />
              ) : (
                <div className="text-txt-muted text-center">
                  <div className="text-6xl mb-4">📦</div>
                  <p>Нет изображения</p>
                </div>
              )}
            </div>
          </div>

          {/* Info */}
          <div className="space-y-6">
            {/* Title */}
            <div>
              {product.brand && (
                <p className="text-sm font-medium text-accent-light uppercase tracking-wide mb-1">{product.brand}</p>
              )}
              <h1 className="text-2xl lg:text-3xl font-bold text-txt-primary mb-3">{product.title}</h1>
              {product.rating && (
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1">
                    <Star className="w-5 h-5 fill-amber-400 text-amber-400" />
                    <span className="font-semibold text-txt-primary">{product.rating.toFixed(1)}</span>
                    <span className="text-txt-muted">({product.reviews_count?.toLocaleString()} отзывов)</span>
                  </div>
                </div>
              )}
            </div>

            {/* Best price card */}
            <div className="card p-6 bg-accent/10 border-accent/30">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm text-txt-secondary mb-1">Лучшая цена</p>
                  <p className="text-3xl font-bold text-accent-light">{formatPrice(bestPrice)}</p>
                  {bestOffer?.original && (
                    <p className="text-txt-muted line-through">{formatPrice(bestOffer.original)}</p>
                  )}
                </div>
                {bestOffer && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/20">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: bestOffer.color }} />
                    <span className="text-sm font-medium text-accent-light">{bestOffer.marketplace}</span>
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                <a
                  href={bestOffer?.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 btn-primary justify-center"
                >
                  <ShoppingCart className="w-5 h-5" />
                  Купить
                  <ExternalLink className="w-4 h-4" />
                </a>
                <button 
                  onClick={() => setIsLiked(!isLiked)}
                  className={`p-3 rounded-xl border transition-colors ${
                    isLiked 
                      ? 'bg-red-500 border-red-500 text-white' 
                      : 'bg-graphite-800 border-graphite-600 text-txt-secondary hover:text-red-500 hover:border-red-500/30'
                  }`}
                >
                  <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
                </button>
                <button 
                  onClick={() => setShowAlert(true)}
                  className="p-3 rounded-xl bg-graphite-800 border border-graphite-600 text-txt-secondary hover:text-accent-light hover:border-accent/30 transition-colors"
                >
                  <Bell className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Alert modal */}
            {showAlert && (
              <div className="card p-4 border-accent/30 bg-accent/5">
                <p className="text-sm text-txt-secondary mb-3">
                  🔔 Уведомление будет отправлено когда цена упадёт ниже текущей
                </p>
                <div className="flex gap-2">
                  <button 
                    onClick={() => setShowAlert(false)} 
                    className="btn-primary flex-1 justify-center text-sm"
                  >
                    Подписаться на снижение
                  </button>
                  <button 
                    onClick={() => setShowAlert(false)}
                    className="px-4 py-2 text-sm text-txt-muted hover:text-txt-primary"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}

            {/* All prices */}
            <div className="card p-6">
              <h3 className="font-semibold text-txt-primary mb-4">Цены на маркетплейсах</h3>
              <div className="space-y-3">
                {prices.map((p) => {
                  const isBest = p.price === bestPrice && p.available
                  return (
                    <div
                      key={p.marketplace}
                      className={`flex items-center justify-between p-3 rounded-xl transition-colors ${
                        p.available 
                          ? isBest ? 'bg-accent/10 border border-accent/30' : 'bg-graphite-700 hover:bg-graphite-600' 
                          : 'bg-graphite-800 opacity-50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: p.color }} />
                        <span className="font-medium text-txt-primary">{p.marketplace}</span>
                        {isBest && <span className="text-xs bg-accent text-white px-2 py-0.5 rounded-full">Лучшая</span>}
                        {!p.available && <span className="text-xs text-txt-muted">(нет в наличии)</span>}
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className={`font-semibold ${isBest ? 'text-accent-light' : 'text-txt-primary'}`}>
                            {formatPrice(p.price)}
                          </p>
                          {p.original && <p className="text-xs text-txt-muted line-through">{formatPrice(p.original)}</p>}
                        </div>
                        {p.available && (
                          <a
                            href={p.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 rounded-lg text-txt-muted hover:text-accent-light hover:bg-graphite-600 transition-colors"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Price history */}
            <div className="card p-6">
              <h3 className="font-semibold text-txt-primary mb-4">Динамика цен</h3>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 bg-graphite-700 rounded-xl">
                  <p className="text-sm text-txt-muted mb-1">Минимум</p>
                  <p className="font-semibold text-accent-light">{formatPrice(priceHistory.min)}</p>
                </div>
                <div className="text-center p-3 bg-graphite-700 rounded-xl">
                  <p className="text-sm text-txt-muted mb-1">Средняя</p>
                  <p className="font-semibold text-txt-primary">{formatPrice(priceHistory.avg)}</p>
                </div>
                <div className="text-center p-3 bg-graphite-700 rounded-xl">
                  <p className="text-sm text-txt-muted mb-1">Максимум</p>
                  <p className="font-semibold text-txt-secondary">{formatPrice(priceHistory.max)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-3 rounded-xl bg-green-500/10 border border-green-500/20">
                <TrendingDown className="w-5 h-5 text-green-400" />
                <span className="text-sm text-txt-secondary">Цена снижается — хорошее время для покупки!</span>
              </div>
            </div>

            {/* Specs */}
            <div className="card p-6">
              <h3 className="font-semibold text-txt-primary mb-4">Характеристики</h3>
              <dl className="space-y-3">
                {Object.entries(specs).map(([key, value]) => (
                  <div key={key} className="flex justify-between py-2 border-b border-graphite-600 last:border-0">
                    <dt className="text-txt-muted">{key}</dt>
                    <dd className="text-txt-primary font-medium text-right">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
