/**
 * Utility functions
 */

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind CSS classes with clsx
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format price with currency
 */
export function formatPrice(
  price: number | undefined | null,
  currency: string = 'RUB',
  locale: string = 'ru-RU'
): string {
  if (price == null || isNaN(price)) return '—'
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price)
}

/**
 * Format number with spaces
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('ru-RU').format(num)
}

/**
 * Calculate discount percentage
 */
export function calculateDiscount(
  currentPrice: number,
  originalPrice: number | null
): number | null {
  if (!originalPrice || originalPrice <= currentPrice) return null
  return Math.round(((originalPrice - currentPrice) / originalPrice) * 100)
}

/**
 * Format date relative to now
 */
export function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Сегодня'
  if (diffDays === 1) return 'Вчера'
  if (diffDays < 7) return `${diffDays} дн. назад`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} нед. назад`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} мес. назад`
  return `${Math.floor(diffDays / 365)} г. назад`
}

/**
 * Format date for display
 */
export function formatDate(
  dateString: string,
  options?: Intl.DateTimeFormatOptions
): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    ...options,
  })
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

/**
 * Get trend icon and color
 */
export function getTrendInfo(trend: 'rising' | 'falling' | 'stable'): {
  icon: string
  color: string
  text: string
} {
  switch (trend) {
    case 'rising':
      return { icon: '↑', color: 'text-red-500', text: 'Растёт' }
    case 'falling':
      return { icon: '↓', color: 'text-green-500', text: 'Падает' }
    case 'stable':
      return { icon: '→', color: 'text-gray-500', text: 'Стабильно' }
  }
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null
  
  return (...args: Parameters<T>) => {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

/**
 * Generate placeholder image URL
 */
export function getPlaceholderImage(width: number, height: number): string {
  return `https://placehold.co/${width}x${height}/e5e7eb/9ca3af?text=Нет+фото`
}
