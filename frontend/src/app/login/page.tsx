'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Mail, Lock, User, Eye, EyeOff, LogIn, UserPlus } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const { login, register, user, isLoading, error, clearError } = useAuth()
  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [showPass, setShowPass] = useState(false)

  useEffect(() => {
    if (user) router.push('/dashboard')
  }, [user, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    let ok: boolean
    if (tab === 'login') {
      ok = await login(email, password)
    } else {
      ok = await register(email, password, fullName)
    }
    if (ok) router.push('/dashboard')
  }

  return (
    <div className="container py-12 max-w-md mx-auto">
      {/* Tabs */}
      <div className="flex mb-6 bg-[var(--c1)] rounded-xl p-1">
        <button
          onClick={() => { setTab('login'); clearError() }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
            tab === 'login' ? 'bg-[var(--ac)] text-white' : 'text-[var(--td)] hover:text-[var(--t)]'
          }`}
        >
          <LogIn className="w-4 h-4" /> Вход
        </button>
        <button
          onClick={() => { setTab('register'); clearError() }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
            tab === 'register' ? 'bg-[var(--ac)] text-white' : 'text-[var(--td)] hover:text-[var(--t)]'
          }`}
        >
          <UserPlus className="w-4 h-4" /> Регистрация
        </button>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-[var(--c1)] rounded-2xl p-6 space-y-4 border border-[var(--bd)]">
        <h1 className="text-xl font-bold text-[var(--t)] mb-2">
          {tab === 'login' ? 'Вход в аккаунт' : 'Создание аккаунта'}
        </h1>

        {tab === 'register' && (
          <div className="relative">
            <User className="absolute left-3 top-3 w-5 h-5 text-[var(--td)]" />
            <input
              type="text"
              placeholder="Имя (необязательно)"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              className="w-full pl-11 pr-4 py-2.5 bg-[var(--c2)] border border-[var(--bd)] rounded-xl text-sm text-[var(--t)] placeholder:text-[var(--td)] focus:outline-none focus:border-[var(--ac)]"
            />
          </div>
        )}

        <div className="relative">
          <Mail className="absolute left-3 top-3 w-5 h-5 text-[var(--td)]" />
          <input
            type="email"
            placeholder="Email"
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 bg-[var(--c2)] border border-[var(--bd)] rounded-xl text-sm text-[var(--t)] placeholder:text-[var(--td)] focus:outline-none focus:border-[var(--ac)]"
          />
        </div>

        <div className="relative">
          <Lock className="absolute left-3 top-3 w-5 h-5 text-[var(--td)]" />
          <input
            type={showPass ? 'text' : 'password'}
            placeholder="Пароль"
            required
            minLength={6}
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full pl-11 pr-11 py-2.5 bg-[var(--c2)] border border-[var(--bd)] rounded-xl text-sm text-[var(--t)] placeholder:text-[var(--td)] focus:outline-none focus:border-[var(--ac)]"
          />
          <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-3 text-[var(--td)]">
            {showPass ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>

        {error && (
          <div className="text-red-400 text-sm bg-red-500/10 rounded-lg px-3 py-2">{error}</div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 bg-[var(--ac)] hover:bg-[var(--ac2)] text-white font-semibold rounded-xl transition-all disabled:opacity-50"
        >
          {isLoading ? 'Загрузка...' : tab === 'login' ? 'Войти' : 'Зарегистрироваться'}
        </button>
      </form>

    </div>
  )
}
