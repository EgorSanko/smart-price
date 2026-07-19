/**
 * Animated SVG illustrations for Smart Price — all inline, zero deps.
 * Keyframes live in globals.css.
 */

export function SadPanda({ className = '' }: { className?: string }) {
  return (
    <div className={`relative mx-auto w-40 h-40 select-none ${className}`} aria-hidden>
      <svg viewBox="0 0 200 200" className="w-full h-full animate-panda-sway">
        <ellipse cx="55" cy="55" rx="22" ry="24" fill="#1a1a1a" />
        <ellipse cx="145" cy="55" rx="22" ry="24" fill="#1a1a1a" />
        <ellipse cx="55" cy="58" rx="11" ry="12" fill="#3a3a3a" />
        <ellipse cx="145" cy="58" rx="11" ry="12" fill="#3a3a3a" />
        <ellipse cx="100" cy="110" rx="68" ry="62" fill="#f7f4ef" />
        <ellipse cx="72" cy="105" rx="18" ry="24" fill="#1a1a1a" transform="rotate(-18 72 105)" />
        <ellipse cx="128" cy="105" rx="18" ry="24" fill="#1a1a1a" transform="rotate(18 128 105)" />
        <circle cx="72" cy="110" r="5" fill="#fff" />
        <circle cx="128" cy="110" r="5" fill="#fff" />
        <circle cx="72" cy="111" r="2.5" fill="#1a1a1a" />
        <circle cx="128" cy="111" r="2.5" fill="#1a1a1a" />
        <ellipse cx="100" cy="135" rx="6" ry="4" fill="#1a1a1a" />
        <path d="M 82 158 Q 100 146 118 158" stroke="#1a1a1a" strokeWidth="3.5" fill="none" strokeLinecap="round" />
        <ellipse cx="62" cy="130" rx="3.5" ry="5" fill="#5bb9ff" className="animate-panda-tear" style={{ transformOrigin: '62px 130px' }} />
      </svg>
    </div>
  )
}

export function PiggyBank({ className = '' }: { className?: string }) {
  return (
    <div className={`relative mx-auto w-40 h-40 select-none ${className}`} aria-hidden>
      <svg viewBox="0 0 200 200" className="w-full h-full">
        {/* falling coins */}
        <g>
          <ellipse cx="90" cy="20" rx="8" ry="3" fill="#f5c342" className="animate-coin-drop-1" />
          <ellipse cx="120" cy="10" rx="8" ry="3" fill="#f5c342" className="animate-coin-drop-2" />
          <ellipse cx="105" cy="5" rx="8" ry="3" fill="#f5c342" className="animate-coin-drop-3" />
        </g>
        {/* piggy body */}
        <g className="animate-piggy-wiggle" style={{ transformOrigin: '100px 130px' }}>
          <ellipse cx="100" cy="130" rx="68" ry="48" fill="#ff8fb4" />
          {/* legs */}
          <rect x="62" y="162" width="14" height="18" rx="4" fill="#ff8fb4" />
          <rect x="124" y="162" width="14" height="18" rx="4" fill="#ff8fb4" />
          {/* ear */}
          <path d="M 55 95 L 52 75 L 72 95 Z" fill="#ff7aa4" />
          {/* coin slot */}
          <rect x="92" y="90" width="16" height="4" rx="2" fill="#c15580" />
          {/* snout */}
          <ellipse cx="46" cy="130" rx="14" ry="12" fill="#ff7aa4" />
          <circle cx="42" cy="128" r="2" fill="#8a3558" />
          <circle cx="50" cy="128" r="2" fill="#8a3558" />
          {/* eye */}
          <circle cx="75" cy="118" r="3" fill="#2a1420" />
          <circle cx="76" cy="117" r="1" fill="#fff" />
          {/* tail */}
          <path d="M 165 120 Q 178 118 175 130 Q 172 138 168 132" stroke="#ff7aa4" strokeWidth="4" fill="none" strokeLinecap="round" />
        </g>
      </svg>
    </div>
  )
}

