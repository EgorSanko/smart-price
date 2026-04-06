'use client'

import Link from 'next/link'
import { XCircle, ArrowRight } from 'lucide-react'

export default function PaymentCancelPage() {
  return (
    <div className="container py-20 max-w-md mx-auto text-center">
      <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
      <h1 className="text-2xl font-bold text-[var(--t)] mb-2">Оплата отменена</h1>
      <p className="text-[var(--td)] mb-6">Платёж не был завершён. Вы можете попробовать снова.</p>
      <Link
        href="/pricing"
        className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--ac)] hover:bg-[var(--ac2)] text-white font-semibold rounded-xl transition-all"
      >
        Вернуться к тарифам <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  )
}
