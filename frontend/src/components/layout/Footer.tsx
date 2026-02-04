/**
 * Footer - фиолетово-графитовая тема
 */

import Link from 'next/link'
import { Github, Mail, Heart } from 'lucide-react'

const footerLinks = {
  product: [
    { name: 'Поиск товаров', href: '/' },
    { name: 'Сравнение цен', href: '/compare' },
    { name: 'AI Ассистент', href: '/chat' },
  ],
  marketplaces: [
    { name: 'Ozon', href: 'https://ozon.ru' },
    { name: 'Wildberries', href: 'https://wildberries.ru' },
    { name: 'Яндекс Маркет', href: 'https://market.yandex.ru' },
    { name: 'AliExpress', href: 'https://aliexpress.ru' },
  ],
}

export function Footer() {
  return (
    <footer className="bg-graphite-900 border-t border-graphite-600 mt-auto">
      <div className="container py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center shadow-glow">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <span className="text-xl font-semibold text-txt-primary">
                Smart<span className="text-accent-light">Price</span>
              </span>
            </Link>
            <p className="mt-4 text-sm text-txt-muted">
              AI-powered метапоиск товаров с интеллектуальным анализом цен
            </p>
            <div className="flex gap-4 mt-4">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-txt-muted hover:text-accent-light transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <a href="mailto:contact@smartprice.ru" className="text-txt-muted hover:text-accent-light transition-colors">
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-sm font-semibold text-txt-primary">Продукт</h3>
            <ul className="mt-4 space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.name}>
                  <Link href={link.href} className="text-sm text-txt-muted hover:text-accent-light transition-colors">
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Marketplaces */}
          <div>
            <h3 className="text-sm font-semibold text-txt-primary">Маркетплейсы</h3>
            <ul className="mt-4 space-y-3">
              {footerLinks.marketplaces.map((link) => (
                <li key={link.name}>
                  <a href={link.href} target="_blank" rel="noopener noreferrer" className="text-sm text-txt-muted hover:text-accent-light transition-colors">
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* About */}
          <div>
            <h3 className="text-sm font-semibold text-txt-primary">О проекте</h3>
            <ul className="mt-4 space-y-3">
              <li>
                <Link href="/about" className="text-sm text-txt-muted hover:text-accent-light transition-colors">
                  О нас
                </Link>
              </li>
              <li>
                <Link href="/docs" className="text-sm text-txt-muted hover:text-accent-light transition-colors">
                  Документация
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-graphite-600">
          <p className="text-sm text-txt-muted text-center flex items-center justify-center gap-1">
            Сделано с <Heart className="w-4 h-4 text-red-500" /> для дипломного проекта © {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </footer>
  )
}
