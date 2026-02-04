/**
 * Home page with working search
 */

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { 
  TrendingDown, 
  BarChart2, 
  Bell, 
  Bot,
  Smartphone,
  Laptop,
  Headphones,
  Tv,
  ArrowRight,
  Check,
  Zap,
  Shield,
  Clock,
  Search
} from 'lucide-react'

const categories = [
  { name: 'Смартфоны', slug: 'smartphones', query: 'iPhone Samsung', icon: Smartphone, count: '12 000+', gradient: 'from-blue-500 to-blue-600' },
  { name: 'Ноутбуки', slug: 'laptops', query: 'MacBook ноутбук', icon: Laptop, count: '8 500+', gradient: 'from-purple-500 to-purple-600' },
  { name: 'Наушники', slug: 'headphones', query: 'AirPods наушники Sony', icon: Headphones, count: '15 000+', gradient: 'from-orange-500 to-orange-600' },
  { name: 'Телевизоры', slug: 'tvs', query: 'телевизор Samsung', icon: Tv, count: '6 000+', gradient: 'from-red-500 to-red-600' },
]

const features = [
  {
    icon: TrendingDown,
    title: 'Сравнение цен',
    description: 'Видите цены на один товар со всех маркетплейсов одновременно',
    href: '/compare',
  },
  {
    icon: BarChart2,
    title: 'История цен',
    description: 'Отслеживайте динамику и находите лучшее время для покупки',
    href: '/search?q=iPhone',
  },
  {
    icon: Bell,
    title: 'Уведомления',
    description: 'Узнайте первым, когда цена снизится до нужного уровня',
    href: '/search?q=AirPods',
  },
  {
    icon: Bot,
    title: 'AI-помощник',
    description: 'Умный ассистент поможет выбрать и сравнить товары',
    href: '/chat',
  },
]

const marketplaces = [
  { name: 'Ozon', color: '#005bff' },
  { name: 'Wildberries', color: '#cb11ab' },
  { name: 'Яндекс Маркет', color: '#ffcc00' },
  { name: 'AliExpress', color: '#ff4747' },
]

export default function HomePage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="py-16 lg:py-24">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent-light text-sm font-medium mb-6">
              <Zap className="w-4 h-4" />
              Мета-поиск по 4+ маркетплейсам
            </div>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-txt-primary mb-6">
              Найдите лучшую цену{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-accent-light">
                за секунды
              </span>
            </h1>
            <p className="text-lg md:text-xl text-txt-secondary mb-8 max-w-2xl mx-auto">
              Сравнивайте цены, отслеживайте скидки и получайте уведомления 
              о снижении цен на миллионы товаров
            </p>

            {/* Search form */}
            <form onSubmit={handleSearch} className="max-w-xl mx-auto mb-8">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Искать товары..."
                  className="w-full h-14 pl-5 pr-32 rounded-2xl bg-graphite-800 border border-graphite-600 text-txt-primary placeholder:text-txt-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent text-lg"
                />
                <button
                  type="submit"
                  className="absolute right-2 top-2 bottom-2 px-6 bg-accent text-white rounded-xl hover:bg-accent-light transition-colors font-semibold flex items-center gap-2"
                >
                  <Search className="w-5 h-5" />
                  <span className="hidden sm:inline">Найти</span>
                </button>
              </div>
            </form>

            {/* Маркетплейсы */}
            <div className="flex items-center justify-center gap-3 flex-wrap">
              <span className="text-sm text-txt-muted">Ищем на:</span>
              {marketplaces.map((mp) => (
                <span
                  key={mp.name}
                  className="text-sm font-semibold px-3 py-1.5 rounded-full border-2 transition-all hover:scale-105 cursor-default"
                  style={{ borderColor: mp.color, color: mp.color }}
                >
                  {mp.name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-4 border-y border-graphite-600 bg-graphite-900">
        <div className="container">
          <div className="flex items-center justify-center gap-8 flex-wrap text-sm">
            <div className="flex items-center gap-2 text-txt-secondary">
              <Check className="w-5 h-5 text-accent" />
              <span className="font-medium">Бесплатный сервис</span>
            </div>
            <div className="flex items-center gap-2 text-txt-secondary">
              <Zap className="w-5 h-5 text-accent" />
              <span className="font-medium">Поиск за секунды</span>
            </div>
            <div className="flex items-center gap-2 text-txt-secondary">
              <Shield className="w-5 h-5 text-accent" />
              <span className="font-medium">Проверенные магазины</span>
            </div>
            <div className="flex items-center gap-2 text-txt-secondary">
              <Clock className="w-5 h-5 text-accent" />
              <span className="font-medium">Обновление каждый час</span>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16">
        <div className="container">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl md:text-3xl font-bold text-txt-primary">
              Популярные категории
            </h2>
            <Link 
              href="/search" 
              className="text-accent-light font-semibold hover:text-accent flex items-center gap-1 transition-colors"
            >
              Все категории
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {categories.map((category) => {
              const Icon = category.icon
              return (
                <Link
                  key={category.slug}
                  href={`/search?q=${encodeURIComponent(category.query)}`}
                  className="group bg-graphite-800 hover:bg-graphite-700 rounded-2xl p-6 border border-graphite-600 hover:border-accent/30 transition-all"
                >
                  <div className={`w-14 h-14 bg-gradient-to-br ${category.gradient} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-lg`}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="font-semibold text-txt-primary mb-1">
                    {category.name}
                  </h3>
                  <p className="text-sm text-txt-muted">{category.count} товаров</p>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-graphite-900">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-txt-primary mb-4">
              Почему SmartPrice?
            </h2>
            <p className="text-lg text-txt-secondary max-w-2xl mx-auto">
              Экономьте время и деньги с помощью умного поиска и AI-аналитики
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon
              return (
                <Link
                  key={feature.title}
                  href={feature.href}
                  className="bg-graphite-800 rounded-2xl p-6 border border-graphite-600 hover:border-accent/30 transition-all group"
                >
                  <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
                    <Icon className="w-6 h-6 text-accent-light" />
                  </div>
                  <h3 className="text-lg font-semibold text-txt-primary mb-2 group-hover:text-accent-light transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-txt-secondary text-sm">
                    {feature.description}
                  </p>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gradient-to-r from-accent to-accent-light">
        <div className="container text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
            Начните экономить прямо сейчас
          </h2>
          <p className="text-white/80 text-lg mb-8 max-w-xl mx-auto">
            Введите название товара в поиске и узнайте, где купить дешевле
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/search?q=iPhone"
              className="inline-flex items-center gap-2 bg-white text-accent font-semibold rounded-xl px-8 py-3 hover:bg-gray-100 transition-colors shadow-lg"
            >
              Попробовать поиск
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 font-semibold text-white border-2 border-white/30 rounded-xl px-8 py-3 hover:bg-white/10 transition-colors"
            >
              <Bot className="w-5 h-5" />
              AI-помощник
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
