import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Сравнение товаров',
}

export default function CompareLayout({ children }: { children: React.ReactNode }) {
  return children
}
