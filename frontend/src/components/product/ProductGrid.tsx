/**
 * ProductGrid component for displaying products in a responsive grid
 */

import { ProductCard, ProductCardSkeleton } from './ProductCard'
import type { Product } from '@/types'

interface ProductGridProps {
  products: Product[]
  showMarketplace?: boolean
  className?: string
}

export function ProductGrid({
  products,
  showMarketplace = true,
  className,
}: ProductGridProps) {
  if (!products || products.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Товары не найдены</p>
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            showMarketplace={showMarketplace}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * ProductGridSkeleton for loading state
 */
export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  )
}

