/**
 * Product-related TypeScript types
 */

export interface Marketplace {
  id: number
  name: string
  display_name: string
  base_url: string
  is_active: boolean
}

export interface Category {
  id: number
  name: string
  slug: string
  parent_id: number | null
  level: number
}

export interface Product {
  id: number
  external_id: string
  marketplace_id: number
  marketplace?: Marketplace
  title: string
  description: string | null
  brand: string | null
  category_id: number | null
  category?: Category
  current_price: number
  original_price: number | null
  currency: string
  url: string
  image_url: string | null
  images: string[]
  rating: number | null
  reviews_count: number
  specs: Record<string, string | number> | null
  is_available: boolean
  seller_name: string | null
  seller_rating: number | null
  barcode: string | null
  created_at: string
  updated_at: string
  last_scraped_at: string | null
}

export interface PricePoint {
  price: number
  original_price: number | null
  recorded_at: string
}

export interface PriceStats {
  min_price: number
  max_price: number
  avg_price: number
  current_vs_min_percent: number
  trend: 'rising' | 'falling' | 'stable'
}

export interface ProductWithHistory extends Product {
  price_history: PricePoint[]
  price_stats: PriceStats
}

export interface MatchedProduct {
  product: Product
  marketplace_name: string
  confidence_score: number
}

export interface ProductComparison {
  canonical_title: string
  brand: string | null
  matches: MatchedProduct[]
  best_price: MatchedProduct
  price_difference_percent: number
}

export interface PriceForecast {
  product_id: number
  forecast_days: number
  predictions: Array<{
    date: string
    predicted_price: number
    lower_bound: number
    upper_bound: number
  }>
  recommendation: {
    action: 'buy_now' | 'wait' | 'neutral'
    reason: string
    best_date: string | null
    expected_price: number | null
  }
}

export type MarketplaceName = 'ozon' | 'wildberries' | 'yandex_market' | 'aliexpress'

export const MARKETPLACE_COLORS: Record<MarketplaceName, string> = {
  ozon: '#005bff',
  wildberries: '#cb11ab',
  yandex_market: '#ffcc00',
  aliexpress: '#ff4747',
}

export const MARKETPLACE_NAMES: Record<MarketplaceName, string> = {
  ozon: 'Ozon',
  wildberries: 'Wildberries',
  yandex_market: 'Яндекс Маркет',
  aliexpress: 'AliExpress',
}
