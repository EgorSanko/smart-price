/**
 * Docs page - фиолетово-графитовая тема
 */

import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Документация',
}
import { BookOpen, Code, Rocket, Settings, Search, Bell, BarChart2, Bot } from 'lucide-react'

const sections = [
  {
    title: 'Начало работы',
    icon: Rocket,
    items: [
      { title: 'Как искать товары', href: '#search' },
      { title: 'Сравнение цен', href: '#compare' },
      { title: 'Уведомления', href: '#alerts' },
    ],
  },
  {
    title: 'Функции',
    icon: Settings,
    items: [
      { title: 'Мета-поиск', href: '#meta-search' },
      { title: 'История цен', href: '#price-history' },
      { title: 'AI-ассистент', href: '#ai' },
    ],
  },
  {
    title: 'API',
    icon: Code,
    items: [
      { title: 'Документация API', href: '#api' },
      { title: 'Примеры запросов', href: '#examples' },
      { title: 'Лимиты', href: '#limits' },
    ],
  },
]

const guides = [
  {
    icon: Search,
    title: 'Поиск товаров',
    description: 'Введите название товара в поисковую строку. Система найдёт товары на всех подключённых маркетплейсах и покажет сравнение цен.',
  },
  {
    icon: BarChart2,
    title: 'Сравнение цен',
    description: 'На странице товара вы увидите цены со всех маркетплейсов. Лучшая цена выделена. Нажмите "Перейти к покупке" для перехода в магазин.',
  },
  {
    icon: Bell,
    title: 'Уведомления о цене',
    description: 'Нажмите на колокольчик на странице товара и укажите целевую цену. Мы уведомим вас, когда цена снизится.',
  },
  {
    icon: Bot,
    title: 'AI-ассистент',
    description: 'Перейдите в раздел "AI Помощник" и задайте вопрос. AI поможет найти товары, сравнить цены и даст рекомендации.',
  },
]

export default function DocsPage() {
  return (
    <div className="min-h-screen py-16">
      <div className="container">
        <div className="grid lg:grid-cols-[280px_1fr] gap-8">
          {/* Sidebar */}
          <aside className="hidden lg:block">
            <div className="sticky top-20">
              <div className="card p-4">
                <h2 className="font-semibold text-txt-primary mb-4 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-accent-light" />
                  Документация
                </h2>
                <nav className="space-y-4">
                  {sections.map((section) => {
                    const Icon = section.icon
                    return (
                      <div key={section.title}>
                        <h3 className="flex items-center gap-2 text-sm font-medium text-txt-secondary mb-2">
                          <Icon className="w-4 h-4" />
                          {section.title}
                        </h3>
                        <ul className="space-y-1 ml-6">
                          {section.items.map((item) => (
                            <li key={item.title}>
                              <a
                                href={item.href}
                                className="block text-sm text-txt-muted hover:text-accent-light transition-colors py-1"
                              >
                                {item.title}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )
                  })}
                </nav>
              </div>
            </div>
          </aside>

          {/* Content */}
          <main className="min-w-0">
            <div className="mb-12">
              <h1 className="text-4xl font-bold text-txt-primary mb-4">Документация</h1>
              <p className="text-xl text-txt-secondary">
                Руководство по использованию Smart Price
              </p>
            </div>

            {/* Quick Start */}
            <section id="search" className="mb-12">
              <h2 className="text-2xl font-bold text-txt-primary mb-6">Быстрый старт</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {guides.map((guide) => {
                  const Icon = guide.icon
                  return (
                    <div key={guide.title} className="card p-6">
                      <div className="w-10 h-10 bg-accent/20 rounded-xl flex items-center justify-center mb-4">
                        <Icon className="w-5 h-5 text-accent-light" />
                      </div>
                      <h3 className="font-semibold text-txt-primary mb-2">{guide.title}</h3>
                      <p className="text-sm text-txt-secondary">{guide.description}</p>
                    </div>
                  )
                })}
              </div>
            </section>

            {/* Meta Search */}
            <section id="meta-search" className="mb-12">
              <h2 className="text-2xl font-bold text-txt-primary mb-4">Мета-поиск</h2>
              <div className="card p-6">
                <p className="text-txt-secondary mb-4">
                  Smart Price выполняет поиск по нескольким маркетплейсам одновременно:
                </p>
                <ul className="space-y-2">
                  <li className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-[#ff6600]" />
                    <span className="text-txt-primary">Ситилинк</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-[#cb11ab]" />
                    <span className="text-txt-primary">Wildberries</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-[#ffcc00]" />
                    <span className="text-txt-primary">Яндекс Маркет</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-[#ff4747]" />
                    <span className="text-txt-primary">AliExpress</span>
                  </li>
                </ul>
              </div>
            </section>

            {/* API */}
            <section id="api" className="mb-12">
              <h2 className="text-2xl font-bold text-txt-primary mb-4">API</h2>
              <div className="card p-6">
                <p className="text-txt-secondary mb-4">
                  Smart Price предоставляет REST API для интеграции:
                </p>
                <div className="bg-graphite-900 rounded-xl p-4 font-mono text-sm">
                  <p className="text-txt-muted"># Поиск товаров</p>
                  <p className="text-accent-light">GET /api/v1/search?q=iphone</p>
                  <p className="text-txt-muted mt-4"># Получение товара</p>
                  <p className="text-accent-light">GET /api/v1/products/123</p>
                  <p className="text-txt-muted mt-4"># История цен</p>
                  <p className="text-accent-light">GET /api/v1/products/123/history</p>
                </div>
                <p className="text-sm text-txt-muted mt-4">
                  Полная документация API доступна по адресу{' '}
                  <code className="text-accent-light">/api/docs</code>
                </p>
              </div>
            </section>

            {/* FAQ */}
            <section id="faq" className="mb-12">
              <h2 className="text-2xl font-bold text-txt-primary mb-4">FAQ</h2>
              <div className="space-y-4">
                <div className="card p-6">
                  <h3 className="font-semibold text-txt-primary mb-2">Это бесплатно?</h3>
                  <p className="text-txt-secondary">Да, Smart Price полностью бесплатен для использования.</p>
                </div>
                <div className="card p-6">
                  <h3 className="font-semibold text-txt-primary mb-2">Как часто обновляются цены?</h3>
                  <p className="text-txt-secondary">Цены обновляются каждый час для популярных товаров.</p>
                </div>
                <div className="card p-6">
                  <h3 className="font-semibold text-txt-primary mb-2">Почему цена отличается от магазина?</h3>
                  <p className="text-txt-secondary">
                    Цены могут меняться в реальном времени. Мы рекомендуем проверять финальную цену на сайте магазина.
                  </p>
                </div>
              </div>
            </section>

            {/* Contact */}
            <div className="p-6 bg-accent/10 border border-accent/20 rounded-2xl">
              <h3 className="font-semibold text-accent-light mb-2">Нужна помощь?</h3>
              <p className="text-txt-secondary text-sm">
                Если у вас есть вопросы, напишите нам на{' '}
                <a href="mailto:support@smartprice.ru" className="text-accent-light hover:underline">
                  support@smartprice.ru
                </a>
              </p>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
