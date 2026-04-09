'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, ExternalLink, Search, MessageCircle, Store, Sparkles, Copy, Check, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { chatWithAI, proxyImage, type Product, type ChatMessage } from '@/lib/api'

const MP_META: Record<string, { label: string; color: string; badge: string }> = {
  onliner:     { label: 'Onliner',       color: '#65cb02', badge: 'mp-badge-onliner' },
  yandex:      { label: 'Яндекс Маркет', color: '#ffcc00', badge: 'mp-badge-yandex' },
  wildberries: { label: 'Wildberries',    color: '#cb11ab', badge: 'mp-badge-wb' },
  citilink:    { label: 'Ситилинк',       color: '#ff6600', badge: 'mp-badge-citilink' },
  regard:      { label: 'Регард',         color: '#e53935', badge: 'mp-badge-regard' },
  aliexpress:  { label: 'AliExpress',     color: '#ff4747', badge: 'mp-badge-aliexpress' },
  worlddevices:{ label: 'World Devices',  color: '#2196f3', badge: 'mp-badge-worlddevices' },
  oneclick:    { label: '1click',         color: '#0084ff', badge: 'mp-badge-oneclick' },
  biggeek:     { label: 'BigGeek',        color: '#7b1fa2', badge: 'mp-badge-biggeek' },
}

interface Message extends ChatMessage {
  products?: Product[]
  isSearching?: boolean
  searchQuery?: string
}

const CHAT_STORAGE_KEY = 'sp_chat_state_v1'

interface PersistedChatState {
  messages: Message[]
  region: 'BY' | 'RU' | 'all'
}

function loadChatPersisted(): PersistedChatState | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(CHAT_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as PersistedChatState
  } catch {
    return null
  }
}

