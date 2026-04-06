'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  Smartphone, Laptop, Cpu, Tv, Camera, Gamepad2, Keyboard, Home,
  Heart, CookingPot, Lightbulb, ChevronRight, Search, ArrowLeft,
  Phone, Tablet, Headphones, Watch, Activity, BatteryCharging,
  Monitor, HardDrive, Plug, Box, Fan, Speaker, Wifi, Usb,
  Mouse, Armchair, Wind, Scissors, Smile, Scale, Shield,
  Sparkles, Flame, Droplets, Coffee, Loader2, Tag, Package,
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

const ICON_MAP: Record<string, any> = {
  Smartphone, Laptop, Cpu, Tv, Camera, Gamepad2, Keyboard, Home,
  Heart, CookingPot, Lightbulb, Phone, Tablet, Headphones, Watch,
  Activity, BatteryCharging, Monitor, HardDrive, Plug, Box, Fan,
  Speaker, Wifi, Usb, Mouse, Armchair, Wind, Scissors, Smile, Scale,
  Shield, Sparkles, Flame, Droplets, Coffee,
  MonitorSmartphone: Monitor, MonitorPlay: Monitor, MonitorUp: Monitor,
  MemoryStick: HardDrive, CircuitBoard: Cpu, AirVent: Wind,
  WashingMachine: Sparkles, Projector: Tv, Refrigerator: Home,
  Blend: CookingPot, SquareStack: Box, Hand: Heart,
}

interface CatalogChild {
  name: string
  slug: string
  icon?: string
  citilink?: string
}

interface CatalogGroup {
  name: string
  slug: string
  icon?: string
  children: CatalogChild[]
}

interface BrandInfo {
  name: string
  count: number
}

interface CatalogProduct {
  title: string
  brand: string
}

