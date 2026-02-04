/**
 * API client with mock data for demo
 */

import type { Product, SearchParams } from '@/types'

// Mock data
const MOCK_PRODUCTS: Product[] = [
  {
    id: 1,
    external_id: 'ozon-1',
    marketplace_id: 1,
    title: 'Apple iPhone 15 Pro 256GB Natural Titanium',
    brand: 'Apple',
    current_price: 94990,
    original_price: 109990,
    currency: 'RUB',
    url: 'https://ozon.ru/product/1',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-p/wc1000/6923153689.jpg',
    rating: 4.9,
    reviews_count: 2847,
    is_available: true,
    marketplace: { name: 'ozon' },
  },
  {
    id: 2,
    external_id: 'wb-1',
    marketplace_id: 2,
    title: 'Apple iPhone 15 Pro 256GB Black Titanium',
    brand: 'Apple',
    current_price: 97500,
    original_price: 109990,
    currency: 'RUB',
    url: 'https://wildberries.ru/product/1',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-p/wc1000/6923153689.jpg',
    rating: 4.8,
    reviews_count: 1523,
    is_available: true,
    marketplace: { name: 'wildberries' },
  },
  {
    id: 3,
    external_id: 'ozon-2',
    marketplace_id: 1,
    title: 'Samsung Galaxy S24 Ultra 256GB Titanium Black',
    brand: 'Samsung',
    current_price: 89990,
    original_price: 104990,
    currency: 'RUB',
    url: 'https://ozon.ru/product/2',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-j/wc1000/7038629467.jpg',
    rating: 4.7,
    reviews_count: 1892,
    is_available: true,
    marketplace: { name: 'ozon' },
  },
  {
    id: 4,
    external_id: 'wb-2',
    marketplace_id: 2,
    title: 'Apple AirPods Pro 2 с USB-C',
    brand: 'Apple',
    current_price: 21990,
    original_price: 24990,
    currency: 'RUB',
    url: 'https://wildberries.ru/product/2',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-z/wc1000/6812149651.jpg',
    rating: 4.9,
    reviews_count: 5621,
    is_available: true,
    marketplace: { name: 'wildberries' },
  },
  {
    id: 5,
    external_id: 'ym-1',
    marketplace_id: 3,
    title: 'Sony PlayStation 5 Slim',
    brand: 'Sony',
    current_price: 57990,
    original_price: 64990,
    currency: 'RUB',
    url: 'https://market.yandex.ru/product/1',
    image_url: 'https://ir.ozone.ru/s3/multimedia-o/wc1000/6285268688.jpg',
    rating: 4.8,
    reviews_count: 3421,
    is_available: true,
    marketplace: { name: 'yandex_market' },
  },
  {
    id: 6,
    external_id: 'ozon-3',
    marketplace_id: 1,
    title: 'Xiaomi Robot Vacuum S10+ Робот-пылесос',
    brand: 'Xiaomi',
    current_price: 24990,
    original_price: 34990,
    currency: 'RUB',
    url: 'https://ozon.ru/product/3',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-x/wc1000/6949149393.jpg',
    rating: 4.6,
    reviews_count: 892,
    is_available: true,
    marketplace: { name: 'ozon' },
  },
  {
    id: 7,
    external_id: 'wb-3',
    marketplace_id: 2,
    title: 'MacBook Air 15 M2 256GB Space Gray',
    brand: 'Apple',
    current_price: 124990,
    original_price: 139990,
    currency: 'RUB',
    url: 'https://wildberries.ru/product/3',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-9/wc1000/6789556285.jpg',
    rating: 4.9,
    reviews_count: 1247,
    is_available: true,
    marketplace: { name: 'wildberries' },
  },
  {
    id: 8,
    external_id: 'ali-1',
    marketplace_id: 4,
    title: 'Наушники Sony WH-1000XM5 Black',
    brand: 'Sony',
    current_price: 28990,
    original_price: 34990,
    currency: 'RUB',
    url: 'https://aliexpress.ru/product/1',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-i/wc1000/6543289678.jpg',
    rating: 4.8,
    reviews_count: 2156,
    is_available: true,
    marketplace: { name: 'aliexpress' },
  },
  {
    id: 9,
    external_id: 'ozon-4',
    marketplace_id: 1,
    title: 'Телевизор Samsung QE55Q80C 55" QLED 4K',
    brand: 'Samsung',
    current_price: 84990,
    original_price: 99990,
    currency: 'RUB',
    url: 'https://ozon.ru/product/4',
    image_url: 'https://ir.ozone.ru/s3/multimedia-m/wc1000/6341256789.jpg',
    rating: 4.7,
    reviews_count: 567,
    is_available: true,
    marketplace: { name: 'ozon' },
  },
  {
    id: 10,
    external_id: 'wb-4',
    marketplace_id: 2,
    title: 'Apple Watch Series 9 45mm GPS',
    brand: 'Apple',
    current_price: 39990,
    original_price: 44990,
    currency: 'RUB',
    url: 'https://wildberries.ru/product/4',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-k/wc1000/6890123456.jpg',
    rating: 4.8,
    reviews_count: 1823,
    is_available: true,
    marketplace: { name: 'wildberries' },
  },
  {
    id: 11,
    external_id: 'ym-2',
    marketplace_id: 3,
    title: 'Dyson V15 Detect Absolute',
    brand: 'Dyson',
    current_price: 69990,
    original_price: 79990,
    currency: 'RUB',
    url: 'https://market.yandex.ru/product/2',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-l/wc1000/6234567890.jpg',
    rating: 4.9,
    reviews_count: 2341,
    is_available: true,
    marketplace: { name: 'yandex_market' },
  },
  {
    id: 12,
    external_id: 'ozon-5',
    marketplace_id: 1,
    title: 'iPad Pro 11" M2 128GB Wi-Fi',
    brand: 'Apple',
    current_price: 79990,
    original_price: 89990,
    currency: 'RUB',
    url: 'https://ozon.ru/product/5',
    image_url: 'https://ir.ozone.ru/s3/multimedia-1-m/wc1000/6345678901.jpg',
    rating: 4.9,
    reviews_count: 1567,
    is_available: true,
    marketplace: { name: 'ozon' },
  },
]

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// Search products with filtering
export async function searchProducts(params: SearchParams) {
  await delay(300 + Math.random() * 500) // 300-800ms delay
  
  let filtered = [...MOCK_PRODUCTS]
  
  // Filter by query
  if (params.q) {
    const query = params.q.toLowerCase()
    filtered = filtered.filter(p => 
      p.title.toLowerCase().includes(query) ||
      p.brand?.toLowerCase().includes(query)
    )
  }
  
  // Filter by marketplace
  if (params.marketplace_ids?.length) {
    filtered = filtered.filter(p => params.marketplace_ids!.includes(p.marketplace_id))
  }
  
  // Filter by price
  if (params.min_price !== undefined) {
    filtered = filtered.filter(p => p.current_price >= params.min_price!)
  }
  if (params.max_price !== undefined) {
    filtered = filtered.filter(p => p.current_price <= params.max_price!)
  }
  
  // Filter by availability
  if (params.in_stock) {
    filtered = filtered.filter(p => p.is_available)
  }
  
  // Sort
  switch (params.sort_by) {
    case 'price_asc':
      filtered.sort((a, b) => a.current_price - b.current_price)
      break
    case 'price_desc':
      filtered.sort((a, b) => b.current_price - a.current_price)
      break
    case 'rating':
      filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0))
      break
  }
  
  // Pagination
  const page = params.page || 1
  const perPage = params.per_page || 20
  const start = (page - 1) * perPage
  const paged = filtered.slice(start, start + perPage)
  
  return {
    products: paged,
    total: filtered.length,
    page,
    per_page: perPage,
    facets: {
      marketplaces: {
        ozon: filtered.filter(p => p.marketplace_id === 1).length,
        wildberries: filtered.filter(p => p.marketplace_id === 2).length,
        yandex_market: filtered.filter(p => p.marketplace_id === 3).length,
        aliexpress: filtered.filter(p => p.marketplace_id === 4).length,
      },
      price: {
        min_price: Math.min(...filtered.map(p => p.current_price)),
        max_price: Math.max(...filtered.map(p => p.current_price)),
        avg_price: filtered.reduce((sum, p) => sum + p.current_price, 0) / filtered.length,
      }
    }
  }
}

// Get product by ID
export async function getProduct(id: number) {
  await delay(200 + Math.random() * 300)
  const product = MOCK_PRODUCTS.find(p => p.id === id)
  if (!product) throw new Error('Product not found')
  return product
}

// Get search suggestions
export async function getSearchSuggestions(query: string) {
  await delay(100 + Math.random() * 200)
  
  if (query.length < 2) return { suggestions: [] }
  
  const suggestions = [
    'iPhone 15 Pro',
    'iPhone 15',
    'Samsung Galaxy S24',
    'AirPods Pro',
    'MacBook Air',
    'PlayStation 5',
    'Робот-пылесос',
    'Телевизор Samsung',
    'Apple Watch',
    'Dyson',
  ].filter(s => s.toLowerCase().includes(query.toLowerCase())).slice(0, 5)
  
  return { suggestions }
}

// Health check
export async function getHealth() {
  return { status: 'healthy' }
}

// Export all products for other pages
export function getAllProducts() {
  return MOCK_PRODUCTS
}

export { MOCK_PRODUCTS }
