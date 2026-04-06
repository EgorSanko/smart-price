/**
 * ProductCard with improved UX
 */

'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useState } from 'react'
import { Star, Heart, TrendingDown, Check, ExternalLink } from 'lucide-react'
import { cn, formatPrice, calculateDiscount } from '@/lib/utils'
import type { Product } from '@/types'

interface ProductCardProps {
  product: Product
  showMarketplace?: boolean
  className?: string
}

const marketplaceConfig: Record<string, { name: string; color: string; url: string }> = {
  citilink: { name: 'Ситилинк', color: '#ff6600', url: 'https://citilink.ru' },
  regard: { name: 'Регард', color: '#e53935', url: 'https://regard.ru' },
  aliexpress: { name: 'AliExpress', color: '#ff4747', url: 'https://aliexpress.ru' },
  wildberries: { name: 'WB', color: '#cb11ab', url: 'https://wildberries.ru' },
  yandex_market: { name: 'Я.Маркет', color: '#ffcc00', url: 'https://market.yandex.ru' },
  yandex: { name: 'Я.Маркет', color: '#ffcc00', url: 'https://market.yandex.ru' },
  onliner: { name: 'Onliner', color: '#65cb02', url: 'https://catalog.onliner.by' },
}

const marketplaceIdToName: Record<number, string> = {
  1: 'citilink',
  2: 'wildberries',
  3: 'yandex_market',
  4: 'aliexpress',
}

function getMarketplace(product: Product) {
  const name = product.marketplace?.name || marketplaceIdToName[product.marketplace_id] || 'citilink'
  return marketplaceConfig[name] || marketplaceConfig.citilink
}

export function ProductCard({ product, showMarketplace = true, className }: ProductCardProps) {
  const [isLiked, setIsLiked] = useState(false)
  const [imageError, setImageError] = useState(false)
  const discount = calculateDiscount(product.current_price, product.original_price)
  const mp = getMarketplace(product)
  const reviewsCount = product.reviews_count ?? 0

  const handleLike = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsLiked(!isLiked)
  }

  const handleExternalLink = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    window.open(product.url || mp.url, '_blank')
  }

  return (
    <Link
      href={`/product/${product.id}`}
      className={cn(
        'group block bg-graphite-800 rounded-2xl overflow-hidden',
        'border border-graphite-600 hover:border-accent/30',
        'hover:bg-graphite-700 transition-all duration-200',
        'hover:shadow-card hover:-translate-y-1',
        className
      )}
    >
      {/* Image */}
      <div className="relative aspect-square bg-graphite-900 overflow-hidden">
        {product.image_url && !imageError ? (
          <Image
            src={product.image_url}
            alt={product.title}
            fill
            className="object-contain p-4 group-hover:scale-105 transition-transform duration-300"
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-txt-muted text-sm">
            <div className="text-center">
              <div className="w-16 h-16 bg-graphite-800 rounded-xl flex items-center justify-center mx-auto mb-2">
                📦
              </div>
              Нет фото
            </div>
          </div>
        )}

        {/* Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-start justify-between">
          {discount && discount >= 5 && (
            <span className="badge-discount">
              <TrendingDown className="w-3 h-3" />
              -{discount}%
            </span>
          )}
          <div className="flex gap-2 ml-auto">
            <button
              onClick={handleLike}
              className={cn(
                'p-2 rounded-full backdrop-blur transition-all',
                isLiked
                  ? 'bg-red-500 text-white'
                  : 'bg-graphite-800/80 text-txt-secondary opacity-0 group-hover:opacity-100 hover:text-red-500'
              )}
            >
              <Heart className={cn('w-4 h-4', isLiked && 'fill-current')} />
            </button>
          </div>
        </div>

        {/* Marketplace badge */}
        {showMarketplace && (
          <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
            <span
              className="text-xs font-semibold px-2.5 py-1 rounded-lg text-white shadow-lg"
              style={{ backgroundColor: mp.color }}
            >
              {mp.name}
            </span>
            <button
              onClick={handleExternalLink}
              className="p-2 rounded-lg bg-graphite-800/80 backdrop-blur text-txt-secondary opacity-0 group-hover:opacity-100 hover:text-accent-light transition-all"
              title="Открыть на сайте магазина"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Out of stock overlay */}
        {!product.is_available && (
          <div className="absolute inset-0 bg-graphite-950/80 flex items-center justify-center">
            <span className="bg-txt-primary text-graphite-950 text-sm font-medium px-4 py-2 rounded-full">
              Нет в наличии
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {product.brand && (
          <p className="text-xs font-medium text-accent-light uppercase tracking-wide mb-1">
            {product.brand}
          </p>
        )}

        <h3 className="text-sm font-medium text-txt-secondary line-clamp-2 mb-3 min-h-[40px] group-hover:text-txt-primary transition-colors">
          {product.title}
        </h3>

        {product.rating && (
          <div className="flex items-center gap-2 mb-3">
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
              <span className="text-sm font-medium text-txt-primary">{product.rating.toFixed(1)}</span>
            </div>
            {reviewsCount > 0 && (
              <span className="text-sm text-txt-muted">
                {reviewsCount.toLocaleString('ru-RU')} отзывов
              </span>
            )}
          </div>
        )}

        <div className="space-y-1">
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-txt-primary">
              {formatPrice(product.current_price, product.currency)}
            </span>
            {product.original_price && product.original_price > product.current_price && (
              <span className="text-sm text-txt-muted line-through">
                {formatPrice(product.original_price, product.currency)}
              </span>
            )}
          </div>

          {product.is_available && (
            <div className="flex items-center gap-1.5 text-accent-light">
              <Check className="w-4 h-4" />
              <span className="text-xs font-medium">В наличии</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

export function ProductCardSkeleton() {
  return (
    <div className="bg-graphite-800 rounded-2xl border border-graphite-600 overflow-hidden animate-pulse">
      <div className="aspect-square bg-graphite-700" />
      <div className="p-4 space-y-3">
        <div className="h-3 bg-graphite-700 rounded w-1/4" />
        <div className="space-y-2">
          <div className="h-4 bg-graphite-700 rounded w-full" />
          <div className="h-4 bg-graphite-700 rounded w-3/4" />
        </div>
        <div className="h-4 bg-graphite-700 rounded w-1/3" />
        <div className="h-6 bg-graphite-700 rounded w-1/2" />
      </div>
    </div>
  )
}
