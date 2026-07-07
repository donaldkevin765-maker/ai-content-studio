'use client'

import { useState, useEffect } from 'react'
import { Plus, Film, Loader2, MoreHorizontal, Calendar, ChevronRight } from 'lucide-react'
import { projects, type Project } from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import Link from 'next/link'

export default function Dashboard() {
  const [projectList, setProjectList] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNewProject, setShowNewProject] = useState(false)
  const [newTitle, setNewTitle] = useState('')

  const loadProjects = async () => {
    try {
      setLoading(true)
      const data = await projects.list()
      setProjectList(data.items || [])
    } catch (err: any) {
      setError(err.message || 'Errore caricamento progetti')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadProjects() }, [])

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

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Progetti</h1>
          <p className="text-sm text-gray-500 mt-1">
            {projectList.length} progetti
          </p>
        </div>
        <Button onClick={() => setShowNewProject(true)}>
          <Plus className="h-4 w-4" />
          Nuovo Progetto
        </Button>
      </div>

      {/* New project form */}
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

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
          <button onClick={loadProjects} className="ml-2 underline">Riprova</button>
        </div>
      )}

      {/* Projects list */}
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
    </div>
  )
}
