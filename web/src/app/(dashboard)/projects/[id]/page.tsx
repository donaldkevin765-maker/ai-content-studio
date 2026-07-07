'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Film, Plus, Loader2, Trash2, Video as VideoIcon, Calendar, MoreHorizontal, ChevronRight } from 'lucide-react'
import { projects, videos, type Project, type Video } from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import Link from 'next/link'
import { cn } from '@/lib/utils'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [project, setProject] = useState<Project | null>(null)
  const [videoList, setVideoList] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNewVideo, setShowNewVideo] = useState(false)
  const [newTitle, setNewTitle] = useState('')

  const load = async () => {
    try {
      setLoading(true)
      const pid = parseInt(id)
      const [p, v] = await Promise.all([
        projects.get(pid),
        videos.list(pid),
      ])
      setProject(p)
      setVideoList(v.items || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const createVideo = async () => {
    if (!newTitle.trim()) return
    try {
      const v = await videos.create({ project_id: parseInt(id), title: newTitle.trim() })
      setVideoList(prev => [v, ...prev])
      setNewTitle('')
      setShowNewVideo(false)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const deleteProject = async () => {
    if (!confirm('Eliminare questo progetto e tutti i suoi video?')) return
    try {
      await projects.delete(parseInt(id))
      router.push('/')
    } catch (err: any) {
      setError(err.message)
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-400" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.push('/')}>
          <ArrowLeft className="h-4 w-4" /> Indietro
        </Button>
        <Card>
          <CardContent className="py-8 text-center text-gray-500">
            Progetto non trovato
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push('/')} className="h-9 w-9 p-0">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white">{project.title}</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {videoList.length} video · {new Date(project.created_at).toLocaleDateString('it')}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setShowNewVideo(true)}>
            <Plus className="h-4 w-4" /> Nuovo Video
          </Button>
          <Button variant="ghost" onClick={deleteProject} className="text-red-400 hover:text-red-300">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* New video form */}
      {showNewVideo && (
        <Card>
          <CardContent className="flex items-center gap-3">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Titolo del video..."
              className="glass-input flex-1"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && createVideo()}
            />
            <Button onClick={createVideo} disabled={!newTitle.trim()}>Crea</Button>
            <Button variant="ghost" onClick={() => { setShowNewVideo(false); setNewTitle('') }}>
              Annulla
            </Button>
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
          <button onClick={load} className="ml-2 underline">Riprova</button>
        </div>
      )}

      {/* Videos list */}
      {videoList.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-600">
          <VideoIcon className="h-12 w-12 mb-4 opacity-50" />
          <p className="text-lg font-medium">Nessun video</p>
          <p className="text-sm mt-1">Crea un video per questo progetto</p>
          <Button onClick={() => setShowNewVideo(true)} className="mt-4">
            <Plus className="h-4 w-4" /> Nuovo Video
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {videoList.map((video) => (
            <Link key={video.id} href={`/videos/${video.id}`}>
              <Card hover>
                <CardContent className="flex items-center gap-4">
                  <div className={cn(
                    'flex h-12 w-20 items-center justify-center rounded-lg',
                    video.status === 'completed' ? 'bg-emerald-500/10' :
                    video.status === 'rendering' || video.status === 'processing' ? 'bg-brand-500/10' :
                    'bg-white/5'
                  )}>
                    <VideoIcon className={cn(
                      'h-6 w-6',
                      video.status === 'completed' ? 'text-emerald-400' :
                      video.status === 'rendering' || video.status === 'processing' ? 'text-brand-400' :
                      'text-gray-500'
                    )} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-white">{video.title}</h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className={cn(
                        'text-[10px] font-medium px-2 py-0.5 rounded-full',
                        video.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                        video.status === 'rendering' || video.status === 'processing' ? 'bg-brand-500/10 text-brand-400' :
                        video.status === 'error' ? 'bg-red-500/10 text-red-400' :
                        'bg-gray-500/10 text-gray-400'
                      )}>
                        {video.status}
                      </span>
                      {video.duration > 0 && (
                        <span className="text-xs text-gray-600 font-mono">
                          {Math.round(video.duration)}s
                        </span>
                      )}
                      {video.progress_percent > 0 && video.status !== 'completed' && (
                        <span className="text-xs text-brand-400 font-mono">
                          {Math.round(video.progress_percent)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-gray-600" />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* Project info */}
      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold text-white">Dettagli Progetto</h3>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Lingua</span>
              <p className="text-white font-medium mt-0.5">{project.language}</p>
            </div>
            <div>
              <span className="text-gray-500">Stato</span>
              <p className="text-white font-medium mt-0.5">{project.status}</p>
            </div>
            <div>
              <span className="text-gray-500">Creato</span>
              <p className="text-white font-medium mt-0.5">
                {new Date(project.created_at).toLocaleString('it')}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Aggiornato</span>
              <p className="text-white font-medium mt-0.5">
                {new Date(project.updated_at).toLocaleString('it')}
              </p>
            </div>
          </div>
          {project.description && (
            <div className="mt-4">
              <span className="text-sm text-gray-500">Descrizione</span>
              <p className="text-sm text-white mt-0.5">{project.description}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
