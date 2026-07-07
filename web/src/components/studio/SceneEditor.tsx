'use client'

import { useState, useRef } from 'react'
import { GripVertical, Plus, Trash2, Copy, ChevronUp, ChevronDown, Film, Camera, Monitor, Type, Image as ImageIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'

interface Scene {
  id: string
  name: string
  duration: number
  type: 'webcam' | 'screen' | 'text' | 'image' | 'mixed'
  thumbnail?: string
}

const initialScenes: Scene[] = [
  { id: 's1', name: 'Intro', duration: 5000, type: 'webcam' },
  { id: 's2', name: 'Dimostrazione', duration: 15000, type: 'screen' },
  { id: 's3', name: 'Conclusione', duration: 5000, type: 'webcam' },
]

const typeConfig = {
  webcam: { icon: Camera, label: 'Webcam', color: 'text-brand-400', bg: 'bg-brand-500/10' },
  screen: { icon: Monitor, label: 'Schermo', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  text: { icon: Type, label: 'Testo', color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  image: { icon: ImageIcon, label: 'Immagine', color: 'text-purple-400', bg: 'bg-purple-500/10' },
  mixed: { icon: Film, label: 'Misto', color: 'text-pink-400', bg: 'bg-pink-500/10' },
}

export function SceneEditor() {
  const [scenes, setScenes] = useState<Scene[]>(initialScenes)
  const [selectedScene, setSelectedScene] = useState<string>('s1')
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const dragOverIndexRef = useRef<number | null>(null)

  const addScene = () => {
    const newScene: Scene = {
      id: `s${Date.now()}`,
      name: `Scena ${scenes.length + 1}`,
      duration: 5000,
      type: 'webcam',
    }
    setScenes(prev => [...prev, newScene])
    setSelectedScene(newScene.id)
  }

  const removeScene = (id: string) => {
    if (scenes.length <= 1) return
    setScenes(prev => prev.filter(s => s.id !== id))
    if (selectedScene === id) {
      setSelectedScene(scenes[0].id === id ? scenes[1]?.id : scenes[0].id)
    }
  }

  const duplicateScene = (id: string) => {
    const scene = scenes.find(s => s.id === id)
    if (!scene) return
    const newScene: Scene = { ...scene, id: `s${Date.now()}`, name: `${scene.name} (copia)` }
    const idx = scenes.findIndex(s => s.id === id)
    setScenes(prev => [...prev.slice(0, idx + 1), newScene, ...prev.slice(idx + 1)])
    setSelectedScene(newScene.id)
  }

  const moveScene = (id: string, direction: 'up' | 'down') => {
    const idx = scenes.findIndex(s => s.id === id)
    if (direction === 'up' && idx === 0) return
    if (direction === 'down' && idx === scenes.length - 1) return
    const newScenes = [...scenes]
    const targetIdx = direction === 'up' ? idx - 1 : idx + 1
    ;[newScenes[idx], newScenes[targetIdx]] = [newScenes[targetIdx], newScenes[idx]]
    setScenes(newScenes)
  }

  const updateScene = (id: string, updates: Partial<Scene>) => {
    setScenes(prev => prev.map(s => s.id === id ? { ...s, ...updates } : s))
  }

  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (index: number) => {
    dragOverIndexRef.current = index
  }

  const handleDrop = () => {
    if (draggedIndex === null || dragOverIndexRef.current === null) return
    if (draggedIndex === dragOverIndexRef.current) return

    const newScenes = [...scenes]
    const [removed] = newScenes.splice(draggedIndex, 1)
    newScenes.splice(dragOverIndexRef.current, 0, removed)
    setScenes(newScenes)
    setDraggedIndex(null)
    dragOverIndexRef.current = null
  }

  const totalDuration = scenes.reduce((acc, s) => acc + s.duration, 0)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Film className="h-4 w-4 text-brand-400" />
          <h3 className="text-sm font-semibold text-white">Scene</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-mono">
            {(totalDuration / 1000).toFixed(1)}s
          </span>
          <Button variant="ghost" size="sm" onClick={addScene} className="h-8">
            <Plus className="h-3.5 w-3.5" />
            Aggiungi
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        {scenes.map((scene, index) => {
          const config = typeConfig[scene.type]
          const Icon = config.icon
          const isSelected = selectedScene === scene.id

          return (
            <div
              key={scene.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => { e.preventDefault(); handleDragOver(index) }}
              onDrop={handleDrop}
              onClick={() => setSelectedScene(scene.id)}
              className={cn(
                'flex items-center gap-3 rounded-lg border px-3 py-2.5 cursor-pointer transition-all',
                isSelected
                  ? 'border-brand-500/30 bg-brand-500/10'
                  : 'border-white/10 hover:bg-white/5'
              )}
            >
              <button
                className="cursor-grab text-gray-600 hover:text-gray-400 transition-colors"
                onMouseDown={(e) => e.stopPropagation()}
              >
                <GripVertical className="h-3.5 w-3.5" />
              </button>

              <div className={cn('flex h-8 w-8 items-center justify-center rounded-lg', config.bg)}>
                <Icon className={cn('h-4 w-4', config.color)} />
              </div>

              <div className="flex-1 min-w-0">
                <input
                  value={scene.name}
                  onChange={(e) => updateScene(scene.id, { name: e.target.value })}
                  onClick={(e) => e.stopPropagation()}
                  className="w-full bg-transparent text-sm font-medium text-white focus:outline-none"
                />
                <div className="flex items-center gap-2 mt-0.5">
                  <select
                    value={scene.type}
                    onChange={(e) => updateScene(scene.id, { type: e.target.value as Scene['type'] })}
                    onClick={(e) => e.stopPropagation()}
                    className="text-[10px] bg-transparent text-gray-500 focus:outline-none cursor-pointer"
                  >
                    <option value="webcam">Webcam</option>
                    <option value="screen">Schermo</option>
                    <option value="text">Testo</option>
                    <option value="image">Immagine</option>
                    <option value="mixed">Misto</option>
                  </select>
                  <span className="text-[10px] text-gray-600">
                    {(scene.duration / 1000).toFixed(1)}s
                  </span>
                </div>
              </div>

              {/* Duration slider */}
              <input
                type="range"
                min="1000"
                max="60000"
                step="500"
                value={scene.duration}
                onChange={(e) => updateScene(scene.id, { duration: parseInt(e.target.value) })}
                onClick={(e) => e.stopPropagation()}
                className="w-16 accent-brand-500 hidden sm:block"
              />

              <div className="flex items-center gap-0.5">
                <button
                  onClick={(e) => { e.stopPropagation(); moveScene(scene.id, 'up') }}
                  className="flex h-6 w-6 items-center justify-center rounded text-gray-600 hover:text-white hover:bg-white/5 transition-colors"
                  disabled={index === 0}
                >
                  <ChevronUp className="h-3 w-3" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); moveScene(scene.id, 'down') }}
                  className="flex h-6 w-6 items-center justify-center rounded text-gray-600 hover:text-white hover:bg-white/5 transition-colors"
                  disabled={index === scenes.length - 1}
                >
                  <ChevronDown className="h-3 w-3" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); duplicateScene(scene.id) }}
                  className="flex h-6 w-6 items-center justify-center rounded text-gray-600 hover:text-white hover:bg-white/5 transition-colors"
                >
                  <Copy className="h-3 w-3" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); removeScene(scene.id) }}
                  className="flex h-6 w-6 items-center justify-center rounded text-gray-600 hover:text-red-400 hover:bg-white/5 transition-colors"
                  disabled={scenes.length <= 1}
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
          )
        })}

        {scenes.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-gray-600">
            <Film className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">Nessuna scena</p>
            <Button variant="ghost" size="sm" onClick={addScene} className="mt-2">
              <Plus className="h-4 w-4" /> Crea scena
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
