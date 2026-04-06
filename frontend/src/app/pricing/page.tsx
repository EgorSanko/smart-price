'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Check, Zap, Crown, Rocket } from 'lucide-react'
import { useAuth, authFetch } from '@/lib/auth'

const PLANS = [
  {
    id: 'free',
    name: 'Бесплатный',
    price: '0',
    period: '',
    icon: Zap,
    color: 'var(--td)',
    features: [
      'Поиск по маркетплейсам',
      'Каталог товаров',
      'Сравнение до 3 товаров',
      'История цен за 7 дней',
    ],
    limitations: [
      'Ограничение поисков',
      'Нет уведомлений о скидках',
      'Нет экспорта данных',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '299',
    period: '/мес',
    icon: Crown,
    color: 'var(--ac)',
    popular: true,
    features: [
      'Безлимитный поиск',
      'История цен за 365 дней',
      'Уведомления о скидках (до 10)',
      'Безлимитное сравнение',
      'AI-помощник без лимитов',
      'Приоритетная загрузка',
    ],
    limitations: [],
  },
  {
    id: 'business',
    name: 'Business',
    price: '799',
    period: '/мес',
    icon: Rocket,
    color: '#a855f7',
    features: [
      'Всё из Pro',
      'API доступ',
      'Безлимитные уведомления',
      'Экспорт в CSV/Excel',
      'Приоритетная поддержка',
      'Мониторинг конкурентов',
    ],
    limitations: [],
  },
]

export default function PricingPage() {
  const router = useRouter()
  const { user, token } = useAuth()
  const [loading, setLoading] = useState<string | null>(null)

  const handleSubscribe = async (planId: string) => {
    if (!token) {
      router.push('/login')
      return
    }
    if (planId === 'free') return

    setLoading(planId)
    try {
      const res = await authFetch('/api/v1/payments/create', {
        method: 'POST',
        body: JSON.stringify({ plan: planId }),
      })
      if (res.ok) {
        const data = await res.json()
        window.location.href = data.confirmation_url
      } else {
        alert('Ошибка создания платежа')
      }
    } catch {
      alert('Ошибка сети')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="container py-12 max-w-5xl mx-auto">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-[var(--t)] mb-3">Тарифные планы</h1>
        <p className="text-[var(--td)] text-lg">Выберите план, подходящий именно вам</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map(plan => {
          const Icon = plan.icon
          const isCurrent = user?.subscription_plan === plan.id
          return (
            <div
              key={plan.id}
              className={`relative bg-[var(--c1)] rounded-2xl border p-6 flex flex-col ${
                plan.popular
                  ? 'border-[var(--ac)] shadow-lg shadow-[var(--ac)]/10'
                  : 'border-[var(--bd)]'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-[var(--ac)] text-white text-xs font-bold rounded-full">
                  Популярный
                </div>
              )}

              <div className="mb-4">
                <Icon className="w-8 h-8 mb-3" style={{ color: plan.color }} />
                <h2 className="text-xl font-bold text-[var(--t)]">{plan.name}</h2>
                <div className="mt-2">
                  <span className="text-3xl font-black text-[var(--t)]">{plan.price} ₽</span>
                  <span className="text-[var(--td)] text-sm">{plan.period}</span>
                </div>
              </div>

              <ul className="space-y-2.5 mb-6 flex-1">
                {plan.features.map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <Check className="w-4 h-4 mt-0.5 shrink-0" style={{ color: plan.color }} />
                    <span className="text-[var(--t)]">{f}</span>
                  </li>
                ))}
                {plan.limitations.map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-[var(--td)]">
                    <span className="w-4 h-4 mt-0.5 shrink-0 text-center">—</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSubscribe(plan.id)}
                disabled={isCurrent || loading === plan.id}
                className={`w-full py-3 rounded-xl font-semibold text-sm transition-all ${
                  isCurrent
                    ? 'bg-[var(--c2)] text-[var(--td)] cursor-default'
                    : plan.popular
                      ? 'bg-[var(--ac)] hover:bg-[var(--ac2)] text-white'
                      : 'bg-[var(--c2)] hover:bg-[var(--c3)] text-[var(--t)]'
                } disabled:opacity-50`}
              >
                {loading === plan.id ? 'Обработка...' : isCurrent ? 'Текущий план' : plan.id === 'free' ? 'Бесплатно' : 'Оформить подписку'}
              </button>
            </div>
          )
        })}
      </div>

      {/* Payment info */}
      <div className="mt-10 text-center text-sm text-[var(--td)] space-y-1">
        <p>Оплата через ЮKassa. Безопасная обработка платежей.</p>
        <p>Подписка активируется мгновенно после оплаты. Отмена в любое время.</p>
      </div>
    </div>
  )
}