const CATALOG: CatalogGroup[] = [
  {
    name: 'Смартфоны и гаджеты', slug: 'smartphones-gadgets', icon: 'Smartphone',
    children: [
      { name: 'Смартфоны', slug: 'smartphones', icon: 'Smartphone' },
      { name: 'Планшеты', slug: 'tablets', icon: 'Tablet' },
      { name: 'Наушники', slug: 'headphones', icon: 'Headphones' },
      { name: 'Смарт-часы', slug: 'smartwatches', icon: 'Watch' },
      { name: 'Фитнес-браслеты', slug: 'fitness-bands', icon: 'Activity' },
      { name: 'Power Bank', slug: 'powerbanks', icon: 'BatteryCharging' },
    ],
  },
  {
    name: 'Ноутбуки и компьютеры', slug: 'laptops-pcs', icon: 'Laptop',
    children: [
      { name: 'Ноутбуки', slug: 'laptops', icon: 'Laptop' },
      { name: 'Игровые ноутбуки', slug: 'gaming-laptops', icon: 'Gamepad2' },
      { name: 'Мониторы', slug: 'monitors', icon: 'Monitor' },
    ],
  },
  {
    name: 'Комплектующие для ПК', slug: 'pc-parts', icon: 'Cpu',
    children: [
      { name: 'Процессоры', slug: 'cpus', icon: 'Cpu' },
      { name: 'Видеокарты', slug: 'gpus', icon: 'Monitor' },
      { name: 'Материнские платы', slug: 'motherboards', icon: 'Cpu' },
      { name: 'Оперативная память', slug: 'ram', icon: 'HardDrive' },
      { name: 'SSD накопители', slug: 'ssd', icon: 'HardDrive' },
      { name: 'Блоки питания', slug: 'psu', icon: 'Plug' },
      { name: 'Корпуса', slug: 'cases', icon: 'Box' },
      { name: 'Охлаждение', slug: 'cooling', icon: 'Fan' },
    ],
  },
  {
    name: 'ТВ и аудио', slug: 'tv-audio', icon: 'Tv',
    children: [
      { name: 'Телевизоры', slug: 'tvs', icon: 'Tv' },
      { name: 'Аудиотехника', slug: 'audio', icon: 'Speaker' },
      { name: 'Умные колонки', slug: 'smart-speakers', icon: 'Speaker' },
    ],
  },
  {
    name: 'Фототехника', slug: 'photo', icon: 'Camera',
    children: [
      { name: 'Фотоаппараты и камеры', slug: 'cameras', icon: 'Camera' },
    ],
  },
  {
    name: 'Игры и консоли', slug: 'gaming', icon: 'Gamepad2',
    children: [
      { name: 'Игровые приставки', slug: 'consoles', icon: 'Gamepad2' },
      { name: 'Игровая периферия', slug: 'gaming-peripherals', icon: 'Mouse' },
    ],
  },
  {
    name: 'Периферия', slug: 'peripherals', icon: 'Keyboard',
    children: [
      { name: 'Клавиатуры и мыши', slug: 'keyboards-mice', icon: 'Keyboard' },
      { name: 'Сетевое оборудование', slug: 'networking', icon: 'Wifi' },
    ],
  },
  {
    name: 'Техника для дома', slug: 'home-appliances', icon: 'Home',
    children: [
      { name: 'Пылесосы', slug: 'vacuum-cleaners', icon: 'Sparkles' },
      { name: 'Стиральные машины', slug: 'washing-machines', icon: 'Sparkles' },
      { name: 'Холодильники', slug: 'refrigerators', icon: 'Home' },
      { name: 'Кондиционеры', slug: 'air-conditioners', icon: 'Wind' },
      { name: 'Обогреватели', slug: 'heaters', icon: 'Flame' },
      { name: 'Увлажнители воздуха', slug: 'humidifiers', icon: 'Droplets' },
      { name: 'Утюги и отпариватели', slug: 'irons', icon: 'Sparkles' },
    ],
  },
  {
    name: 'Техника для кухни', slug: 'kitchen', icon: 'CookingPot',
    children: [
      { name: 'Кофемашины', slug: 'coffee-machines', icon: 'Coffee' },
      { name: 'Посудомоечные машины', slug: 'dishwashers', icon: 'Droplets' },
      { name: 'Микроволновые печи', slug: 'microwaves', icon: 'CookingPot' },
      { name: 'Мультиварки', slug: 'multicookers', icon: 'CookingPot' },
      { name: 'Электрочайники', slug: 'kettles', icon: 'CookingPot' },
      { name: 'Блендеры и миксеры', slug: 'blenders', icon: 'CookingPot' },
    ],
  },
  {
    name: 'Красота и здоровье', slug: 'beauty-health', icon: 'Heart',
    children: [
      { name: 'Фены и стайлеры', slug: 'hair-styling', icon: 'Wind' },
      { name: 'Бритвы и эпиляторы', slug: 'shavers', icon: 'Scissors' },
      { name: 'Электрические зубные щётки', slug: 'toothbrushes', icon: 'Smile' },
    ],
  },
  {
    name: 'Умный дом', slug: 'smart-home', icon: 'Lightbulb',
    children: [
      { name: 'Камеры и безопасность', slug: 'security-cameras', icon: 'Shield' },
      { name: 'Умное освещение', slug: 'smart-lighting', icon: 'Lightbulb' },
    ],
  },
]

function getIcon(name?: string) {
  if (!name) return Smartphone
  return ICON_MAP[name] || Smartphone
}

// ──────────────────────────────────────────────────────────────────
// Navigation steps:
// 1. "root"    → show category groups (Смартфоны, Ноутбуки, ...)
// 2. "group"   → show subcategories (Наушники, Планшеты, ...)
// 3. "brands"  → show brands in subcategory (Apple, Sony, JBL, ...)
// 4. "models"  → show product models for selected brand
// ──────────────────────────────────────────────────────────────────

type Step = 'root' | 'group' | 'brands' | 'models'

