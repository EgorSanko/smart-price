/**
 * SearchBar component (простой вариант)
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search } from 'lucide-react'

interface SearchBarProps {
  initialQuery?: string
  placeholder?: string
  autoFocus?: boolean
}

export function SearchBar({
  initialQuery = '',
  placeholder = 'Искать товары...',
  autoFocus = false,
}: SearchBarProps) {
  const router = useRouter()
  const [query, setQuery] = useState(initialQuery)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`)
    }
  }

  return (
    <form onSubmit={handleSearch} className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className="input pr-14"
      />
      <button
        type="submit"
        className="absolute right-2 top-2 bottom-2 px-4 bg-accent-500 text-white rounded-lg hover:bg-accent-600 transition-colors"
      >
        <Search className="w-5 h-5" />
      </button>
    </form>
  )
}