export function RollingCart({ className = '' }: { className?: string }) {
  return (
    <div className={`relative mx-auto w-40 h-24 select-none ${className}`} aria-hidden>
      <svg viewBox="0 0 200 120" className="w-full h-full">
        {/* ground */}
        <line x1="10" y1="105" x2="190" y2="105" stroke="currentColor" strokeOpacity="0.15" strokeWidth="2" strokeDasharray="4 6" />
        <g className="animate-cart-roll" style={{ transformOrigin: 'center' }}>
          {/* basket */}
          <path d="M 50 40 L 150 40 L 140 85 L 65 85 Z" fill="none" stroke="#5aa7ff" strokeWidth="3" strokeLinejoin="round" />
          {/* basket bars */}
          <line x1="75" y1="40" x2="80" y2="85" stroke="#5aa7ff" strokeWidth="2" />
          <line x1="100" y1="40" x2="100" y2="85" stroke="#5aa7ff" strokeWidth="2" />
          <line x1="125" y1="40" x2="120" y2="85" stroke="#5aa7ff" strokeWidth="2" />
          <line x1="55" y1="60" x2="145" y2="60" stroke="#5aa7ff" strokeWidth="2" />
          {/* handle */}
          <path d="M 50 40 L 38 25 L 28 25" fill="none" stroke="#5aa7ff" strokeWidth="3" strokeLinecap="round" />
          {/* coins inside */}
          <circle cx="85" cy="55" r="5" fill="#f5c342" />
          <circle cx="110" cy="55" r="5" fill="#f5c342" />
          {/* wheels */}
          <circle cx="75" cy="98" r="8" fill="#2a3340" className="animate-wheel-spin" style={{ transformOrigin: '75px 98px' }} />
          <circle cx="75" cy="98" r="2" fill="#5aa7ff" />
          <circle cx="130" cy="98" r="8" fill="#2a3340" className="animate-wheel-spin" style={{ transformOrigin: '130px 98px' }} />
          <circle cx="130" cy="98" r="2" fill="#5aa7ff" />
        </g>
      </svg>
    </div>
  )
}

export function HappyCoin({ className = '' }: { className?: string }) {
  return (
    <div className={`relative w-20 h-20 select-none ${className}`} aria-hidden>
      <svg viewBox="0 0 100 100" className="w-full h-full">
        {/* sparkles */}
        <g className="animate-sparkle" style={{ transformOrigin: 'center' }}>
          <path d="M 15 20 L 18 27 L 25 30 L 18 33 L 15 40 L 12 33 L 5 30 L 12 27 Z" fill="#f5c342" opacity="0.8" />
          <path d="M 82 70 L 84 75 L 89 77 L 84 79 L 82 84 L 80 79 L 75 77 L 80 75 Z" fill="#5aa7ff" opacity="0.8" />
        </g>
        <g className="animate-coin-bob" style={{ transformOrigin: '50px 55px' }}>
          {/* coin */}
          <circle cx="50" cy="55" r="30" fill="#f5c342" stroke="#d99f1f" strokeWidth="2" />
          <circle cx="50" cy="55" r="24" fill="none" stroke="#d99f1f" strokeWidth="1.5" strokeDasharray="2 2" />
          {/* eyes */}
          <circle cx="42" cy="50" r="2.5" fill="#2a1420" />
          <circle cx="58" cy="50" r="2.5" fill="#2a1420" />
          {/* smile */}
          <path d="M 40 62 Q 50 70 60 62" stroke="#2a1420" strokeWidth="2.5" fill="none" strokeLinecap="round" />
        </g>
      </svg>
    </div>
  )
}