export default function CatalogPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('root')
  const [selectedGroup, setSelectedGroup] = useState<CatalogGroup | null>(null)
  const [selectedChild, setSelectedChild] = useState<CatalogChild | null>(null)
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null)

  const [brands, setBrands] = useState<BrandInfo[]>([])
  const [products, setProducts] = useState<CatalogProduct[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Breadcrumb path
  const breadcrumb: { label: string; onClick: () => void }[] = [
    { label: 'Каталог', onClick: () => goToRoot() },
  ]
  if (selectedGroup) {
    breadcrumb.push({
      label: selectedGroup.name,
      onClick: () => goToGroup(selectedGroup),
    })
  }
  if (selectedChild) {
    breadcrumb.push({
      label: selectedChild.name,
      onClick: () => goToBrands(selectedChild),
    })
  }
  if (selectedBrand) {
    breadcrumb.push({
      label: selectedBrand,
      onClick: () => {},
    })
  }

  const goToRoot = () => {
    setStep('root')
    setSelectedGroup(null)
    setSelectedChild(null)
    setSelectedBrand(null)
    setBrands([])
    setProducts([])
    setError(null)
  }

  const goToGroup = (group: CatalogGroup) => {
    setStep('group')
    setSelectedGroup(group)
    setSelectedChild(null)
    setSelectedBrand(null)
    setBrands([])
    setProducts([])
    setError(null)
  }

  const goToBrands = useCallback(async (child: CatalogChild) => {
    setStep('brands')
    setSelectedChild(child)
    setSelectedBrand(null)
    setProducts([])
    setError(null)
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/api/v1/catalog/browse/${child.slug}`)
      if (!res.ok) throw new Error('Failed to load')
      const data = await res.json()
      setBrands(data.brands || [])
      setProducts(data.products || [])
    } catch {
      setError('Не удалось загрузить данные. Попробуйте позже.')
    } finally {
      setLoading(false)
    }
  }, [])

  const goToModels = useCallback(async (brand: string, childSlug: string) => {
    setStep('models')
    setSelectedBrand(brand)
    setLoading(true)
    setError(null)

    try {
      const res = await fetch(
        `${API_URL}/api/v1/catalog/browse/${childSlug}?brand=${encodeURIComponent(brand)}`
      )
      if (!res.ok) throw new Error('Failed to load')
      const data = await res.json()
      setProducts(data.products || [])
    } catch {
      setError('Не удалось загрузить модели.')
    } finally {
      setLoading(false)
    }
  }, [])

  const searchModel = (title: string) => {
    router.push(`/?q=${encodeURIComponent(title)}`)
  }

  return (
    <div className="container py-8 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        {breadcrumb.map((item, i) => (
          <span key={i} className="flex items-center gap-2">
            {i > 0 && <ChevronRight className="w-3 h-3 text-[var(--td)]" />}
            <button
              onClick={item.onClick}
              className={`text-sm font-medium transition-colors ${
                i === breadcrumb.length - 1
                  ? 'text-[var(--t)] cursor-default'
                  : 'text-[var(--ac2)] hover:text-[var(--ac)]'
              }`}
            >
              {item.label}
            </button>
          </span>
        ))}
      </div>

      {/* Header */}
      <div className="mb-6">
        {step !== 'root' && (
          <button
            onClick={() => {
              if (step === 'models' && selectedChild) goToBrands(selectedChild)
              else if (step === 'brands' && selectedGroup) goToGroup(selectedGroup)
              else goToRoot()
            }}
            className="flex items-center gap-2 text-sm text-[var(--ac2)] hover:text-[var(--ac)] mb-3 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Назад
          </button>
        )}
        <h1 className="text-2xl font-bold text-[var(--t)] mb-1">
          {step === 'root' && 'Каталог товаров'}
          {step === 'group' && selectedGroup?.name}
          {step === 'brands' && selectedChild?.name}
          {step === 'models' && `${selectedChild?.name} — ${selectedBrand}`}
        </h1>
        <p className="text-sm text-[var(--td)]">
          {step === 'root' && 'Выберите категорию'}
          {step === 'group' && 'Выберите подкатегорию'}
          {step === 'brands' && 'Выберите бренд'}
          {step === 'models' && 'Выберите модель для сравнения цен'}
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-[var(--ac2)] animate-spin" />
            <p className="text-sm text-[var(--td)]">
              Загружаем каталог...
            </p>
          </div>
        </div>
      )}

      {/* Step 1: Root — Category Groups */}
      {step === 'root' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {CATALOG.map((group) => {
            const Icon = getIcon(group.icon)
            return (
              <button
                key={group.slug}
                onClick={() => goToGroup(group)}
                className="flex items-center gap-3 p-4 rounded-xl border border-[var(--bd)] bg-[var(--c1)] hover:border-[var(--ac)]/30 hover:bg-[var(--c2)] transition-all text-left"
              >
                <div className="w-10 h-10 rounded-lg bg-[var(--ac-glow)] flex items-center justify-center flex-shrink-0">
                  <Icon className="w-5 h-5 text-[var(--ac2)]" />
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-sm font-semibold text-[var(--t)] truncate">
                    {group.name}
                  </h2>
                  <span className="text-xs text-[var(--td)]">
                    {group.children.length} подкатегорий
                  </span>
                </div>
                <ChevronRight className="w-4 h-4 text-[var(--td)]" />
              </button>
            )
          })}
        </div>
      )}

      {/* Step 2: Group — Subcategories */}
      {step === 'group' && selectedGroup && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {selectedGroup.children.map((child) => {
            const ChildIcon = getIcon(child.icon)
            return (
              <button
                key={child.slug}
                onClick={() => goToBrands(child)}
                className="flex items-center gap-3 p-4 rounded-xl border border-[var(--bd)] bg-[var(--c1)] hover:border-[var(--ac)]/30 hover:bg-[var(--c2)] transition-all text-left"
              >
                <div className="w-9 h-9 rounded-lg bg-[var(--c2)] flex items-center justify-center flex-shrink-0">
                  <ChildIcon className="w-4 h-4 text-[var(--ac2)]" />
                </div>
                <span className="text-sm font-medium text-[var(--t)] truncate flex-1">
                  {child.name}
                </span>
                <ChevronRight className="w-4 h-4 text-[var(--td)]" />
              </button>
            )
          })}
        </div>
      )}

      {/* Step 3: Brands */}
      {step === 'brands' && !loading && (
        <div>
          {brands.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {brands.map((brand) => (
                <button
                  key={brand.name}
                  onClick={() => selectedChild && goToModels(brand.name, selectedChild.slug)}
                  className="flex items-center gap-3 p-4 rounded-xl border border-[var(--bd)] bg-[var(--c1)] hover:border-[var(--ac)]/30 hover:bg-[var(--c2)] transition-all text-left"
                >
                  <Tag className="w-4 h-4 text-[var(--ac2)] flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-semibold text-[var(--t)] block truncate">
                      {brand.name}
                    </span>
                    <span className="text-xs text-[var(--td)]">
                      {brand.count} {brand.count === 1 ? 'товар' : brand.count < 5 ? 'товара' : 'товаров'}
                    </span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-[var(--td)]" />
                </button>
              ))}
            </div>
          ) : !error && (
            <p className="text-sm text-[var(--td)] text-center py-12">
              Товары не найдены в этой категории
            </p>
          )}
        </div>
      )}

      {/* Step 4: Models — Product list */}
      {step === 'models' && !loading && (
        <div>
          {products.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {products.map((product, i) => (
                <button
                  key={i}
                  onClick={() => searchModel(product.title)}
                  className="flex items-center gap-3 p-4 rounded-xl border border-[var(--bd)] bg-[var(--c1)] hover:border-[var(--ac)]/30 hover:bg-[var(--c2)] transition-all text-left group"
                >
                  <div className="w-10 h-10 rounded-lg bg-[var(--c2)] flex-shrink-0 flex items-center justify-center group-hover:bg-[var(--ac-glow)] transition-colors">
                    <Package className="w-5 h-5 text-[var(--td)] group-hover:text-[var(--ac2)] transition-colors" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-[var(--t)] truncate">
                      {product.title}
                    </h3>
                    <p className="text-xs text-[var(--td)] mt-0.5">
                      Нажмите для сравнения цен
                    </p>
                  </div>
                  <Search className="w-4 h-4 text-[var(--td)] group-hover:text-[var(--ac2)] flex-shrink-0 transition-colors" />
                </button>
              ))}
            </div>
          ) : !error && (
            <p className="text-sm text-[var(--td)] text-center py-12">
              Товары этого бренда не найдены
            </p>
          )}
        </div>
      )}
    </div>
  )
}
