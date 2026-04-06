'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Search, Sparkles, ShoppingBag, Smartphone, Laptop, Tv, Headphones } from 'lucide-react'

export default function NotFound() {
  const [tilt, setTilt] = useState({ x: 0, y: 0 })
  const [lostCount, setLostCount] = useState<number | null>(null)

  // Easter egg: counter of "lost souls" who hit 404
  useEffect(() => {
    try {
      const KEY = 'sp_404_lost_count'
      const cur = parseInt(localStorage.getItem(KEY) || '0', 10)
      const next = (isNaN(cur) ? 0 : cur) + 1
      localStorage.setItem(KEY, String(next))
      setLostCount(next)
    } catch {
      // localStorage may be unavailable (private mode, SSR)
    }
  }, [])

  // Mouse parallax — only on devices with hover (skip touch/mobile)
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!window.matchMedia('(hover: hover)').matches) return

    function handleMove(e: MouseEvent) {
      const x = (e.clientX / window.innerWidth - 0.5) * 24 // -12 to 12 deg
      const y = (e.clientY / window.innerHeight - 0.5) * -16
      setTilt({ x, y })
    }

    window.addEventListener('mousemove', handleMove)
    return () => window.removeEventListener('mousemove', handleMove)
  }, [])

  return (
    <div className="nf-root">
      {/* Aurora gradient background blobs */}
      <div className="nf-aurora nf-aurora-1" aria-hidden="true" />
      <div className="nf-aurora nf-aurora-2" aria-hidden="true" />
      <div className="nf-aurora nf-aurora-3" aria-hidden="true" />

      <div className="nf-container">
        {/* 3D scene with orbits and 404 */}
        <div
          className="nf-scene"
          style={{
            transform: `perspective(1200px) rotateX(${tilt.y}deg) rotateY(${tilt.x}deg)`,
          }}
        >
          {/* Static orbit rings */}
          <div className="nf-ring nf-ring-1" aria-hidden="true" />
          <div className="nf-ring nf-ring-2" aria-hidden="true" />
          <div className="nf-ring nf-ring-3" aria-hidden="true" />

          {/* Orbiting product icons */}
          <div className="nf-orbit-icon nf-icon-1" aria-hidden="true">
            <ShoppingBag size={22} />
          </div>
          <div className="nf-orbit-icon nf-icon-2" aria-hidden="true">
            <Smartphone size={22} />
          </div>
          <div className="nf-orbit-icon nf-icon-3" aria-hidden="true">
            <Laptop size={22} />
          </div>
          <div className="nf-orbit-icon nf-icon-4" aria-hidden="true">
            <Headphones size={20} />
          </div>
          <div className="nf-orbit-icon nf-icon-5" aria-hidden="true">
            <Tv size={22} />
          </div>

          {/* The big 404 */}
          <div className="nf-404">
            <span className="nf-404-text">404</span>
            <div className="nf-scanline" aria-hidden="true" />
          </div>
        </div>

        {/* Title and message */}
        <h1 className="nf-title">Товар не найден на наших полках</h1>
        <p className="nf-subtitle">
          Возможно, он распродан, переехал в другую категорию
          <br />
          или ещё не поступил в продажу. Попробуй поиск или вернись на главную.
        </p>

        {/* Call to action buttons */}
        <div className="nf-actions">
          <Link href="/" className="nf-btn nf-btn-primary">
            <Search size={18} />
            <span>Найти товар</span>
          </Link>
          <Link href="/chat" className="nf-btn nf-btn-secondary">
            <Sparkles size={18} />
            <span>Спросить AI Помощника</span>
          </Link>
        </div>

        {/* Easter egg: lost souls counter */}
        {lostCount !== null && lostCount > 0 && (
          <div className="nf-counter">
            Ты <span className="nf-counter-num">#{lostCount.toLocaleString('ru-RU')}</span> в клубе заблудившихся
          </div>
        )}
      </div>
    </div>
  )
}