export function CheckCoin({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={`w-5 h-5 ${className}`} aria-hidden>
      <circle cx="12" cy="12" r="10" fill="#22c55e" />
      <path d="M 7 12 L 11 16 L 17 9" stroke="#fff" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function CrossedTag({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={`w-5 h-5 ${className}`} aria-hidden>
      <path d="M 3 12 L 12 3 L 21 3 L 21 12 L 12 21 Z" fill="#f59e0b" opacity="0.2" />
      <path d="M 3 12 L 12 3 L 21 3 L 21 12 L 12 21 Z" stroke="#f59e0b" strokeWidth="1.8" fill="none" strokeLinejoin="round" />
      <circle cx="16" cy="8" r="1.5" fill="#f59e0b" />
      <line x1="5" y1="5" x2="19" y2="19" stroke="#ef4444" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}

export function PriceTagHero({ className = '' }: { className?: string }) {
  return (
    <div className={`relative w-full max-w-[280px] aspect-square mx-auto select-none ${className}`} aria-hidden>
      <svg viewBox="0 0 240 240" className="w-full h-full">
        {/* glow */}
        <circle cx="120" cy="120" r="95" fill="var(--ac)" opacity="0.08" className="animate-pulse-slow" />
        {/* arrow down */}
        <g className="animate-arrow-drop" style={{ transformOrigin: '180px 80px' }}>
          <line x1="180" y1="50" x2="180" y2="100" stroke="#22c55e" strokeWidth="5" strokeLinecap="round" />
          <path d="M 170 92 L 180 105 L 190 92" stroke="#22c55e" strokeWidth="5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </g>
        {/* price tag */}
        <g className="animate-tag-sway" style={{ transformOrigin: '120px 140px' }}>
          <path d="M 55 85 L 130 85 L 175 130 L 120 185 L 65 130 Z" fill="var(--ac)" opacity="0.18" stroke="var(--ac)" strokeWidth="2.5" strokeLinejoin="round" />
          <circle cx="82" cy="112" r="8" fill="var(--ac)" />
          <circle cx="82" cy="112" r="3" fill="#fff" />
          <text x="115" y="148" fontSize="28" fontWeight="800" fill="currentColor" textAnchor="middle">₽</text>
        </g>
        {/* bouncing coin */}
        <g className="animate-coin-bob2" style={{ transformOrigin: '50px 180px' }}>
          <circle cx="50" cy="180" r="18" fill="#f5c342" stroke="#d99f1f" strokeWidth="2" />
          <text x="50" y="187" fontSize="16" fontWeight="800" fill="#8a5a0b" textAnchor="middle">₽</text>
        </g>
      </svg>
    </div>
  )
}

export function EmptyCart({ className = '' }: { className?: string }) {
  return (
    <div className={`relative mx-auto w-40 h-28 select-none ${className}`} aria-hidden>
      <svg viewBox="0 0 200 140" className="w-full h-full">
        <line x1="10" y1="115" x2="190" y2="115" stroke="currentColor" strokeOpacity="0.15" strokeWidth="2" strokeDasharray="4 6" />
        {/* tumbleweed */}
        <g className="animate-tumble" style={{ transformOrigin: 'center' }}>
          <g>
            <circle cx="30" cy="100" r="12" fill="none" stroke="#b38b5e" strokeWidth="1.5" opacity="0.7" />
            <path d="M 22 92 L 38 108 M 38 92 L 22 108 M 20 100 L 40 100 M 30 88 L 30 112" stroke="#b38b5e" strokeWidth="1.2" opacity="0.6" />
          </g>
        </g>
        {/* empty cart */}
        <g>
          <path d="M 90 55 L 170 55 L 162 100 L 100 100 Z" fill="none" stroke="currentColor" strokeOpacity="0.4" strokeWidth="2.5" strokeLinejoin="round" />
          <path d="M 90 55 L 80 40 L 70 40" fill="none" stroke="currentColor" strokeOpacity="0.4" strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="110" cy="112" r="6" fill="none" stroke="currentColor" strokeOpacity="0.4" strokeWidth="2" />
          <circle cx="155" cy="112" r="6" fill="none" stroke="currentColor" strokeOpacity="0.4" strokeWidth="2" />
        </g>
      </svg>
    </div>
  )
}
