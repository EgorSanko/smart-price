/**
 * Search hooks with proper error handling
 */

'use client'

import { useQuery } from '@tanstack/react-query'
import { searchProducts, getSearchSuggestions } from '@/lib/api'
import type { SearchParams } from '@/types'

export function useSearch(params: SearchParams | null) {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => searchProducts(params!),
    enabled: !!params?.q,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  })
}

export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: ['suggestions', query],
    queryFn: () => getSearchSuggestions(query),
    enabled: query.length >= 2,
    staleTime: 1000 * 60 * 10,
  })
}
