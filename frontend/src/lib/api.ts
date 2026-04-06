/**
 * Smart Price API Client
 * Connects to FastAPI backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

// Типы данных
export interface Product {
  title: string
  price: string
  price_num: number
  url: string
  marketplace: 'onliner' | 'yandex' | 'citilink' | 'wildberries' | 'regard' | 'aliexpress'
  image: string
  shop: string
  specs?: string
  category?: string
  category_key?: string
  onliner_key?: string
}

export interface SearchStreamEvent {
  status: 'start' | 'parsing' | 'done' | 'error' | 'complete' | 'corrected'
  query?: string
  original?: string
  corrected?: string
  region?: string
  sources?: string[]
  source?: string
  name?: string
  count?: number
  error?: string
  results?: Product[]
  products?: Product[]
  total?: number
}

export interface PriceHistoryResponse {
  product_key: string
  days: number
  history: {
    price: number
    currency: string
    date: string
    name?: string
    shop?: string
  }[]
  stats: {
    min: number
    max: number
    avg: number
    count: number
    current?: number
    first_seen: string
    last_seen: string
  }
  has_data: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

// SSE Search (live marketplace scraping)
export function searchProducts(
  query: string,
  region: string = 'all',
  onEvent: (event: SearchStreamEvent) => void,
  onError?: (error: Error) => void
): () => void {
  const url = `${API_URL}/api/v1/live-search/stream?q=${encodeURIComponent(query)}&region=${region}`

  const eventSource = new EventSource(url)

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data) as SearchStreamEvent
      onEvent(data)

      if (data.status === 'complete') {
        eventSource.close()
      }
    } catch (err) {
      console.error('Parse error:', err)
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    onError?.(new Error('Connection error'))
  }

  // Return cleanup function
  return () => eventSource.close()
}

// AI Chat (SSE)
export function chatWithAI(
  message: string,
  history: ChatMessage[],
  region: string = 'all',
  productsContext: string = '',
  onChunk: (data: { text?: string; searching?: boolean; query?: string; products?: Product[]; done?: boolean }) => void,
  onError?: (error: Error) => void
): () => void {
  const controller = new AbortController()

  fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history,
      region,
      products_context: productsContext,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) throw new Error('Chat error')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onChunk(data)
            } catch { /* ignore parse errors */ }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })

  return () => controller.abort()
}

// AI Compare (SSE)
export function compareProducts(
  products: Product[],
  onChunk: (data: { text?: string; done?: boolean }) => void,
  onError?: (error: Error) => void
): () => void {
  const controller = new AbortController()

  fetch(`${API_URL}/api/v1/ai/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ products }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) throw new Error('Compare error')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onChunk(data)
            } catch { /* ignore parse errors */ }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })

  return () => controller.abort()
}

// ── Analyze Price types ────────────────────────────────────────────────────────

export interface PriceStats {
  min: number
  median: number
  mean: number
  max: number
  stdev: number
  count: number
  currency: string
}

export interface OfferLite {
  title: string
  price_num: number
  currency: string
  shop: string | null
  marketplace: string
  url: string
  image: string | null
}

export interface RedFlag {
  severity: 'info' | 'warn' | 'danger'
  text: string
}

export interface AnalyzeResult {
  query: string
  region: 'BY' | 'RU'
  currency: string
  verdict: 'good' | 'fair' | 'bad'
  score: number
  stats: PriceStats
  best_offer: OfferLite
  red_flags: RedFlag[]
  value_analysis: string
  alternatives: { cheaper: OfferLite[]; pricier: OfferLite[] }
  generated_at: string
}

export type AnalyzeStreamEvent =
  | { status: 'start'; query: string; region: string }
  | { status: 'parsing'; sources?: string[]; source?: string }
  | { status: 'scraped'; total: number }
  | { status: 'stats'; stats: PriceStats }
  | { status: 'analyzing' }
  | { status: 'result'; payload: AnalyzeResult }
  | { status: 'error'; message: string }

export function analyzePrice(
  query: string,
  region: 'BY' | 'RU',
  onEvent: (ev: AnalyzeStreamEvent) => void,
  onError: (err: string) => void
): () => void {
  const url = `${API_URL}/api/v1/analyze/stream?q=${encodeURIComponent(query)}&region=${region}`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data) as AnalyzeStreamEvent
      onEvent(data)
      if (data.status === 'result' || data.status === 'error') {
        eventSource.close()
      }
    } catch (err) {
      console.error('Analyze parse error:', err)
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    onError('Ошибка соединения с сервером')
  }

  return () => eventSource.close()
}

// Price History
export async function getPriceHistory(productKey: string, days: number = 30): Promise<PriceHistoryResponse | null> {
  try {
    const response = await fetch(
      `${API_URL}/api/v1/products/history?product_key=${encodeURIComponent(productKey)}&days=${days}`
    )
    if (!response.ok) return null
    return await response.json()
  } catch {
    return null
  }
}

// Image proxy (bypass hotlink protection)
export function proxyImage(url: string): string {
  if (!url) return ''
  return `${API_URL}/api/v1/image-proxy?url=${encodeURIComponent(url)}`
}

// Health check
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/api/v1/health`)
    return response.ok
  } catch {
    return false
  }
}

// List available parsers
export async function getParsers(): Promise<Record<string, { name: string; enabled: boolean; color: string; region: string }> | null> {
  try {
    const response = await fetch(`${API_URL}/api/v1/parsers`)
    if (!response.ok) return null
    return await response.json()
  } catch {
    return null
  }
}