export default function ChatPage() {
  const [hydrated, setHydrated] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [region, setRegion] = useState<'BY' | 'RU' | 'all'>('BY')
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null)
  const [copiedAll, setCopiedAll] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  // Restore chat state on mount
  useEffect(() => {
    const saved = loadChatPersisted()
    if (saved) {
      setMessages(saved.messages || [])
      setRegion(saved.region || 'BY')
    }
    setHydrated(true)
  }, [])

  // Persist chat state on every change
  useEffect(() => {
    if (!hydrated) return
    try {
      const data: PersistedChatState = { messages, region }
      localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(data))
    } catch { /* ignore */ }
  }, [hydrated, messages, region])

  const clearChat = () => {
    cleanupRef.current?.()
    setMessages([])
    setInput('')
    setIsLoading(false)
    try { localStorage.removeItem(CHAT_STORAGE_KEY) } catch { /* ignore */ }
  }

  const copyToClipboard = async (text: string): Promise<boolean> => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
        return true
      }
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.focus()
      ta.select()
      const ok = document.execCommand('copy')
      document.body.removeChild(ta)
      return ok
    } catch {
      return false
    }
  }

  const handleCopyMessage = async (idx: number, content: string) => {
    const ok = await copyToClipboard(content)
    if (ok) {
      setCopiedIdx(idx)
      setTimeout(() => setCopiedIdx(null), 1500)
    }
  }

  const handleCopyAll = async () => {
    const text = messages
      .filter(m => m.content)
      .map(m => `${m.role === 'user' ? 'Я' : 'AI Помощник'}: ${m.content}`)
      .join('\n\n')
    const ok = await copyToClipboard(text)
    if (ok) {
      setCopiedAll(true)
      setTimeout(() => setCopiedAll(false), 1500)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => { scrollToBottom() }, [messages])

  const sendMessage = () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setMessages(prev => [...prev, { role: 'assistant', content: '', isSearching: false }])

    const history: ChatMessage[] = messages.map(m => ({ role: m.role, content: m.content }))

    cleanupRef.current = chatWithAI(
      userMessage, history, region, '',
      (data) => {
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (data.text) last.content += data.text
          if (data.searching) { last.isSearching = true; last.searchQuery = data.query }
          if (data.products) { last.products = data.products; last.isSearching = false }
          if (data.done) { last.isSearching = false; setIsLoading(false) }
          return updated
        })
      },
      () => {
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1].content = 'Ошибка подключения. Попробуйте ещё раз.'
          return updated
        })
        setIsLoading(false)
      }
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  useEffect(() => { return () => cleanupRef.current?.() }, [])

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 8rem)' }}>
      {/* Sub-header */}
      <div className="border-b border-[var(--bd)]" style={{ background: 'rgba(15,15,23,.8)', backdropFilter: 'blur(16px)' }}>
        <div className="container flex items-center gap-3 py-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--ac)] to-purple-500 flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h1 className="font-bold text-[var(--t)] text-sm tracking-tight">AI Помощник</h1>
            <p className="text-[11px] text-[var(--td)]">Поиск, сравнение и рекомендации товаров</p>
          </div>
          {messages.length > 0 && (
            <>
              <button
                onClick={handleCopyAll}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-[var(--td)] hover:text-[var(--t)] hover:bg-[var(--c2)] border border-[var(--bd)] transition-all flex items-center gap-1.5"
                title="Скопировать весь диалог"
              >
                {copiedAll ? <Check className="w-3.5 h-3.5 text-[var(--g)]" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{copiedAll ? 'Скопировано' : 'Копировать'}</span>
              </button>
              <button
                onClick={clearChat}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-[var(--td)] hover:text-[var(--t)] hover:bg-[var(--c2)] border border-[var(--bd)] transition-all flex items-center gap-1.5"
                title="Очистить чат"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Очистить</span>
              </button>
            </>
          )}
          <div className="flex gap-1 p-1 bg-[var(--c2)] rounded-xl border border-[var(--bd)]">
            {(['BY', 'RU'] as const).map(r => (
              <button
                key={r}
                onClick={() => setRegion(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  region === r
                    ? 'bg-[var(--ac)] text-white shadow-sm'
                    : 'text-[var(--td)] hover:text-[var(--t)]'
                }`}
              >
                {r === 'BY' ? '🇧🇾 BY' : '🇷🇺 RU'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="container py-6 space-y-5">
          {messages.length === 0 && (
            <div className="text-center py-16">
              <div className="w-20 h-20 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-[var(--ac)] to-purple-600 flex items-center justify-center shadow-lg shadow-[var(--ac-glow)]">
                <MessageCircle className="w-9 h-9 text-white" />
              </div>
              <h2 className="text-xl font-bold text-[var(--t)] mb-2">Спросите что угодно о товарах</h2>
              <p className="text-[var(--td)] text-sm mb-8 max-w-md mx-auto">
                Найду лучшие цены, сравню характеристики и помогу выбрать
              </p>

              <div className="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
                {[
                  'Найди iPhone 16 до 3000 BYN',
                  'Сравни Samsung и Xiaomi',
                  'Подбери ноутбук для работы',
                  'Какой телевизор купить?',
                ].map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(q)}
                    className="px-4 py-2.5 bg-[var(--c1)] rounded-xl text-xs text-[var(--td)] hover:text-[var(--t)] hover:bg-[var(--c2)] border border-[var(--bd)] hover:border-[var(--bd2)] transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <div key={idx} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
              <div className={`max-w-[85%] ${message.role === 'user' ? 'order-2' : ''}`}>
                {message.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--ac)] to-purple-500 flex items-center justify-center">
                      <Sparkles className="w-3.5 h-3.5 text-white" />
                    </div>
                    <span className="text-xs font-semibold text-[var(--td)]">AI Помощник</span>
                  </div>
                )}

                <div className={`rounded-2xl p-4 ${
                  message.role === 'user'
                    ? 'bg-[var(--ac)] text-white rounded-br-md'
                    : 'bg-[var(--c1)] border border-[var(--bd)] rounded-bl-md'
                }`}>
                  {message.isSearching && (
                    <div className="ai-search-card mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-[var(--ac)]/15 flex items-center justify-center shrink-0" style={{ animation: 'aiSearchPulse 2s ease-in-out infinite' }}>
                          <Search className="w-4.5 h-4.5 text-[var(--ac)]" style={{ animation: 'aiIconBounce 1s ease-in-out infinite' }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[13px] font-semibold text-[var(--t)]">Ищу по магазинам</span>
                            <div className="ai-search-dots flex gap-1">
                              <span /><span /><span />
                            </div>
                          </div>
                          <p className="text-[11px] text-[var(--td)] mt-0.5 truncate">{message.searchQuery}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {message.content && (
                    <div className="group/msg relative">
                      <div className={`chat-md text-sm leading-relaxed ${message.role === 'user' ? 'chat-md-user' : ''}`} style={{ WebkitUserSelect: 'text', userSelect: 'text' }}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                      </div>
                      <button
                        onClick={() => handleCopyMessage(idx, message.content)}
                        className={`absolute -top-1 -right-1 p-1.5 rounded-lg transition-all ${
                          message.role === 'user'
                            ? 'bg-white/15 hover:bg-white/25 text-white'
                            : 'bg-[var(--c2)] hover:bg-[var(--c3)] text-[var(--td)] hover:text-[var(--t)] border border-[var(--bd)]'
                        } opacity-60 hover:opacity-100 focus:opacity-100`}
                        title="Скопировать сообщение"
                        aria-label="Скопировать сообщение"
                      >
                        {copiedIdx === idx ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  )}

                  {message.role === 'assistant' && !message.content && isLoading && !message.isSearching && (
                    <div className="ai-thinking-card">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl bg-[var(--ac)]/10 flex items-center justify-center shrink-0">
                          <Sparkles className="w-4 h-4 text-[var(--ac)]" style={{ animation: 'aiIconBounce 1.2s ease-in-out infinite' }} />
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] text-[var(--td)]">Думаю</span>
                          <div className="ai-search-dots flex gap-1">
                            <span /><span /><span />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {message.products && message.products.length > 0 && (
                    <div className="mt-3 space-y-1.5">
                      {message.products.slice(0, 6).map((product, pIdx) => {
                        const mp = MP_META[product.marketplace] || { label: product.marketplace, color: '#888', badge: '' }
                        return (
                          <a
                            key={pIdx}
                            href={product.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-3 p-2.5 bg-[var(--c2)] rounded-xl hover:bg-[var(--c3)] border border-[var(--bd)] hover:border-[var(--bd2)] transition-all group"
                          >
                            {product.image ? (
                              <img src={proxyImage(product.image)} alt={product.title} className="w-11 h-11 object-contain bg-white rounded-lg p-0.5 shrink-0" />
                            ) : (
                              <div className="w-11 h-11 bg-white rounded-lg flex items-center justify-center shrink-0">
                                <Store className="w-5 h-5 text-gray-300" />
                              </div>
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-[var(--t)] line-clamp-1 font-medium">{product.title}</p>
                              <div className="flex items-center gap-1.5 mt-0.5">
                                <span className="text-[10px] text-[var(--tm)]">{product.shop}</span>
                                <span className={`badge text-[9px] py-0 px-1.5 ${mp.badge}`}>{mp.label}</span>
                              </div>
                            </div>
                            <div className="text-right shrink-0">
                              <p className="font-bold text-sm text-[var(--t)]">{product.price}</p>
                            </div>
                            <ExternalLink className="w-3.5 h-3.5 text-[var(--tm)] group-hover:text-[var(--ac)] transition-colors shrink-0" />
                          </a>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-[var(--bd)] p-4" style={{ background: 'rgba(10,10,15,.9)', backdropFilter: 'blur(16px)' }}>
        <div className="container">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Спросите о товарах..."
              className="input flex-1 py-3 rounded-xl"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              className="btn-primary px-4 rounded-xl"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
