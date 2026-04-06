import Link from 'next/link'

export function Footer() {
  return (
    <footer className="border-t border-[var(--bd)] py-6 mt-auto">
      <div className="container flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-[var(--tm)] text-xs">
          Smart Price &copy; {new Date().getFullYear()} — Дипломный проект
        </p>
        <div className="flex gap-5 text-xs">
          <Link href="/about" className="text-[var(--td)] hover:text-[var(--t)] transition-colors">О сервисе</Link>
          <Link href="/docs" className="text-[var(--td)] hover:text-[var(--t)] transition-colors">Docs</Link>
        </div>
      </div>
    </footer>
  )
}
