'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { User, LogOut } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export default function DashboardPage() {
  const router = useRouter()
  const { user, token, logout, fetchMe } = useAuth()

  useEffect(() => {
    if (!token) {
      router.push('/login')
      return
    }
    fetchMe()
  }, [token, router, fetchMe])

  if (!user) {
    return <div className="container py-12 text-center text-[var(--td)]">Загрузка...</div>
  }

  return (
    <div className="container py-8 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-[var(--t)]">Личный кабинет</h1>

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

      <button
        onClick={() => { logout(); router.push('/') }}
        className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors"
      >
        <LogOut className="w-4 h-4" /> Выйти из аккаунта
      </button>
    </div>
  )
}
