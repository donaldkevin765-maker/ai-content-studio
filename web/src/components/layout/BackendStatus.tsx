'use client'

import { useEffect, useState, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Activity, Server, RefreshCw, CheckCircle, XCircle } from 'lucide-react'

type BackendInfo = {
  currentUrl: string
  status: 'healthy' | 'unhealthy' | 'checking'
  version?: string
}

const PRESETS = [
  { label: 'Vercel (default)', url: 'https://backend-azure-kappa-69.vercel.app' },
  { label: 'Locale (dev)', url: 'http://localhost:8000' },
]

let oracleUrl = ''
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('oracle_backend_url')
  oracleUrl = stored || ''
}

export function BackendStatus({ sidebarOpen }: { sidebarOpen: boolean }) {
  const [backend, setBackend] = useState<BackendInfo>({ currentUrl: '', status: 'checking' })
  const [showMenu, setShowMenu] = useState(false)
  const [customUrl, setCustomUrl] = useState(oracleUrl)

  const checkHealth = useCallback(async (url: string) => {
    if (!url) return { status: 'unhealthy' as const }
    try {
      const res = await fetch(`${url}/health`, { signal: AbortSignal.timeout(5000) })
      if (!res.ok) return { status: 'unhealthy' as const }
      const data = await res.json()
      return { status: 'healthy' as const, version: data.version || data.app || '' }
    } catch {
      return { status: 'unhealthy' as const }
    }
  }, [])

  const updateBackend = useCallback(async () => {
    const url =
      typeof window !== 'undefined'
        ? localStorage.getItem('api_url') || PRESETS[0].url
        : PRESETS[0].url
    setBackend(prev => ({ ...prev, currentUrl: url, status: 'checking' }))
    const result = await checkHealth(url)
    setBackend(prev => ({ ...prev, currentUrl: url, ...result }))
  }, [checkHealth])

  useEffect(() => {
    updateBackend()
    const interval = setInterval(updateBackend, 30000)
    return () => clearInterval(interval)
  }, [updateBackend])

  const switchBackend = (url: string) => {
    localStorage.setItem('api_url', url)
    setShowMenu(false)
    updateBackend()
    window.location.reload()
  }

  const handleCustomUrl = () => {
    const url = customUrl.trim()
    if (url) {
      localStorage.setItem('oracle_backend_url', url)
      switchBackend(url)
    }
  }

  return (
    <div className="relative border-t border-white/10">
      {sidebarOpen ? (
        <div className="p-3">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs text-gray-500 hover:bg-white/5 hover:text-white transition-colors"
          >
            <Server className="h-3.5 w-3.5 shrink-0" />
            <span className="flex-1 text-left truncate">
              {backend.currentUrl.replace('https://', '').replace('http://', '').replace('.vercel.app', '') || 'Backend'}
            </span>
            {backend.status === 'healthy' && <CheckCircle className="h-3 w-3 text-green-400 shrink-0" />}
            {backend.status === 'unhealthy' && <XCircle className="h-3 w-3 text-red-400 shrink-0" />}
            {backend.status === 'checking' && <RefreshCw className="h-3 w-3 text-gray-500 animate-spin shrink-0" />}
          </button>

          {showMenu && (
            <div className="mt-1 rounded-lg border border-white/10 bg-[#1a1a20] p-2 space-y-1">
              {PRESETS.map(p => (
                <button
                  key={p.url}
                  onClick={() => switchBackend(p.url)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs transition-colors',
                    backend.currentUrl === p.url
                      ? 'bg-brand-500/10 text-brand-400'
                      : 'text-gray-400 hover:bg-white/5 hover:text-white'
                  )}
                >
                  <Activity className="h-3 w-3 shrink-0" />
                  <span className="truncate">{p.label}</span>
                </button>
              ))}
              <div className="flex gap-1 pt-1 border-t border-white/10">
                <input
                  type="text"
                  value={customUrl}
                  onChange={e => setCustomUrl(e.target.value)}
                  placeholder="https://oracle-ip:8000"
                  className="flex-1 rounded-md border border-white/10 bg-black/50 px-2 py-1 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-brand-500/50"
                  onKeyDown={e => e.key === 'Enter' && handleCustomUrl()}
                />
                <button
                  onClick={handleCustomUrl}
                  disabled={!customUrl.trim()}
                  className="rounded-md bg-brand-500/20 px-2 py-1 text-xs text-brand-400 hover:bg-brand-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Vai
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex justify-center p-3">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-500 hover:bg-white/5 hover:text-white transition-colors"
            title={`Backend: ${backend.currentUrl}`}
          >
            {backend.status === 'healthy' && <CheckCircle className="h-4 w-4 text-green-400" />}
            {backend.status === 'unhealthy' && <XCircle className="h-4 w-4 text-red-400" />}
            {backend.status === 'checking' && <RefreshCw className="h-4 w-4 text-gray-500 animate-spin" />}
          </button>

          {showMenu && (
            <div className="absolute left-16 bottom-16 w-64 rounded-lg border border-white/10 bg-[#1a1a20] p-2 space-y-1 shadow-xl z-50">
              {PRESETS.map(p => (
                <button
                  key={p.url}
                  onClick={() => switchBackend(p.url)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs transition-colors',
                    backend.currentUrl === p.url
                      ? 'bg-brand-500/10 text-brand-400'
                      : 'text-gray-400 hover:bg-white/5 hover:text-white'
                  )}
                >
                  <Activity className="h-3 w-3 shrink-0" />
                  <span className="truncate">{p.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
