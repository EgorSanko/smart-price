/**
 * Cheaper feature API client — POST to create, WS to stream.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

export type CheaperStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface CheaperOffer {
  domain: string
  price: number
  product_name?: string | null
  product_url?: string | null
  img_url?: string | null
  rating?: number | null
  review_cnt?: number | null
}

export interface CheaperPlannedShop {
  domain: string
}

export interface CheaperSnapshot {
  task_id: string
  status: CheaperStatus
  url: string
  orig_domain?: string | null
  product_name?: string | null
  product_img_url?: string | null
  orig_price?: number | null
  currency?: string | null
  planned_shops?: CheaperPlannedShop[] | null
  offers?: CheaperOffer[] | null
  error?: string | null
  created_at: string
  started_at?: string | null
  finished_at?: string | null
}

export interface CheaperEvent {
  type: 'snapshot' | 'started' | 'planned_shops' | 'offer' | 'progress' | 'product_name' | 'done' | 'error'
  task_id: string
  data?: Record<string, unknown>
}

export async function createCheaperSearch(url: string): Promise<{ task_id: string; status: CheaperStatus }> {
  const res = await fetch(`${API_URL}/api/v1/cheaper/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!res.ok) throw new Error(`Failed to create task: ${res.status}`)
  return res.json()
}

export async function getCheaperSearch(taskId: string): Promise<CheaperSnapshot> {
  const res = await fetch(`${API_URL}/api/v1/cheaper/${taskId}`)
  if (!res.ok) throw new Error(`Failed to fetch task: ${res.status}`)
  return res.json()
}

export interface CheaperSubscription {
  close: () => void
}

export function subscribeCheaper(
  taskId: string,
  onEvent: (event: CheaperEvent) => void,
  onError?: (err: Event) => void,
): CheaperSubscription {
  const base = API_URL.replace(/^http/, 'ws') || (typeof window !== 'undefined'
    ? (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host
    : '')
  const ws = new WebSocket(`${base}/api/v1/cheaper/ws/${taskId}`)
  ws.onmessage = (msg) => {
    try { onEvent(JSON.parse(msg.data)) } catch { /* ignore */ }
  }
  if (onError) ws.onerror = onError
  return { close: () => { try { ws.close() } catch { /* ignore */ } } }
}
