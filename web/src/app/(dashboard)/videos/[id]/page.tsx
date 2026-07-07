'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  ArrowLeft, Loader2, Play, Square, Sparkles,
  FileText, Image, Clock, CheckCircle2, XCircle,
  AlertCircle, Download, Globe, ChevronRight, Hammer,
} from 'lucide-react'
import { videos, type VideoDetail, type Scene } from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

export default function VideoDetail() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [video, setVideo] = useState<VideoDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [generating, setGenerating] = useState(false)
  const [rendering, setRendering] = useState(false)
  const [compiling, setCompiling] = useState(false)
  const [topic, setTopic] = useState('')
  const [style, setStyle] = useState('informativo')
  const [duration, setDuration] = useState(60)
  const [sceneCount, setSceneCount] = useState(3)
  const [progressInterval, setProgressInterval] = useState<NodeJS.Timeout | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const data = await videos.get(parseInt(id))
      setVideo(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  // Polling progress during render/compile
  const startProgressPolling = useCallback(() => {
    const interval = setInterval(async () => {
      try {
        // Prima prova l'endpoint progress (funziona per render via progress_tracker)
        const progress = await videos.progress(parseInt(id))
        setVideo(prev => prev ? { ...prev, ...progress, progress_percent: progress.percent } : prev)
        if (progress.status === 'completed' || progress.status === 'error') {
          clearInterval(interval)
          load()
        }
      } catch {
        // Se l'endpoint progress non è disponibile (compile), carica i dati direttamente dal DB
        try {
          const data = await videos.get(parseInt(id))
          setVideo(data)
          if (data.status === 'completed' || data.status === 'error') {
            clearInterval(interval)
          }
        } catch {
          // ignora errori di polling
        }
      }
    }, 3000)
    setProgressInterval(interval)
  }, [id, load])

  useEffect(() => {
    return () => {
      if (progressInterval) clearInterval(progressInterval)
    }
  }, [progressInterval])

  const generateScript = async () => {
    if (!topic.trim()) return
    try {
      setGenerating(true)
      const result = await videos.generateScript(parseInt(id), {
        topic: topic.trim(),
        duration_seconds: duration,
        style,
        scene_count: sceneCount,
      })
      setVideo(prev => prev ? { ...prev, script: result.script, scenes: result.scenes as Scene[] } : prev)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  const startRender = async () => {
    try {
      setRendering(true)
      await videos.render(parseInt(id))
      startProgressPolling()
    } catch (err: any) {
      setError(err.message)
      setRendering(false)
    }
  }

  const startCompile = async () => {
    try {
      setCompiling(true)
      await videos.compile(parseInt(id))
      startProgressPolling()
    } catch (err: any) {
      setError(err.message)
      setCompiling(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-400" />
      </div>
    )
  }

  if (!video) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" /> Indietro
        </Button>
        <Card><CardContent className="py-8 text-center text-gray-500">Video non trovato</CardContent></Card>
      </div>
    )
  }

  const isProcessing = video.status === 'rendering' || video.status === 'processing' || video.status === 'compiling'

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push(`/projects/${video.project_id}`)} className="h-9 w-9 p-0">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white">{video.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={cn(
                'text-xs font-medium px-2.5 py-0.5 rounded-full',
                video.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                isProcessing ? 'bg-brand-500/10 text-brand-400' :
                video.status === 'error' ? 'bg-red-500/10 text-red-400' :
                'bg-gray-500/10 text-gray-400'
              )}>
                {video.status === 'completed' ? 'Completato' :
                 isProcessing ? `In elaborazione (${Math.round(video.progress_percent)}%)` :
                 video.status === 'error' ? 'Errore' :
                 video.status === 'draft' ? 'Bozza' : video.status}
              </span>
              {video.duration > 0 && (
                <span className="text-xs text-gray-600 font-mono">{Math.round(video.duration)}s</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
          <button onClick={() => setError('')} className="ml-2 underline">Chiudi</button>
        </div>
      )}

      {/* Progress bar for rendering */}
      {isProcessing && (
        <Card>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">{video.progress_step || 'Elaborazione...'}</span>
              <span className="text-brand-400 font-mono">{Math.round(video.progress_percent)}%</span>
            </div>
            <div className="h-2 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-brand-500 transition-all duration-500"
                style={{ width: `${video.progress_percent}%` }}
              />
            </div>
            <Button variant="ghost" size="sm" onClick={load} className="text-xs">
              Aggiorna
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Script Generation */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-brand-400" />
            <h3 className="text-sm font-semibold text-white">Genera Script AI</h3>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3 items-start">
            <div className="flex-1 space-y-3">
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Argomento del video..."
                className="glass-input"
                disabled={generating}
              />
              <div className="flex gap-3">
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="glass-input flex-1"
                  disabled={generating}
                >
                  <option value="informativo">Informativo</option>
                  <option value="divertente">Divertente</option>
                  <option value="serio">Serio</option>
                  <option value="motivazionale">Motivazionale</option>
                  <option value="didattico">Didattico</option>
                </select>
                <select
                  value={sceneCount}
                  onChange={(e) => setSceneCount(parseInt(e.target.value))}
                  className="glass-input w-24"
                  disabled={generating}
                >
                  <option value={1}>1 scena</option>
                  <option value={2}>2 scene</option>
                  <option value={3}>3 scene</option>
                  <option value={4}>4 scene</option>
                  <option value={5}>5 scene</option>
                  <option value={6}>6 scene</option>
                </select>
                <select
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  className="glass-input w-28"
                  disabled={generating}
                >
                  <option value={30}>30s</option>
                  <option value={60}>60s</option>
                  <option value={120}>2 min</option>
                  <option value={300}>5 min</option>
                  <option value={600}>10 min</option>
                </select>
              </div>
            </div>
            <Button
              onClick={generateScript}
              disabled={!topic.trim() || generating}
              loading={generating}
            >
              {generating ? 'Generazione...' : 'Genera'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Script display */}
      {video.script && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-brand-400" />
              <h3 className="text-sm font-semibold text-white">Script</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-white/10 bg-black/40 p-4 whitespace-pre-wrap text-sm text-gray-300 leading-relaxed font-mono max-h-96 overflow-y-auto">
              {video.script}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scenes */}
      {video.scenes && video.scenes.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Image className="h-4 w-4 text-brand-400" />
              <h3 className="text-sm font-semibold text-white">Scene ({video.scenes.length})</h3>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {video.scenes.map((scene, idx) => (
              <div key={scene.id} className="rounded-lg border border-white/10 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-brand-400">Scena {scene.order || idx + 1}</span>
                  <span className="text-xs text-gray-600 font-mono">{scene.duration}s</span>
                </div>
                <p className="text-sm text-gray-300">{scene.content}</p>
                {scene.image_prompt && (
                  <div className="rounded bg-white/5 px-3 py-2 text-xs text-gray-500">
                    <span className="text-gray-400">Prompt immagine: </span>{scene.image_prompt}
                  </div>
                )}
                {scene.subtitle_text && (
                  <div className="text-xs text-gray-500 italic">
                    "{scene.subtitle_text}"
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button
          onClick={startRender}
          disabled={isProcessing || !video.script}
          loading={rendering}
          size="lg"
        >
          {isProcessing ? (
            <><Loader2 className="h-5 w-5 animate-spin" /> In elaborazione...</>
          ) : (
            <><Play className="h-5 w-5" /> Renderizza Video</>
          )}
        </Button>

        {video.status === 'assets_ready' && (
          <Button
            onClick={startCompile}
            disabled={compiling}
            loading={compiling}
            variant="primary"
            size="lg"
          >
            {compiling ? (
              <><Loader2 className="h-5 w-5 animate-spin" /> Compilazione...</>
            ) : (
              <><Hammer className="h-5 w-5" /> Compila Video Finale</>
            )}
          </Button>
        )}

        {video.output_url && (
          <Button variant="secondary" size="lg" onClick={() => window.open(video.output_url, '_blank')}>
            <Download className="h-5 w-5" /> Scarica
          </Button>
        )}

        <Button variant="secondary" size="lg" onClick={load}>
          Aggiorna
        </Button>
      </div>

      {/* Output */}
      {video.output_url && (
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-white">Video Output</h3>
          </CardHeader>
          <CardContent>
            <video
              src={video.output_url}
              controls
              className="w-full rounded-lg"
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
