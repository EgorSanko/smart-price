/**
 * Products hooks
 */

'use client'

import { useQuery } from '@tanstack/react-query'
import {
  getProducts,
  getProduct,
  getSimilarProducts,
  compareProductPrices,
  getPriceForecast,
} from '@/lib/api'

export function useProducts(params?: {
  page?: number
  per_page?: number
  marketplace_id?: number
}) {
  return useQuery({
    queryKey: ['products', params],
    queryFn: () => getProducts(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useProduct(id: number) {
  return useQuery({
    queryKey: ['product', id],
    queryFn: () => getProduct(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  })
}

export function useSimilarProducts(productId: number, limit?: number) {
  return useQuery({
    queryKey: ['similar', productId, limit],
    queryFn: () => getSimilarProducts(productId, limit),
    enabled: !!productId,
    staleTime: 1000 * 60 * 10,
  })
}

export function useProductComparison(productId: number) {
  return useQuery({
    queryKey: ['comparison', productId],
    queryFn: () => compareProductPrices(productId),
    enabled: !!productId,
    staleTime: 1000 * 60 * 5,
  })
}

export function usePriceForecast(productId: number, days?: number) {
  return useQuery({
    queryKey: ['forecast', productId, days],
    queryFn: () => getPriceForecast(productId, days),
    enabled: !!productId,
    staleTime: 1000 * 60 * 30, // 30 minutes
  })
}
