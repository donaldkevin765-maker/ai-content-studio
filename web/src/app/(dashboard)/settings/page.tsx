'use client'

import { useState } from 'react'
import { Key, Save, CheckCircle2, XCircle, RefreshCw, Film } from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { verifyToken, projects } from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

export default function SettingsPage() {
  const { token, apiUrl, setApiUrl, logout, login } = useAuth()
  const [newToken, setNewToken] = useState(token || '')
  const [newUrl, setNewUrl] = useState(apiUrl)
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState<'idle' | 'saved' | 'error'>('idle')
  const [statusMsg, setStatusMsg] = useState('')

  const handleSave = async () => {
    setSaving(true)
    setStatus('idle')

    if (newUrl !== apiUrl) {
      setApiUrl(newUrl)
    }

    if (newToken !== token) {
      login(newToken)
    }

    try {
      const valid = await verifyToken()
      if (valid) {
        setStatus('saved')
        setStatusMsg('Connessione al backend riuscita')
      } else {
        setStatus('error')
        setStatusMsg('Token non valido per il backend')
      }
    } catch (err: any) {
      setStatus('error')
      setStatusMsg(`Errore connessione: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async () => {
    setSaving(true)
    setStatus('idle')
    try {
      const data = await projects.list(1, 1)
      setStatus('saved')
      setStatusMsg(`Connessione OK · ${data.total} progetti trovati`)
    } catch (err: any) {
      setStatus('error')
      setStatusMsg(`Errore: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Impostazioni</h1>
        <p className="text-sm text-gray-500 mt-1">Configura la connessione al backend</p>
      </div>

      {/* Connection */}
      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold text-white">Connessione Backend</h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">URL Backend</label>
            <input
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              className="glass-input font-mono text-sm"
              placeholder="https://sistema-video-ai.vercel.app"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">Token API</label>
            <div className="relative">
              <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
              <input
                type="password"
                value={newToken}
                onChange={(e) => setNewToken(e.target.value)}
                className="glass-input pl-10 font-mono text-sm"
                placeholder="Bearer token..."
              />
            </div>
          </div>

          {status === 'saved' && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
              <CheckCircle2 className="h-4 w-4" /> {statusMsg}
            </div>
          )}
          {status === 'error' && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              <XCircle className="h-4 w-4" /> {statusMsg}
            </div>
          )}

          <div className="flex gap-3">
            <Button onClick={handleSave} loading={saving} disabled={saving}>
              <Save className="h-4 w-4" /> Salva
            </Button>
            <Button variant="secondary" onClick={testConnection} disabled={saving}>
              <RefreshCw className="h-4 w-4" /> Test Connessione
            </Button>
            <Button variant="ghost" onClick={logout} className="ml-auto text-red-400 hover:text-red-300">
              Disconnetti
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Info */}
      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold text-white">Informazioni</h3>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center gap-3">
            <Film className="h-4 w-4 text-brand-400" />
            <span className="text-gray-400">AI Content Studio v0.1.0</span>
          </div>
          <p className="text-gray-600 text-xs">
            Backend: Sistema Video AI Automatico — 100% gratuito/open-source.
            API disponibili su <a href="https://sistema-video-ai.vercel.app/docs" target="_blank" className="text-brand-400 hover:underline">Swagger Docs</a>.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
