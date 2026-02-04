/**
 * API-related TypeScript types
 */

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface SearchParams {
  q: string
  marketplace_ids?: number[]
  min_price?: number
  max_price?: number
  in_stock?: boolean
  sort_by?: 'relevance' | 'price_asc' | 'price_desc' | 'rating'
  page?: number
  per_page?: number
}

export interface SearchFacets {
  marketplaces: Record<string, number>
  price: {
    min_price: number
    max_price: number
    avg_price: number
    median_price: number
  }
  brands: Record<string, number>
}

export interface SearchResponse<T> {
  products: T[]
  total: number
  page: number
  per_page: number
  facets: SearchFacets | null
}

export interface ApiError {
  detail: string
  code?: string
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy'
  version: string
  services: {
    database: boolean
    redis: boolean
    qdrant: boolean
  }
}

export interface SuggestionItem {
  text: string
  type: string
  count: number
}

export interface SuggestResponse {
  suggestions: Array<string | SuggestionItem>
  products: Array<{
    id: number
    title: string
    image_url: string | null
    price: number
  }>
}
