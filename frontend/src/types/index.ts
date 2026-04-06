export interface Product {
  id: number
  external_id: string
  marketplace_id: number
  title: string
  brand?: string
  current_price: number
  original_price?: number
  currency: string
  url: string
  image_url?: string
  rating?: number
  reviews_count?: number
  is_available: boolean
  marketplace?: { name: string }
}

export interface SearchParams {
  q: string
  marketplace_ids?: number[]
  min_price?: number
  max_price?: number
  in_stock?: boolean
  sort_by?: string
  page?: number
  per_page?: number
}

export interface SearchResponse {
  products: Product[]
  total: number
  page: number
  per_page: number
  facets?: {
    marketplaces: Record<string, number>
    price: {
      min_price: number
      max_price: number
      avg_price: number
    }
  }
}
