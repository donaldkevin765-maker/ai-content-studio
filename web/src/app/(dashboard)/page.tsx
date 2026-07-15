'use client'

import { useState, useEffect } from 'react'
import {
  Plus, Film, Loader2, Calendar, ChevronRight,
  Play, CheckCircle2, AlertCircle, Clock, Download,
  ExternalLink, Sparkles,
} from 'lucide-react'
import { projects, videos, type Project, type Video } from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import Link from 'next/link'

export default function Dashboard() {
  const [projectList, setProjectList] = useState<Project[]>([])
  const [videoList, setVideoList] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNewProject, setShowNewProject] = useState(false)
  const [newTitle, setNewTitle] = useState('')

  const loadData = async () => {
    try {
      setLoading(true)
      const [projData, vidData] = await Promise.all([
        projects.list(),
        videos.list(undefined, 1, 100),
      ])
      setProjectList(projData.items || [])
      setVideoList(vidData.items || [])
    } catch (err: any) {
      setError(err.message || 'Errore caricamento dati')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const createProject = async () => {
    if (!newTitle.trim()) return
    try {
      const p = await projects.create({ title: newTitle.trim() })
      setProjectList(prev => [p, ...prev])
      setNewTitle('')
      setShowNewProject(false)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const statusMeta = (status: string) => {
    switch (status) {
      case 'completed':
      case 'ready':
        return { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10', label: 'Completato' }
      case 'rendering':
      case 'processing':
        return { icon: Loader2, color: 'text-blue-400', bg: 'bg-blue-500/10', label: 'In elaborazione', spin: true }
      case 'draft':
      case 'script_ready':
        return { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-500/10', label: 'Bozza' }
      case 'error':
        return { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/10', label: 'Errore' }
      default:
        return { icon: Film, color: 'text-gray-400', bg: 'bg-gray-500/10', label: status }
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
    <div className="space-y-8 animate-fade-in">
      {/* ─── Header ─── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            {videoList.length} video · {projectList.length} progetti
          </p>
        </div>
        <Button onClick={() => setShowNewProject(true)}>
          <Plus className="h-4 w-4" />
          Nuovo Progetto
        </Button>
      </div>

      {/* ─── Error ─── */}
      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
          <button onClick={loadData} className="ml-2 underline">Riprova</button>
        </div>
      )}

      {/* ─── Nuovo progetto form ─── */}
      {showNewProject && (
        <Card>
          <CardContent className="flex items-center gap-3">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Titolo del progetto..."
              className="glass-input flex-1"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && createProject()}
            />
            <Button onClick={createProject} disabled={!newTitle.trim()}>Crea</Button>
            <Button variant="ghost" onClick={() => { setShowNewProject(false); setNewTitle('') }}>
              Annulla
            </Button>
          </CardContent>
        </Card>
      )}

      {/* ─── Video Recenti ─── */}
      {videoList.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand-400" />
              Video Recenti
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videoList.map((video) => {
              const meta = statusMeta(video.status)
              const Icon = meta.icon
              const date = new Date(video.created_at)

              return (
                <Card key={video.id} hover className="group relative overflow-hidden">
                  {/* Thumbnail placeholder */}
                  <Link href={video.output_url ? video.output_url : `/videos/${video.id}`} target={video.output_url ? '_blank' : undefined}>
                    <div className={cn(
                      'relative flex h-40 items-center justify-center overflow-hidden',
                      meta.bg,
                    )}>
                      {/* Pattern background */}
                      <div className="absolute inset-0 opacity-20">
                        <div className="absolute inset-0" style={{
                          backgroundImage: 'radial-gradient(circle at 25% 25%, rgba(255,255,255,0.05) 1px, transparent 1px)',
                          backgroundSize: '20px 20px',
                        }} />
                      </div>

                      {/* Status icon */}
                      <Icon className={cn(
                        'h-12 w-12 transition-transform duration-300 group-hover:scale-110',
                        meta.color,
                        meta.spin && 'animate-spin',
                      )} />

                      {/* Play overlay on hover (completed only) */}
                      {video.status === 'completed' && video.output_url && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-500/90 shadow-lg shadow-brand-500/30">
                            <Play className="h-6 w-6 text-white ml-0.5" />
                          </div>
                        </div>
                      )}

                      {/* Status badge */}
                      <div className="absolute top-3 left-3">
                        <Badge variant="outline" className={cn('text-[10px] px-2 py-0.5', meta.bg, meta.color, 'border-current/20')}>
                          {meta.spin && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                          {meta.label}
                        </Badge>
                      </div>

                      {/* Duration */}
                      {video.duration > 0 && (
                        <div className="absolute bottom-3 right-3">
                          <span className="flex items-center gap-1 rounded-md bg-black/60 px-2 py-0.5 text-[10px] text-gray-300">
                            <Clock className="h-3 w-3" />
                            {video.duration >= 60
                              ? `${Math.floor(video.duration / 60)}:${(video.duration % 60).toString().padStart(2, '0')}`
                              : `${video.duration}s`}
                          </span>
                        </div>
                      )}
                    </div>
                  </Link>

                  {/* Info */}
                  <CardContent className="space-y-2">
                    <Link href={`/videos/${video.id}`}>
                      <h3 className="text-sm font-semibold text-white truncate hover:text-brand-400 transition-colors">
                        {video.title}
                      </h3>
                    </Link>

                    {/* Progress bar for in-progress */}
                    {(video.status === 'rendering' || video.status === 'processing') && (
                      <div className="space-y-1">
                        <Progress value={video.progress_percent || 0} className="h-1" />
                        <p className="text-[10px] text-gray-500">{video.progress_percent || 0}% · {video.progress_step || 'In elaborazione'}</p>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[10px] text-gray-600 flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {date.toLocaleDateString('it')}
                      </span>

                      <div className="flex items-center gap-1">
                        {/* Play / View button */}
                        {video.status === 'completed' && video.output_url ? (
                          <>
                            <Link
                              href={video.output_url}
                              target="_blank"
                              className="flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-brand-500/10 hover:text-brand-400 transition-colors"
                              title="Guarda video"
                            >
                              <Play className="h-3.5 w-3.5" />
                            </Link>
                            <Link
                              href={video.output_url}
                              download
                              className="flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-brand-500/10 hover:text-brand-400 transition-colors"
                              title="Scarica video"
                            >
                              <Download className="h-3.5 w-3.5" />
                            </Link>
                          </>
                        ) : (
                          <Link
                            href={`/videos/${video.id}`}
                            className="flex h-7 items-center gap-1 rounded-md px-2 text-[10px] text-gray-500 hover:text-brand-400 hover:bg-brand-500/10 transition-colors"
                          >
                            Dettagli <ChevronRight className="h-3 w-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </section>
      )}

      {/* ─── Progetti ─── */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Film className="h-4 w-4 text-brand-400" />
            Progetti
            <span className="text-xs font-normal text-gray-600">({projectList.length})</span>
          </h2>
        </div>

        {projectList.length === 0 && !error ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-600">
            <Film className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-lg font-medium">Nessun progetto</p>
            <p className="text-sm mt-1">Crea il tuo primo progetto per iniziare</p>
            <Button onClick={() => setShowNewProject(true)} className="mt-4">
              <Plus className="h-4 w-4" /> Nuovo Progetto
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projectList.map((project) => {
              const date = new Date(project.created_at)
              return (
                <Link key={project.id} href={`/projects/${project.id}`}>
                  <Card hover className="h-full">
                    <CardContent className="space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-500/10">
                          <Film className="h-5 w-5 text-brand-400" />
                        </div>
                        <span className={cn(
                          'text-[10px] font-medium px-2 py-0.5 rounded-full',
                          project.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' :
                          project.status === 'completed' ? 'bg-brand-500/10 text-brand-400' :
                          'bg-gray-500/10 text-gray-400'
                        )}>
                          {project.status}
                        </span>
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-white">{project.title}</h3>
                        {project.description && (
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2">{project.description}</p>
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-600">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {date.toLocaleDateString('it')}
                        </span>
                        <span className="text-brand-400 flex items-center gap-1">
                          Apri <ChevronRight className="h-3 w-3" />
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
