'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { CheckCircle, ArrowRight, Loader2 } from 'lucide-react'
import { useAuth, authFetch } from '@/lib/auth'

function SuccessContent() {
  const searchParams = useSearchParams()
  const { fetchMe } = useAuth()
  const [confirmed, setConfirmed] = useState(false)

  useEffect(() => {
    const mock = searchParams.get('mock')
    const paymentId = searchParams.get('payment_id')
    if (mock && paymentId) {
      authFetch(`/api/v1/payments/mock-confirm/${paymentId}`, { method: 'POST' })
        .then(() => { setConfirmed(true); fetchMe() })
        .catch(() => setConfirmed(true))
    } else {
      setTimeout(() => { fetchMe(); setConfirmed(true) }, 2000)
    }
  }, [searchParams, fetchMe])

  return confirmed ? (
    <>
      <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
      <h1 className="text-2xl font-bold text-[var(--t)] mb-2">Оплата прошла успешно!</h1>
      <p className="text-[var(--td)] mb-6">Ваша подписка активирована. Спасибо за покупку!</p>
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--ac)] hover:bg-[var(--ac2)] text-white font-semibold rounded-xl transition-all"
      >
        Перейти в кабинет <ArrowRight className="w-4 h-4" />
      </Link>
    </>
  ) : (
    <>
      <Loader2 className="w-12 h-12 text-[var(--ac)] mx-auto mb-4 animate-spin" />
      <h1 className="text-xl font-bold text-[var(--t)]">Обработка платежа...</h1>
    </>
  )
}

export default function PaymentSuccessPage() {
  return (
    <div className="container py-20 max-w-md mx-auto text-center">
      <Suspense fallback={<Loader2 className="w-12 h-12 text-[var(--ac)] mx-auto animate-spin" />}>
        <SuccessContent />
      </Suspense>
    </div>
  )
}
