/**
 * Compare page with working data
 */

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Search, Plus, X, ArrowRight, TrendingDown, ExternalLink, Trash2 } from 'lucide-react'
import { MOCK_PRODUCTS } from '@/lib/api'
import { formatPrice } from '@/lib/utils'

interface CompareItem {
  id: number
  title: string
  brand: string | undefined
  image: string | undefined
  prices: {
    marketplace: string
    price: number
    url: string
    color: string
  }[]
}

export default function ComparePage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  
  // Initialize with first 2 products from mock data
  const [compareItems, setCompareItems] = useState<CompareItem[]>(() => {
    return MOCK_PRODUCTS.slice(0, 2).map(p => ({
      id: p.id,
      title: p.title,
      brand: p.brand,
      image: p.image_url,
      prices: [
        { marketplace: 'Ozon', price: p.current_price, url: 'https://ozon.ru', color: '#005bff' },
        { marketplace: 'Wildberries', price: Math.round(p.current_price * 1.03), url: 'https://wildberries.ru', color: '#cb11ab' },
        { marketplace: 'Яндекс Маркет', price: Math.round(p.current_price * 1.05), url: 'https://market.yandex.ru', color: '#ffcc00' },
      ]
    }))
  })

  const removeItem = (id: number) => {
    setCompareItems(compareItems.filter(item => item.id !== id))
  }

  const addItem = (product: typeof MOCK_PRODUCTS[0]) => {
    if (compareItems.find(item => item.id === product.id)) return
    if (compareItems.length >= 4) return
    
    setCompareItems([...compareItems, {
      id: product.id,
      title: product.title,
      brand: product.brand,
      image: product.image_url,
      prices: [
        { marketplace: 'Ozon', price: product.current_price, url: 'https://ozon.ru', color: '#005bff' },
        { marketplace: 'Wildberries', price: Math.round(product.current_price * 1.03), url: 'https://wildberries.ru', color: '#cb11ab' },
        { marketplace: 'Яндекс Маркет', price: Math.round(product.current_price * 1.05), url: 'https://market.yandex.ru', color: '#ffcc00' },
      ]
    }])
    setShowSearch(false)
    setSearchQuery('')
  }

  const getBestPrice = (item: CompareItem) => Math.min(...item.prices.map(p => p.price))

  const filteredProducts = MOCK_PRODUCTS.filter(p => 
    !compareItems.find(item => item.id === p.id) &&
    (p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
     p.brand?.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="min-h-screen py-8">
      <div className="container">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-txt-primary mb-2">Сравнение цен</h1>
            <p className="text-txt-secondary">Сравните цены на товары с разных маркетплейсов</p>
          </div>
          {compareItems.length < 4 && (
            <button
              onClick={() => setShowSearch(true)}
              className="btn-primary"
            >
              <Plus className="w-5 h-5" />
              Добавить товар
            </button>
          )}
        </div>

        {/* Search modal */}
        {showSearch && (
          <div className="fixed inset-0 z-50 flex items-start justify-center pt-20">
            <div className="absolute inset-0 bg-black/70" onClick={() => setShowSearch(false)} />
            <div className="relative w-full max-w-2xl bg-graphite-800 rounded-2xl border border-graphite-600 shadow-card overflow-hidden">
              <div className="p-4 border-b border-graphite-600">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-txt-muted" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Найти товар для сравнения..."
                    className="w-full pl-12 pr-4 py-3 bg-graphite-700 border border-graphite-600 rounded-xl text-txt-primary placeholder:text-txt-muted focus:outline-none focus:ring-2 focus:ring-accent"
                    autoFocus
                  />
                </div>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {filteredProducts.length > 0 ? (
                  filteredProducts.slice(0, 6).map(product => (
                    <button
                      key={product.id}
                      onClick={() => addItem(product)}
                      className="w-full flex items-center gap-4 p-4 hover:bg-graphite-700 transition-colors text-left"
                    >
                      <div className="w-16 h-16 bg-graphite-700 rounded-xl flex-shrink-0 overflow-hidden">
                        {product.image_url ? (
                          <img src={product.image_url} alt="" className="w-full h-full object-contain p-1" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-2xl">📦</div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-accent-light font-medium mb-1">{product.brand}</p>
                        <p className="text-txt-primary font-medium truncate">{product.title}</p>
                        <p className="text-txt-secondary text-sm">{formatPrice(product.current_price)}</p>
                      </div>
                      <Plus className="w-5 h-5 text-txt-muted" />
                    </button>
                  ))
                ) : (
                  <div className="p-8 text-center text-txt-muted">
                    {searchQuery ? 'Ничего не найдено' : 'Введите название товара'}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Comparison */}
        {compareItems.length > 0 ? (
          <div className="space-y-6">
            {compareItems.map((item) => {
              const bestPrice = getBestPrice(item)
              return (
                <div key={item.id} className="card p-6">
                  <div className="flex flex-col lg:flex-row gap-6">
                    {/* Product info */}
                    <div className="flex gap-4 lg:w-1/3">
                      <Link 
                        href={`/product/${item.id}`}
                        className="w-24 h-24 bg-graphite-700 rounded-xl flex-shrink-0 overflow-hidden hover:ring-2 hover:ring-accent/50 transition-all"
                      >
                        {item.image ? (
                          <img src={item.image} alt={item.title} className="w-full h-full object-contain p-2" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-3xl">📦</div>
                        )}
                      </Link>
                      <div className="flex-1 min-w-0">
                        {item.brand && <p className="text-xs text-accent-light font-medium mb-1">{item.brand}</p>}
                        <Link href={`/product/${item.id}`}>
                          <h3 className="font-semibold text-txt-primary mb-2 line-clamp-2 hover:text-accent-light transition-colors">
                            {item.title}
                          </h3>
                        </Link>
                        <div className="flex items-center gap-2 text-accent-light">
                          <TrendingDown className="w-4 h-4" />
                          <span className="text-sm font-medium">Лучшая: {formatPrice(bestPrice)}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => removeItem(item.id)}
                        className="p-2 text-txt-muted hover:text-red-500 transition-colors self-start"
                        title="Удалить из сравнения"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>

                    {/* Prices */}
                    <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-4">
                      {item.prices.map((price) => {
                        const isBest = price.price === bestPrice
                        return (
                          <div
                            key={price.marketplace}
                            className={`p-4 rounded-xl border transition-all ${
                              isBest 
                                ? 'bg-accent/10 border-accent/30 ring-1 ring-accent/20' 
                                : 'bg-graphite-700 border-graphite-600 hover:border-graphite-500'
                            }`}
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: price.color }} />
                              <span className="text-sm font-medium text-txt-secondary">{price.marketplace}</span>
                              {isBest && (
                                <span className="text-xs bg-accent text-white px-2 py-0.5 rounded-full ml-auto">
                                  Лучшая
                                </span>
                              )}
                            </div>
                            <p className={`text-xl font-bold ${isBest ? 'text-accent-light' : 'text-txt-primary'}`}>
                              {formatPrice(price.price)}
                            </p>
                            <a
                              href={price.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-sm text-txt-muted hover:text-accent-light mt-2 transition-colors"
                            >
                              Перейти <ExternalLink className="w-3 h-3" />
                            </a>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="card p-12 text-center">
            <div className="w-16 h-16 bg-graphite-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-txt-muted" />
            </div>
            <h3 className="text-lg font-semibold text-txt-primary mb-2">Нет товаров для сравнения</h3>
            <p className="text-txt-secondary mb-6">Добавьте товары для сравнения цен</p>
            <button onClick={() => setShowSearch(true)} className="btn-primary">
              <Plus className="w-5 h-5" />
              Добавить товар
            </button>
          </div>
        )}

        {/* Tips */}
        {compareItems.length > 0 && (
          <div className="mt-8 p-6 bg-accent/10 border border-accent/20 rounded-2xl">
            <h3 className="font-semibold text-accent-light mb-2">💡 Совет</h3>
            <p className="text-txt-secondary text-sm">
              Нажмите на изображение или название товара, чтобы перейти на страницу с подробной информацией и историей цен.
              Вы можете сравнивать до 4 товаров одновременно.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
