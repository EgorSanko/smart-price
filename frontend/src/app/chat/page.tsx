/**
 * AI Chat page - фиолетово-графитовая тема
 */

'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Sparkles, ShoppingCart, TrendingDown, Search } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const SUGGESTED_PROMPTS = [
  { icon: Search, text: 'Найди iPhone 15 Pro дешевле 100 000 ₽' },
  { icon: TrendingDown, text: 'Когда лучше купить телевизор Samsung?' },
  { icon: ShoppingCart, text: 'Сравни цены на AirPods Pro 2' },
  { icon: Sparkles, text: 'Посоветуй хороший робот-пылесос до 30 000 ₽' },
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      await new Promise((resolve) => setTimeout(resolve, 1500))
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getSimulatedResponse(userMessage.content),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Извините, произошла ошибка. Попробуйте повторить запрос.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handlePromptClick = (prompt: string) => {
    setInput(prompt)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="container py-8 max-w-4xl">
      <div className="card overflow-hidden flex flex-col h-[calc(100vh-12rem)]">
        {/* Header */}
        <div className="p-4 border-b border-graphite-600 bg-graphite-900">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-accent/20 rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-accent-light" />
            </div>
            <div>
              <h1 className="font-semibold text-txt-primary">AI-ассистент Smart Price</h1>
              <p className="text-sm text-txt-muted">Помогу найти лучшие цены и ответить на вопросы</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-accent/20 rounded-full flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-accent-light" />
              </div>
              <h2 className="text-xl font-semibold text-txt-primary mb-2">Привет! Я ваш AI-помощник</h2>
              <p className="text-txt-secondary max-w-md mb-8">
                Могу помочь найти товары, сравнить цены, проанализировать историю цен и дать рекомендации
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
                {SUGGESTED_PROMPTS.map((prompt, i) => {
                  const Icon = prompt.icon
                  return (
                    <button
                      key={i}
                      onClick={() => handlePromptClick(prompt.text)}
                      className="flex items-center gap-3 p-3 text-left border border-graphite-600 rounded-xl hover:bg-graphite-700 hover:border-accent/30 transition-colors"
                    >
                      <Icon className="w-5 h-5 text-accent-light flex-shrink-0" />
                      <span className="text-sm text-txt-secondary">{prompt.text}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn('flex gap-3', message.role === 'user' ? 'justify-end' : 'justify-start')}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 bg-accent/20 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot className="w-5 h-5 text-accent-light" />
                    </div>
                  )}
                  <div
                    className={cn(
                      'max-w-[80%] rounded-2xl px-4 py-3',
                      message.role === 'user' ? 'bg-accent text-white' : 'bg-graphite-700 text-txt-primary'
                    )}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    <p className={cn('text-xs mt-1', message.role === 'user' ? 'text-white/60' : 'text-txt-muted')}>
                      {message.timestamp.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  {message.role === 'user' && (
                    <div className="w-8 h-8 bg-graphite-700 rounded-full flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-txt-secondary" />
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-accent/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-accent-light" />
                  </div>
                  <div className="bg-graphite-700 rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-accent" />
                      <span className="text-txt-muted">Думаю...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-graphite-600 bg-graphite-900">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Спросите что-нибудь..."
              rows={1}
              className="flex-1 px-4 py-3 bg-graphite-800 border border-graphite-600 text-txt-primary placeholder:text-txt-muted rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
              style={{ maxHeight: '120px' }}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-4 py-3 bg-accent text-white rounded-xl hover:bg-accent-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <p className="text-xs text-txt-muted text-center mt-2">
            AI может ошибаться. Проверяйте важную информацию.
          </p>
        </div>
      </div>
    </div>
  )
}

function getSimulatedResponse(userMessage: string): string {
  const lowerMessage = userMessage.toLowerCase()

  if (lowerMessage.includes('iphone')) {
    return `Я нашёл несколько предложений iPhone 15 Pro:

📱 Ozon: 94 990 ₽ — лучшая цена!
📱 Wildberries: 97 500 ₽
📱 Яндекс Маркет: 99 990 ₽

💡 Рекомендую купить на Ozon — там сейчас самая низкая цена.

Хотите настроить уведомление о снижении цены?`
  }

  if (lowerMessage.includes('телевизор') || lowerMessage.includes('samsung')) {
    return `📊 Анализ цен на телевизоры Samsung:

Лучшее время для покупки:
• Чёрная пятница (ноябрь) — скидки до 30%
• После Нового года (январь) — распродажа
• 11.11 — скидки на AliExpress

Текущий тренд: через 2 недели ожидается акция на Wildberries.

Хотите найти конкретную модель?`
  }

  if (lowerMessage.includes('airpods')) {
    return `🎧 Сравнение цен на AirPods Pro 2:

• Ozon — 21 990 ₽ (лучшая цена!)
• Wildberries — 22 500 ₽
• Яндекс Маркет — 23 990 ₽

⚡ Минимум за 3 месяца: 19 990 ₽ (11.11)

Настроить уведомление при цене ниже 20 000 ₽?`
  }

  if (lowerMessage.includes('пылесос') || lowerMessage.includes('робот')) {
    return `🤖 Рекомендую робот-пылесосы до 30 000 ₽:

1. Xiaomi Robot Vacuum S10 — 24 990 ₽
   ⭐ 4.7 • Влажная уборка, лидар

2. Dreame D9 Max — 27 990 ₽
   ⭐ 4.8 • Мощное всасывание

3. Roborock Q7 Max — 29 990 ₽
   ⭐ 4.9 • Лучший в классе

Рекомендую Xiaomi S10 — сейчас минимальная цена!`
  }

  return `Я могу помочь:

🔍 Поиск товаров на всех маркетплейсах
📊 Сравнение цен
📈 Анализ истории цен
🔔 Уведомления о снижении

Попробуйте спросить:
• "Найди iPhone 15 дешевле 100 000 ₽"
• "Сравни цены на AirPods Pro 2"
• "Когда лучше купить телевизор?"`
}
