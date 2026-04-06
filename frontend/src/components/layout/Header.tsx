'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Search, Scale, MessageCircle, Info, Menu, X, LayoutGrid, CreditCard, LogIn, User, LogOut, Crown, Sparkles } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth'

const navItems = [
  { href: '/', label: 'Поиск', icon: Search },
  { href: '/catalog', label: 'Каталог', icon: LayoutGrid },
  { href: '/compare', label: 'Сравнение', icon: Scale },
  { href: '/analyze', label: 'Анализ цены', icon: Sparkles },
  { href: '/chat', label: 'AI Помощник', icon: MessageCircle },
]

export function Header() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { user, token, logout, fetchMe } = useAuth()

  useEffect(() => {
    if (token && !user) fetchMe()
  }, [token, user, fetchMe])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--bd)]" style={{ background: 'rgba(10,10,15,.85)', backdropFilter: 'blur(24px)' }}>
      <div className="container h-14 flex items-center">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 mr-8">
          <div className="w-8 h-8 rounded-lg bg-[var(--ac)] flex items-center justify-center">
            <span className="text-white font-black text-sm">SP</span>
          </div>
          <span className="font-extrabold text-base tracking-tight">
            <span className="gradient-text">Smart</span>
            <span className="text-[var(--td)]">Price</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-[13px] font-medium transition-all ${
                  isActive
                    ? 'bg-[var(--ac-glow)] text-[var(--ac2)]'
                    : 'text-[var(--td)] hover:text-[var(--t)] hover:bg-[var(--c2)]'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* Right side */}
        <div className="hidden md:flex items-center gap-2 ml-auto">
          <Link
            href="/about"
            className={`p-2 rounded-lg text-[var(--td)] hover:text-[var(--t)] hover:bg-[var(--c2)] transition-all ${
              pathname === '/about' ? 'text-[var(--ac2)]' : ''
            }`}
          >
            <Info className="w-4 h-4" />
          </Link>

          {user ? (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-[var(--c2)] transition-all"
              >
                <div className="w-7 h-7 rounded-full bg-[var(--ac)]/20 flex items-center justify-center">
                  <User className="w-4 h-4 text-[var(--ac)]" />
                </div>
                <span className="text-sm font-medium text-[var(--t)] max-w-[100px] truncate">
                  {user.full_name || user.email.split('@')[0]}
                </span>
                {user.has_active_subscription && (
                  <Crown className="w-3.5 h-3.5 text-[var(--ac)]" />
                )}
              </button>

              {dropdownOpen && (
                <div className="absolute right-0 top-full mt-2 w-56 bg-[var(--c1)] border border-[var(--bd)] rounded-xl shadow-xl overflow-hidden z-50">
                  <div className="px-4 py-3 border-b border-[var(--bd)]">
                    <p className="text-sm font-medium text-[var(--t)]">{user.email}</p>
                    <p className="text-xs text-[var(--td)] mt-0.5">
                      План: {user.subscription_plan === 'free' ? 'Бесплатный' : user.subscription_plan === 'pro' ? 'Pro' : 'Business'}
                    </p>
                  </div>
                  <Link href="/dashboard" onClick={() => setDropdownOpen(false)} className="flex items-center gap-2 px-4 py-2.5 text-sm text-[var(--td)] hover:bg-[var(--c2)] hover:text-[var(--t)]">
                    <User className="w-4 h-4" /> Личный кабинет
                  </Link>
                  <Link href="/pricing" onClick={() => setDropdownOpen(false)} className="flex items-center gap-2 px-4 py-2.5 text-sm text-[var(--td)] hover:bg-[var(--c2)] hover:text-[var(--t)]">
                    <CreditCard className="w-4 h-4" /> Тарифы
                  </Link>
                  <button
                    onClick={() => { logout(); setDropdownOpen(false) }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10"
                  >
                    <LogOut className="w-4 h-4" /> Выйти
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-[13px] font-medium transition-all ${
                pathname === '/login'
                  ? 'bg-[var(--ac)] text-white'
                  : 'bg-[var(--c2)] text-[var(--td)] hover:text-[var(--t)] hover:bg-[var(--c3)]'
              }`}
            >
              <LogIn className="w-4 h-4" /> Войти
            </Link>
          )}
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden ml-auto p-2 text-[var(--td)]"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-[var(--bd)] bg-[var(--bg2)] animate-fadeIn">
          <div className="container py-3 flex flex-col gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-[var(--ac-glow)] text-[var(--ac2)]'
                      : 'text-[var(--td)] hover:bg-[var(--c2)]'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              )
            })}
            <div className="border-t border-[var(--bd)] mt-1 pt-1">
              {user ? (
                <>
                  <Link href="/dashboard" onClick={() => setMobileOpen(false)} className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-[var(--td)] hover:bg-[var(--c2)]">
                    <User className="w-5 h-5" /> Личный кабинет
                  </Link>
                  <button onClick={() => { logout(); setMobileOpen(false) }} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/10">
                    <LogOut className="w-5 h-5" /> Выйти
                  </button>
                </>
              ) : (
                <Link href="/login" onClick={() => setMobileOpen(false)} className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-[var(--ac2)] hover:bg-[var(--c2)]">
                  <LogIn className="w-5 h-5" /> Войти
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
