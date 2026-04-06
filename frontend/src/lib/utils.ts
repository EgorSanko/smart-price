export function cn(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(' ')
}

export function formatPrice(price: number, currency = 'RUB') {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: currency === 'BYN' ? 'BYN' : 'RUB',
    maximumFractionDigits: 0,
  }).format(price)
}

export function formatNumber(num: number) {
  return new Intl.NumberFormat('ru-RU').format(num)
}

export function calculateDiscount(current: number, original?: number) {
  if (!original || original <= current) return null
  return Math.round((1 - current / original) * 100)
}
