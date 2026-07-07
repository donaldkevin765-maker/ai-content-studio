'use client'

import { useState, useEffect } from 'react'
import { Youtube, Music2, Camera, Globe, CheckCircle2, XCircle, ExternalLink, LogOut, RefreshCw, Loader2 } from 'lucide-react'
import { social, videos, type SocialAccount, type Video } from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

const platforms = [
  { id: 'youtube', name: 'YouTube', icon: Youtube, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
  { id: 'tiktok', name: 'TikTok', icon: Music2, color: 'text-pink-400', bg: 'bg-pink-500/10', border: 'border-pink-500/20' },
  { id: 'instagram', name: 'Instagram', icon: Camera, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
]

export default function SocialPage() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [connecting, setConnecting] = useState<string | null>(null)
  const [videoList, setVideoList] = useState<Video[]>([])
  const [selectedVideo, setSelectedVideo] = useState<number | null>(null)
  const [publishTitle, setPublishTitle] = useState('')
  const [publishDesc, setPublishDesc] = useState('')
  const [publishing, setPublishing] = useState(false)
  const [publishResult, setPublishResult] = useState<string | null>(null)

  const load = async () => {
    try {
      setLoading(true)
      const [accs, vids] = await Promise.all([
        social.accounts(),
        videos.list(undefined, 1, 50),
      ])
      setAccounts(accs)
      setVideoList(vids.items || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleConnect = async (platform: string) => {
    setConnecting(platform)
    try {
      const { url } = await social.authUrl(platform)
      window.open(url, '_blank')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnect = async (accountId: number) => {
    try {
      await social.disconnect(accountId)
      setAccounts(prev => prev.filter(a => a.id !== accountId))
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleRefresh = async (accountId: number) => {
    try {
      const updated = await social.refresh(accountId)
      setAccounts(prev => prev.map(a => a.id === accountId ? updated : a))
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handlePublish = async () => {
    if (!selectedVideo || !publishTitle.trim()) return
    const accountId = accounts[0]?.id
    if (!accountId) return

    try {
      setPublishing(true)
      setPublishResult(null)
      const result = await social.publish({
        video_id: selectedVideo,
        account_id: accountId,
        title: publishTitle.trim(),
        description: publishDesc.trim(),
      })
      setPublishResult(result.success ? 'Pubblicato con successo!' : `Errore: ${result.error}`)
    } catch (err: any) {
      setPublishResult(`Errore: ${err.message}`)
    } finally {
      setPublishing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-400" />
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Social</h1>
        <p className="text-sm text-gray-500 mt-1">Connetti i tuoi account social per pubblicare video</p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
          <button onClick={() => setError('')} className="ml-2 underline">Chiudi</button>
        </div>
      )}

      {/* Platform Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {platforms.map((platform) => {
          const Icon = platform.icon
          const account = accounts.find(a => a.platform === platform.id)
          const isConnected = account?.connected

          return (
            <Card key={platform.id} className={cn('relative overflow-hidden', platform.border)}>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl', platform.bg)}>
                      <Icon className={cn('h-5 w-5', platform.color)} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white">{platform.name}</h3>
                      <p className="text-xs text-gray-500">{isConnected ? 'Connesso' : 'Non connesso'}</p>
                    </div>
                  </div>
                  {isConnected ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <XCircle className="h-4 w-4 text-gray-600" />}
                </div>

                {isConnected && account ? (
                  <div className="space-y-3">
                    <div className={cn('flex items-center gap-3 rounded-lg border p-3', platform.border, platform.bg)}>
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-sm font-semibold text-white">
                        {account.platform_username?.[0]?.toUpperCase() || '?'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{account.platform_username || 'Utente'}</p>
                        <p className="text-[10px] text-gray-500 font-mono truncate">{account.platform_user_id}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="secondary" size="sm" className="flex-1" onClick={() => handleRefresh(account.id)}>
                        <RefreshCw className="h-3.5 w-3.5" /> Aggiorna
                      </Button>
                      <Button variant="destructive" size="sm" className="flex-1" onClick={() => handleDisconnect(account.id)}>
                        <LogOut className="h-3.5 w-3.5" /> Disconnetti
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button className="w-full" onClick={() => handleConnect(platform.id)} disabled={connecting === platform.id}>
                    {connecting === platform.id ? (
                      <><Loader2 className="h-4 w-4 animate-spin" /> Connessione...</>
                    ) : (
                      <>Connetti {platform.name}</>
                    )}
                  </Button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Publish */}
      {accounts.length > 0 && videoList.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-white">Pubblica Video</h2>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-gray-400">Video</label>
              <select
                className="glass-input"
                value={selectedVideo || ''}
                onChange={(e) => setSelectedVideo(parseInt(e.target.value))}
              >
                <option value="">Seleziona un video...</option>
                {videoList.filter(v => v.output_url).map(v => (
                  <option key={v.id} value={v.id}>{v.title}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-gray-400">Titolo</label>
              <input
                value={publishTitle}
                onChange={(e) => setPublishTitle(e.target.value)}
                className="glass-input"
                placeholder="Titolo del video..."
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-gray-400">Descrizione</label>
              <textarea
                value={publishDesc}
                onChange={(e) => setPublishDesc(e.target.value)}
                className="glass-input h-24 resize-none"
                placeholder="Descrizione del video..."
              />
            </div>

            {publishResult && (
              <div className={cn(
                'rounded-lg border px-4 py-3 text-sm',
                publishResult.startsWith('Pubblicato') ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400' : 'border-red-500/20 bg-red-500/10 text-red-400'
              )}>
                {publishResult}
              </div>
            )}

            <Button
              className="w-full"
              size="lg"
              onClick={handlePublish}
              disabled={!selectedVideo || !publishTitle.trim() || publishing}
              loading={publishing}
            >
              <Globe className="h-5 w-5" />
              {publishing ? 'Pubblicazione...' : 'Pubblica Ora'}
            </Button>
          </CardContent>
        </Card>
      )}

      {accounts.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center text-gray-500">
            Connetti almeno un account social per pubblicare video
          </CardContent>
        </Card>
      )}
    </div>
  )
}
