'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Film,
  Menu,
  Home,
  Share2,
  Settings,
  LogOut,
  Bot,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth'
import { BackendStatus } from './BackendStatus'
import { Sheet, SheetContent, SheetClose, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'

const navigation = [
  { name: 'Progetti', href: '/', icon: Home },
  { name: 'Assistente AI', href: '/chat', icon: Bot },
  { name: 'Social', href: '/social', icon: Share2 },
  { name: 'Impostazioni', href: '/settings', icon: Settings },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const pathname = usePathname()
  const { logout } = useAuth()

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/' || pathname.startsWith('/projects') || pathname.startsWith('/videos')
    return pathname.startsWith(href)
  }

  const navLinks = (close?: () => void) => navigation.map((item) => {
    const active = isActive(item.href)
    return (
      <Link
        key={item.name}
        href={item.href}
        onClick={close}
        className={cn(
          'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 group',
          active
            ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
            : 'text-gray-400 hover:bg-white/5 hover:text-white'
        )}
      >
        <item.icon className={cn('h-5 w-5 shrink-0', active && 'text-brand-400')} />
        <span>{item.name}</span>
      </Link>
    )
  })

  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0a0c]">
      {/* ─── Desktop sidebar ─── */}
      <aside
        className={cn(
          'hidden lg:flex flex-col border-r border-white/10 bg-[#121216] transition-all duration-300 ease-in-out',
          sidebarOpen ? 'w-64' : 'w-16'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-white/10">
          <Link href="/" className={cn('flex items-center gap-3', !sidebarOpen && 'justify-center w-full')}>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-500 shadow-glow-sm">
              <Film className="h-5 w-5 text-white" />
            </div>
            {sidebarOpen && (
              <div>
                <h1 className="text-sm font-semibold text-white">AI Studio</h1>
                <p className="text-[10px] text-gray-500">Content Creator</p>
              </div>
            )}
          </Link>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-colors"
            aria-label={sidebarOpen ? 'Collassa sidebar' : 'Espandi sidebar'}
          >
            <Menu className="h-4 w-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navLinks()}
        </nav>

        {/* User area */}
        <div className="p-3 border-t border-white/10">
          {sidebarOpen ? (
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-500/20 text-brand-400 text-xs font-semibold">
                  U
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">Utente</p>
                  <p className="text-xs text-gray-500 truncate">Connesso</p>
                </div>
              </div>
              <button
                onClick={logout}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-gray-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
              >
                <LogOut className="h-3.5 w-3.5" />
                Disconnetti
              </button>
            </div>
          ) : (
            <div className="flex justify-center">
              <button
                onClick={logout}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                title="Disconnetti"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Backend status */}
        <BackendStatus sidebarOpen={sidebarOpen} />
      </aside>

      {/* ─── Mobile top bar ─── */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 flex h-14 items-center gap-3 border-b border-white/10 bg-[#121216] px-4">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger
            className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-colors"
            aria-label="Apri menu"
          >
            <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-72 bg-[#121216] border-r border-white/10 p-0">
            <SheetHeader className="flex h-14 flex-row items-center gap-3 border-b border-white/10 px-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 shadow-glow-sm">
                <Film className="h-4 w-4 text-white" />
              </div>
              <SheetTitle className="text-sm font-semibold text-white">AI Studio</SheetTitle>
              <SheetClose
                className="ml-auto flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </SheetClose>
            </SheetHeader>
            <nav className="flex-1 overflow-y-auto p-3 space-y-1">
              {navLinks(() => setMobileOpen(false))}
            </nav>
            <div className="p-3 border-t border-white/10 mt-auto">
              <button
                onClick={() => { logout(); setMobileOpen(false) }}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
              >
                <LogOut className="h-3.5 w-3.5" />
                Disconnetti
              </button>
            </div>
          </SheetContent>
        </Sheet>

        <Link href="/" className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">AI Studio</span>
        </Link>
      </div>

      {/* ─── Main content ─── */}
      <main className="flex-1 overflow-y-auto pt-14 lg:pt-0">
        <div className="mx-auto max-w-7xl p-4 sm:p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
