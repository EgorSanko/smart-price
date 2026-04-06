'use client'

// Next.js route-level Suspense fallback. This shows INSTANTLY on navigation
// from search → product (before the page component mounts), so the user
// never sees a frozen card click. The full-screen loader inside page.tsx
// handles the subsequent data-fetch delay.
export default function ProductLoading() {
  return (
    <div className="pl-root">
      <div className="pl-glow pl-glow-1" aria-hidden="true" />
      <div className="pl-glow pl-glow-2" aria-hidden="true" />
      <div className="pl-content">
        <div className="pl-orb">
          <div className="pl-orbit" />
          <div className="pl-orbit pl-orbit-2" />
          <div className="pl-orbit pl-orbit-3" />
          <div className="pl-core">SP</div>
        </div>
        <div className="pl-title">Smart Price</div>
        <div className="pl-bar-track">
          <div className="pl-bar-glow" />
        </div>
        <div className="pl-dots">
          <span className="pl-dot" />
          <span className="pl-dot" />
          <span className="pl-dot" />
        </div>
        <p className="pl-sub">Открываем карточку товара</p>
      </div>

      <style jsx>{`
        .pl-root {
          position: fixed; inset: 0; z-index: 100;
          display: flex; align-items: center; justify-content: center;
          background: var(--sp-bg, #0a0a0f);
          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
        }
        .pl-glow {
          position: absolute; top: 30%; left: 50%;
          width: 500px; height: 500px;
          transform: translate(-50%, -50%);
          border-radius: 50%;
          background: radial-gradient(circle, rgba(108,92,231,.15), transparent 70%);
          filter: blur(60px);
          animation: plGlowPulse 3s ease-in-out infinite;
        }
        .pl-glow-2 {
          top: 60%; width: 400px; height: 400px;
          background: radial-gradient(circle, rgba(0,210,106,.1), transparent 70%);
          animation-delay: 1.5s;
        }
        @keyframes plGlowPulse {
          0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: 1; transform: translate(-50%, -50%) scale(1.15); }
        }

        .pl-content {
          position: relative; z-index: 1;
          display: flex; flex-direction: column; align-items: center;
        }

        .pl-orb {
          position: relative; width: 120px; height: 120px; margin-bottom: 40px;
        }
        .pl-orbit {
          position: absolute; inset: 0; border-radius: 50%;
          border: 2px solid transparent;
          border-top-color: var(--sp-accent, #6c5ce7);
          animation: plSpin 1.4s linear infinite;
        }
        .pl-orbit-2 {
          inset: 12px;
          border-top-color: transparent;
          border-right-color: var(--sp-green, #00d26a);
          border-bottom-color: var(--sp-green, #00d26a);
          animation-duration: 2s;
          animation-direction: reverse;
        }
        .pl-orbit-3 {
          inset: 24px;
          border-top-color: var(--sp-orange, #f7931a);
          border-left-color: var(--sp-orange, #f7931a);
          border-right-color: transparent;
          border-bottom-color: transparent;
          animation-duration: 2.8s;
        }
        @keyframes plSpin { to { transform: rotate(360deg); } }

        .pl-core {
          position: absolute; inset: 32px;
          display: flex; align-items: center; justify-content: center;
          font-size: 28px; font-weight: 800; letter-spacing: -1px;
          color: var(--sp-t1, #fff);
          background: radial-gradient(circle, var(--sp-card, #17171f) 60%, transparent);
          border-radius: 50%;
          animation: plCorePulse 2s ease-in-out infinite;
        }
        @keyframes plCorePulse {
          0%, 100% { text-shadow: 0 0 12px rgba(108,92,231,.6); }
          50% { text-shadow: 0 0 28px rgba(108,92,231,.8), 0 0 60px rgba(108,92,231,.15); }
        }

        .pl-title {
          font-size: 32px; font-weight: 800; letter-spacing: 2px;
          color: var(--sp-t1, #fff); margin-bottom: 28px;
          background: linear-gradient(135deg, #fff, #6c5ce7);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .pl-bar-track {
          width: 260px; height: 3px; border-radius: 3px;
          background: var(--sp-border, #2a2a35); overflow: hidden; margin-bottom: 24px;
          position: relative;
        }
        .pl-bar-glow {
          position: absolute; top: 0; left: 0;
          width: 40%; height: 100%; border-radius: 3px;
          background: linear-gradient(90deg, #6c5ce7, #00d26a, #6c5ce7);
          box-shadow: 0 0 12px rgba(108,92,231,.6);
          animation: plBarSlide 1.8s ease-in-out infinite;
        }
        @keyframes plBarSlide {
          0% { left: -40%; }
          100% { left: 100%; }
        }

        .pl-dots {
          display: flex; gap: 8px; margin-bottom: 20px;
        }
        .pl-dot {
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--sp-accent, #6c5ce7);
          animation: plDotBounce 1.2s ease-in-out infinite;
        }
        .pl-dot:nth-child(2) { animation-delay: 0.15s; }
        .pl-dot:nth-child(3) { animation-delay: 0.3s; }
        @keyframes plDotBounce {
          0%, 80%, 100% { opacity: 0.3; transform: scale(1); }
          40% { opacity: 1; transform: scale(1.5); }
        }

        .pl-sub {
          font-size: 14px; color: var(--sp-t3, #888); letter-spacing: 0.5px;
          margin: 0;
        }
      `}</style>
    </div>
  )
}
