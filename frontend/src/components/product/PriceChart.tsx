/**
 * PriceChart component for displaying price history
 */

'use client'

import { useMemo, useState } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { format, subDays, isAfter } from 'date-fns'
import { ru } from 'date-fns/locale'
import { TrendingDown, TrendingUp, Minus, Calendar } from 'lucide-react'
import { cn, formatPrice, getTrendInfo } from '@/lib/utils'
import type { PricePoint, PriceStats } from '@/types'

interface PriceChartProps {
  priceHistory: PricePoint[]
  priceStats: PriceStats
  currentPrice: number
  currency?: string
  className?: string
}

const TIME_RANGES = [
  { label: '7 дней', days: 7 },
  { label: '30 дней', days: 30 },
  { label: '90 дней', days: 90 },
  { label: 'Всё время', days: 365 },
]

export function PriceChart({
  priceHistory,
  priceStats,
  currentPrice,
  currency = 'RUB',
  className,
}: PriceChartProps) {
  const [selectedRange, setSelectedRange] = useState(30)

  // Filter data by selected range
  const filteredData = useMemo(() => {
    const cutoffDate = subDays(new Date(), selectedRange)
    return priceHistory
      .filter((point) => isAfter(new Date(point.recorded_at), cutoffDate))
      .map((point) => ({
        date: new Date(point.recorded_at).getTime(),
        price: point.price,
        originalPrice: point.original_price,
      }))
      .sort((a, b) => a.date - b.date)
  }, [priceHistory, selectedRange])

  // Calculate min/max for Y axis
  const { minY, maxY } = useMemo(() => {
    if (filteredData.length === 0) return { minY: 0, maxY: 100 }
    const prices = filteredData.map((d) => d.price)
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    const padding = (max - min) * 0.1
    return {
      minY: Math.floor(min - padding),
      maxY: Math.ceil(max + padding),
    }
  }, [filteredData])

  const trendInfo = getTrendInfo(priceStats.trend)

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.[0]) return null
    const data = payload[0].payload
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="text-sm text-gray-500">
          {format(new Date(data.date), 'd MMMM yyyy', { locale: ru })}
        </p>
        <p className="text-lg font-bold text-gray-900">
          {formatPrice(data.price, currency)}
        </p>
        {data.originalPrice && data.originalPrice > data.price && (
          <p className="text-sm text-gray-400 line-through">
            {formatPrice(data.originalPrice, currency)}
          </p>
        )}
      </div>
    )
  }

  return (
    <div className={cn('bg-white rounded-xl border border-gray-200 p-6', className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">История цен</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={cn('font-medium', trendInfo.color)}>
              {trendInfo.icon} {trendInfo.text}
            </span>
            <span className="text-gray-400">•</span>
            <span className="text-sm text-gray-600">
              {priceStats.current_vs_min_percent > 0
                ? `+${priceStats.current_vs_min_percent.toFixed(0)}% от минимума`
                : 'Минимальная цена'}
            </span>
          </div>
        </div>

        {/* Time range selector */}
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
          {TIME_RANGES.map((range) => (
            <button
              key={range.days}
              onClick={() => setSelectedRange(range.days)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                selectedRange === range.days
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <p className="text-xs text-green-600 mb-1">Минимум</p>
          <p className="text-lg font-bold text-green-700">
            {formatPrice(priceStats.min_price, currency)}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-1">Средняя</p>
          <p className="text-lg font-bold text-gray-700">
            {formatPrice(priceStats.avg_price, currency)}
          </p>
        </div>
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <p className="text-xs text-red-600 mb-1">Максимум</p>
          <p className="text-lg font-bold text-red-700">
            {formatPrice(priceStats.max_price, currency)}
          </p>
        </div>
      </div>

      {/* Chart */}
      {filteredData.length > 0 ? (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={filteredData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) =>
                  format(new Date(value), 'd MMM', { locale: ru })
                }
                stroke="#9ca3af"
                fontSize={12}
              />
              <YAxis
                domain={[minY, maxY]}
                tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                stroke="#9ca3af"
                fontSize={12}
                width={50}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine
                y={currentPrice}
                stroke="#10b981"
                strokeDasharray="5 5"
                label={{
                  value: 'Сейчас',
                  position: 'right',
                  fill: '#10b981',
                  fontSize: 12,
                }}
              />
              <ReferenceLine
                y={priceStats.min_price}
                stroke="#22c55e"
                strokeDasharray="3 3"
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#colorPrice)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-64 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <Calendar className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p>Нет данных за выбранный период</p>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * PriceChartSkeleton for loading state
 */
export function PriceChartSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
      <div className="flex justify-between mb-6">
        <div>
          <div className="h-6 w-32 bg-gray-200 rounded mb-2" />
          <div className="h-4 w-48 bg-gray-200 rounded" />
        </div>
        <div className="h-10 w-64 bg-gray-200 rounded-lg" />
      </div>
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-lg" />
        ))}
      </div>
      <div className="h-64 bg-gray-100 rounded-lg" />
    </div>
  )
}
