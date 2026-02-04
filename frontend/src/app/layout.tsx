import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Header, Footer } from '@/components/layout'
import { Providers } from './providers'
import './globals.css'

const inter = Inter({ subsets: ['latin', 'cyrillic'] })

export const metadata: Metadata = {
  title: {
    template: '%s | Smart Price',
    default: 'Smart Price — Умный поиск товаров',
  },
  description:
    'AI-powered метапоиск товаров с интеллектуальным анализом цен на Ozon, Wildberries, Яндекс Маркет и AliExpress',
  keywords: [
    'поиск товаров',
    'сравнение цен',
    'ozon',
    'wildberries',
    'яндекс маркет',
    'aliexpress',
    'скидки',
    'акции',
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen flex flex-col">
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  )
}
