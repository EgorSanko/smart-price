/**
 * Header - фиолетово-графитовая тема
 */

'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState } from 'react'
import { 
  Search, 
  Menu, 
  X, 
  Heart, 
  User, 
  BarChart2, 
  Smartphone,
  Laptop,
  Headphones,
  Tv,
  Home,
  Gamepad2,
  ChevronRight,
  MessageSquare
} from 'lucide-react'
import { cn } from '@/lib/utils'

const categories = [
  { name: 'Смартфоны и гаджеты', slug: 'smartphones', icon: Smartphone },
  { name: 'Компьютеры и ноутбуки', slug: 'laptops', icon: Laptop },
  { name: 'Телевизоры Аудио Hi-Fi', slug: 'tvs', icon: Tv },
  { name: 'Наушники', slug: 'headphones', icon: Headphones },
  { name: 'Для дома', slug: 'home', icon: Home },
  { name: 'Игры и консоли', slug: 'gaming', icon: Gamepad2 },
]

export function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const [showCatalog, setShowCatalog] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  return (
    <header className="sticky top-0 z-50 bg-graphite-900 border-b border-graphite-600">
      <div className="container">
        <div className="flex items-center gap-4 h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 flex-shrink-0">
            <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center shadow-glow">
              <span className="text-white font-bold text-xl">S</span>
            </div>
            <span className="text-xl font-bold text-txt-primary hidden sm:block tracking-tight">
              SMART<span className="text-accent-light">PRICE</span>
            </span>
          </Link>

          {/* Catalog button */}
          <div className="relative">
            <button
              onClick={() => setShowCatalog(!showCatalog)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold bg-accent text-white hover:bg-accent-light transition-colors"
            >
              {showCatalog ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              <span className="hidden sm:inline">Каталог</span>
            </button>

            {/* Catalog dropdown */}
            {showCatalog && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowCatalog(false)} />
                <div className="absolute top-full left-0 mt-2 w-72 bg-graphite-800 rounded-2xl border border-graphite-600 shadow-card py-2 z-50">
                  {categories.map((cat) => {
                    const Icon = cat.icon
                    return (
                      <Link
                        key={cat.slug}
                        href={`/search?category=${cat.slug}`}
                        onClick={() => setShowCatalog(false)}
                        className="flex items-center gap-3 px-4 py-3 text-txt-secondary hover:bg-graphite-700 hover:text-txt-primary transition-colors group"
                      >
                        <Icon className="w-5 h-5 text-txt-muted group-hover:text-accent-light" />
                        <span className="font-medium flex-1">{cat.name}</span>
                        <ChevronRight className="w-4 h-4 text-txt-muted group-hover:text-accent-light" />
                      </Link>
                    )
                  })}
                </div>
              </>
            )}
          </div>

          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 max-w-2xl hidden md:block">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Искать товары"
                className="w-full h-11 pl-4 pr-14 rounded-xl bg-graphite-800 border border-graphite-600 text-txt-primary placeholder:text-txt-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all"
              />
              <button
                type="submit"
                className="absolute right-1 top-1 bottom-1 px-4 bg-accent text-white rounded-lg hover:bg-accent-light transition-colors"
              >
                <Search className="w-5 h-5" />
              </button>
            </div>
          </form>

          {/* Nav links */}
          <nav className="hidden lg:flex items-center gap-1">
            <Link
              href="/compare"
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
                pathname === '/compare' ? 'text-accent-light' : 'text-txt-secondary hover:text-txt-primary'
              )}
            >
              <BarChart2 className="w-5 h-5" />
              <span>Сравнение</span>
            </Link>
            <Link
              href="/chat"
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
                pathname === '/chat' ? 'text-accent-light' : 'text-txt-secondary hover:text-txt-primary'
              )}
            >
              <MessageSquare className="w-5 h-5" />
              <span>AI</span>
            </Link>
          </nav>

          {/* User actions */}
          <div className="flex items-center gap-1">
            <button className="p-2.5 rounded-lg text-txt-secondary hover:text-txt-primary hover:bg-graphite-800 transition-colors">
              <Heart className="w-5 h-5" />
            </button>
            <button className="p-2.5 rounded-lg text-txt-secondary hover:text-txt-primary hover:bg-graphite-800 transition-colors">
              <User className="w-5 h-5" />
            </button>

            {/* Mobile menu */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2.5 rounded-lg text-txt-secondary hover:text-txt-primary hover:bg-graphite-800"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile search */}
        <form onSubmit={handleSearch} className="md:hidden pb-3">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Искать товары"
              className="w-full h-11 pl-4 pr-14 rounded-xl bg-graphite-800 border border-graphite-600 text-txt-primary placeholder:text-txt-muted focus:outline-none focus:ring-2 focus:ring-accent"
            />
            <button
              type="submit"
              className="absolute right-1 top-1 bottom-1 px-4 bg-accent text-white rounded-lg"
            >
              <Search className="w-5 h-5" />
            </button>
          </div>
        </form>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-graphite-800 border-t border-graphite-600">
          <div className="container py-4 space-y-2">
            {categories.map((cat) => {
              const Icon = cat.icon
              return (
                <Link
                  key={cat.slug}
                  href={`/search?category=${cat.slug}`}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-txt-secondary hover:bg-graphite-700 hover:text-txt-primary"
                >
                  <Icon className="w-5 h-5 text-txt-muted" />
                  <span className="font-medium">{cat.name}</span>
                </Link>
              )
            })}
            <div className="border-t border-graphite-600 pt-4 mt-4">
              <Link
                href="/compare"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-txt-secondary hover:bg-graphite-700"
              >
                <BarChart2 className="w-5 h-5 text-txt-muted" />
                <span>Сравнение</span>
              </Link>
              <Link
                href="/chat"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-txt-secondary hover:bg-graphite-700"
              >
                <MessageSquare className="w-5 h-5 text-txt-muted" />
                <span>AI Помощник</span>
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
