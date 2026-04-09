/**
 * About page - фиолетово-графитовая тема
 */

import type { Metadata } from 'next'
import { Github, Mail, Code, Database, Brain, Zap } from 'lucide-react'

export const metadata: Metadata = {
  title: 'О проекте',
}

const techStack = [
  { name: 'Next.js 14', category: 'Frontend', icon: Code },
  { name: 'FastAPI', category: 'Backend', icon: Zap },
  { name: 'PostgreSQL', category: 'Database', icon: Database },
  { name: 'Gemini AI', category: 'AI/ML', icon: Brain },
]

const features = [
  {
    title: 'Мета-поиск',
    description: 'Поиск по 6 маркетплейсам одновременно: Яндекс Маркет, Wildberries, Ситилинк, Регард, AliExpress, Onliner',
  },
  {
    title: 'Сравнение цен',
    description: 'Автоматическое сопоставление одинаковых товаров на разных площадках',
  },
  {
    title: 'История цен',
    description: 'Отслеживание динамики цен и прогнозирование лучшего времени для покупки',
  },
  {
    title: 'AI-ассистент',
    description: 'Умный помощник на базе AI для поиска товаров и рекомендаций',
  },
  {
    title: 'Уведомления',
    description: 'Оповещения о снижении цены до целевого уровня',
  },
  {
    title: 'Анализ отзывов',
    description: 'AI-суммаризация тысяч отзывов в ключевые тезисы',
  },
]

export default function AboutPage() {
  return (
    <div className="min-h-screen py-16">
      <div className="container max-w-4xl">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-txt-primary mb-4">О проекте Smart Price</h1>
          <p className="text-xl text-txt-secondary max-w-2xl mx-auto">
            AI-powered система метапоиска товаров с интеллектуальным анализом цен
          </p>
        </div>

        {/* About */}
        <div className="card p-8 mb-12">
          <h2 className="text-2xl font-bold text-txt-primary mb-4">Что такое Smart Price?</h2>
          <div className="prose prose-invert max-w-none text-txt-secondary space-y-4">
            <p>
              Smart Price — это дипломный проект, представляющий собой современную систему метапоиска товаров
              на крупнейших российских маркетплейсах с использованием искусственного интеллекта для анализа цен.
            </p>
            <p>
              Сервис позволяет пользователям находить лучшие цены на товары, сравнивать предложения
              с разных площадок, отслеживать историю изменения цен и получать умные рекомендации
              от AI-ассистента.
            </p>
          </div>
        </div>

        {/* Features */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-txt-primary mb-6">Возможности</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {features.map((feature) => (
              <div key={feature.title} className="card p-5 hover:border-accent/30 transition-colors">
                <h3 className="font-semibold text-txt-primary mb-2">{feature.title}</h3>
                <p className="text-sm text-txt-secondary">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Tech Stack */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-txt-primary mb-6">Технологии</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {techStack.map((tech) => {
              const Icon = tech.icon
              return (
                <div key={tech.name} className="card p-4 text-center">
                  <div className="w-12 h-12 bg-accent/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                    <Icon className="w-6 h-6 text-accent-light" />
                  </div>
                  <p className="font-semibold text-txt-primary">{tech.name}</p>
                  <p className="text-xs text-txt-muted">{tech.category}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Author */}
        <div className="card p-8">
          <h2 className="text-2xl font-bold text-txt-primary mb-6">Автор</h2>
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="w-24 h-24 bg-gradient-to-br from-accent to-accent-light rounded-full flex items-center justify-center text-white text-3xl font-bold">
              EP
            </div>
            <div className="text-center sm:text-left">
              <h3 className="text-xl font-semibold text-txt-primary mb-1">Егор</h3>
              <p className="text-txt-secondary mb-4">Студент • Full-stack разработчик</p>
              <div className="flex items-center justify-center sm:justify-start gap-4">
                <a href="https://github.com/EgorSanko/smart-price" target="_blank" rel="noopener noreferrer" className="text-txt-muted hover:text-accent-light transition-colors">
                  <Github className="w-5 h-5" />
                </a>
                <a href="mailto:egor3sanko22@mail.ru" className="text-txt-muted hover:text-accent-light transition-colors">
                  <Mail className="w-5 h-5" />
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-8 p-6 bg-accent/10 border border-accent/20 rounded-2xl text-center">
          <p className="text-txt-secondary text-sm">
            Это дипломный проект. Цены и данные о товарах могут отличаться от реальных.
            Сервис предоставляется «как есть» в образовательных целях.
          </p>
        </div>
      </div>
    </div>
  )
}
