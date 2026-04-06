'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { User, Crown, CreditCard, Calendar, LogOut, ArrowRight } from 'lucide-react'
import { useAuth, authFetch } from '@/lib/auth'

interface PaymentItem {
  id: number
  amount: number
  plan: string
  status: string
  created_at: string
  confirmed_at: string | null
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, token, logout, fetchMe } = useAuth()
  const [payments, setPayments] = useState<PaymentItem[]>([])

  useEffect(() => {
    if (!token) {
      router.push('/login')
      return
    }
    fetchMe()
    authFetch('/api/v1/payments/history').then(r => r.ok ? r.json() : []).then(setPayments).catch(() => {})
  }, [token, router, fetchMe])

  if (!user) {
    return <div className="container py-12 text-center text-[var(--td)]">Загрузка...</div>
  }

  const planNames: Record<string, string> = { free: 'Бесплатный', pro: 'Pro', business: 'Business' }
  const planColors: Record<string, string> = { free: 'var(--td)', pro: 'var(--ac)', business: '#a855f7' }
  const statusLabels: Record<string, string> = { pending: 'Ожидает', succeeded: 'Оплачено', canceled: 'Отменено' }
  const statusColors: Record<string, string> = { pending: 'text-yellow-400', succeeded: 'text-green-400', canceled: 'text-red-400' }

  return (
    <div className="container py-8 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-[var(--t)]">Личный кабинет</h1>

      {/* Profile card */}
      <div className="bg-[var(--c1)] rounded-2xl border border-[var(--bd)] p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-full bg-[var(--ac)]/20 flex items-center justify-center">
            <User className="w-7 h-7 text-[var(--ac)]" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[var(--t)]">{user.full_name || user.email.split('@')[0]}</h2>
            <p className="text-sm text-[var(--td)]">{user.email}</p>
          </div>
        </div>
      </div>

      {/* Subscription card */}
      <div className="bg-[var(--c1)] rounded-2xl border border-[var(--bd)] p-6">
        <div className="flex items-center gap-2 mb-4">
          <Crown className="w-5 h-5" style={{ color: planColors[user.subscription_plan] }} />
          <h3 className="text-lg font-bold text-[var(--t)]">Подписка</h3>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="text-2xl font-black" style={{ color: planColors[user.subscription_plan] }}>
              {planNames[user.subscription_plan] || user.subscription_plan}
            </p>
            {user.has_active_subscription && user.subscription_expires_at && (
              <p className="text-sm text-[var(--td)] flex items-center gap-1 mt-1">
                <Calendar className="w-4 h-4" />
                Активна до {new Date(user.subscription_expires_at).toLocaleDateString('ru-RU')}
              </p>
            )}
            {!user.has_active_subscription && user.subscription_plan === 'free' && (
              <p className="text-sm text-[var(--td)] mt-1">Бесплатный план с базовыми возможностями</p>
            )}
          </div>
          <Link
            href="/pricing"
            className="flex items-center gap-1 px-4 py-2 bg-[var(--ac)] hover:bg-[var(--ac2)] text-white text-sm font-semibold rounded-xl transition-all"
          >
            {user.subscription_plan === 'free' ? 'Улучшить' : 'Изменить'}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Payment history */}
      {payments.length > 0 && (
        <div className="bg-[var(--c1)] rounded-2xl border border-[var(--bd)] p-6">
          <div className="flex items-center gap-2 mb-4">
            <CreditCard className="w-5 h-5 text-[var(--ac)]" />
            <h3 className="text-lg font-bold text-[var(--t)]">История платежей</h3>
          </div>

          <div className="space-y-3">
            {payments.map(p => (
              <div key={p.id} className="flex items-center justify-between py-2 border-b border-[var(--bd)] last:border-0">
                <div>
                  <p className="text-sm font-medium text-[var(--t)]">
                    Подписка {planNames[p.plan] || p.plan}
                  </p>
                  <p className="text-xs text-[var(--td)]">
                    {new Date(p.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-[var(--t)]">{p.amount} ₽</p>
                  <p className={`text-xs font-medium ${statusColors[p.status] || 'text-[var(--td)]'}`}>
                    {statusLabels[p.status] || p.status}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logout */}
      <button
        onClick={() => { logout(); router.push('/') }}
        className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors"
      >
        <LogOut className="w-4 h-4" /> Выйти из аккаунта
      </button>
    </div>
  )
}
