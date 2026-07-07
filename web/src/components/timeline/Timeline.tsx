'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import {
  Video,
  Music,
  Mic,
  Image,
  Plus,
  GripVertical,
  Scissors,
  Trash2,
  Clock,
  Play,
  Pause,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatTime } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { generateId } from '@/lib/utils'

interface TrackClip {
  id: string
  type: 'video' | 'audio' | 'text' | 'image'
  label: string
  start: number  // ms
  duration: number  // ms
  color?: string
}

interface Track {
  id: string
  name: string
  type: 'video' | 'audio' | 'text' | 'overlay'
  clips: TrackClip[]
  visible: boolean
  locked: boolean
}

const TRACK_COLORS = {
  video: 'rgba(99, 102, 241, 0.3)',
  audio: 'rgba(34, 197, 94, 0.3)',
  text: 'rgba(234, 179, 8, 0.3)',
  overlay: 'rgba(236, 72, 153, 0.3)',
  default: 'rgba(255, 255, 255, 0.1)',
}

const TRACK_ICONS = {
  video: Video,
  audio: Music,
  text: Type,
  overlay: Image,
}

import { Type } from 'lucide-react'

export function Timeline() {
  const [tracks, setTracks] = useState<Track[]>([
    {
      id: 'video-1',
      name: 'Video',
      type: 'video',
      clips: [
        { id: 'clip-1', type: 'video', label: 'Webcam', start: 0, duration: 15000, color: TRACK_COLORS.video },
      ],
      visible: true,
      locked: false,
    },
    {
      id: 'audio-1',
      name: 'Audio',
      type: 'audio',
      clips: [
        { id: 'clip-2', type: 'audio', label: 'Microfono', start: 0, duration: 15000, color: TRACK_COLORS.audio },
      ],
      visible: true,
      locked: false,
    },
    {
      id: 'text-1',
      name: 'Sottotitoli',
      type: 'text',
      clips: [],
      visible: true,
      locked: false,
    },
    {
      id: 'overlay-1',
      name: 'Overlay',
      type: 'overlay',
      clips: [],
      visible: true,
      locked: false,
    },
  ])

  const [currentTime, setCurrentTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [zoom, setZoom] = useState(1)
  const timelineRef = useRef<HTMLDivElement>(null)
  const animationRef = useRef<number | null>(null)
  const [draggingClip, setDraggingClip] = useState<string | null>(null)

  const totalDuration = Math.max(
    ...tracks.map(t =>
      t.clips.reduce((max, c) => Math.max(max, c.start + c.duration), 0)
    ),
    30000 // minimum 30s
  )

  const pixelsPerMs = 0.05 * zoom
  const timelineWidth = totalDuration * pixelsPerMs

  const togglePlay = useCallback(() => {
    if (isPlaying) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
        animationRef.current = null
      }
      setIsPlaying(false)
    } else {
      if (currentTime >= totalDuration) setCurrentTime(0)
      setIsPlaying(true)
    }
  }, [isPlaying, currentTime, totalDuration])

  useEffect(() => {
    if (!isPlaying) return

    let lastTime = performance.now()
    const animate = (now: number) => {
      const delta = now - lastTime
      lastTime = now

      setCurrentTime(prev => {
        const next = prev + delta
        if (next >= totalDuration) {
          setIsPlaying(false)
          return totalDuration
        }
        return next
      })

      animationRef.current = requestAnimationFrame(animate)
    }

    animationRef.current = requestAnimationFrame(animate)
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
    }
  }, [isPlaying, totalDuration])

  const addTrack = (type: Track['type']) => {
    const newTrack: Track = {
      id: `${type}-${Date.now()}`,
      name: `${type === 'video' ? 'Video' : type === 'audio' ? 'Audio' : type === 'text' ? 'Testo' : 'Overlay'} ${tracks.filter(t => t.type === type).length + 1}`,
      type,
      clips: [],
      visible: true,
      locked: false,
    }
    setTracks(prev => [...prev, newTrack])
  }

  const removeTrack = (trackId: string) => {
    setTracks(prev => prev.filter(t => t.id !== trackId))
  }

  const addClip = (trackId: string) => {
    setTracks(prev => prev.map(track => {
      if (track.id !== trackId) return track
      return {
        ...track,
        clips: [...track.clips, {
          id: `clip-${Date.now()}`,
          type: track.type === 'overlay' ? 'image' : track.type === 'text' ? 'text' : track.type,
          label: `Clip ${track.clips.length + 1}`,
          start: Math.max(0, currentTime - 2000),
          duration: 5000,
          color: TRACK_COLORS[track.type] || TRACK_COLORS.default,
        }],
      }
    }))
  }

  const removeClip = (trackId: string, clipId: string) => {
    setTracks(prev => prev.map(track => {
      if (track.id !== trackId) return track
      return { ...track, clips: track.clips.filter(c => c.id !== clipId) }
    }))
  }

  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!timelineRef.current) return
    const rect = timelineRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const time = x / pixelsPerMs
    setCurrentTime(Math.max(0, Math.min(time, totalDuration)))
  }

  const formatTimeCompact = (ms: number) => {
    const s = Math.floor(ms / 1000)
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-brand-400" />
          <h3 className="text-sm font-semibold text-white">Timeline</h3>
        </div>
        <div className="flex items-center gap-1.5">
          <Button variant="ghost" size="sm" onClick={togglePlay} className="h-8">
            {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
          </Button>
          <input
            type="range"
            min="0.25"
            max="4"
            step="0.25"
            value={zoom}
            onChange={(e) => setZoom(parseFloat(e.target.value))}
            className="w-20 accent-brand-500"
            title="Zoom"
          />
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={() => addTrack('video')} className="h-8 px-2" title="Aggiungi traccia video">
              <Video className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => addTrack('audio')} className="h-8 px-2" title="Aggiungi traccia audio">
              <Music className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => addTrack('text')} className="h-8 px-2" title="Aggiungi traccia testo">
              <Type className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {/* Time ruler */}
        <div className="sticky top-0 z-10 flex border-b border-white/10 bg-[#121216]">
          <div className="w-36 shrink-0 border-r border-white/10 px-3 py-2 text-[10px] font-medium text-gray-500 uppercase">
            Tracce
          </div>
          <div
            ref={timelineRef}
            className="relative flex-1 h-8 cursor-pointer overflow-hidden"
            onClick={handleTimelineClick}
          >
            {/* Time markers */}
            {Array.from({ length: Math.ceil(totalDuration / 5000) }, (_, i) => (
              <div
                key={i}
                className="absolute top-0 h-full border-l border-white/5"
                style={{ left: `${i * 5000 * pixelsPerMs}px` }}
              >
                <span className="ml-1.5 text-[10px] text-gray-600">{formatTimeCompact(i * 5000)}</span>
              </div>
            ))}
            {/* Playhead */}
            <div
              className="absolute top-0 h-full w-px bg-brand-500 z-20 pointer-events-none shadow-glow-sm"
              style={{ left: `${currentTime * pixelsPerMs}px` }}
            >
              <div className="absolute -top-0.5 -left-1 h-2 w-2 rounded-full bg-brand-500 shadow-glow-sm" />
            </div>
          </div>
        </div>

        {/* Tracks */}
        <div className="overflow-y-auto max-h-[320px]">
          {tracks.map((track) => {
            const TrackIcon = TRACK_ICONS[track.type]
            return (
              <div key={track.id} className="flex border-b border-white/5 last:border-b-0">
                {/* Track label */}
                <div className="flex w-36 shrink-0 items-center gap-2 border-r border-white/5 px-3 py-2">
                  <button className="cursor-grab text-gray-600 hover:text-gray-400">
                    <GripVertical className="h-3.5 w-3.5" />
                  </button>
                  <TrackIcon className={cn('h-3.5 w-3.5', track.visible ? 'text-brand-400' : 'text-gray-600')} />
                  <span className="flex-1 truncate text-xs font-medium text-gray-300">{track.name}</span>
                  <button
                    onClick={() => addClip(track.id)}
                    className="text-gray-600 hover:text-white transition-colors"
                  >
                    <Plus className="h-3 w-3" />
                  </button>
                  {track.clips.length > 0 && (
                    <button
                      onClick={() => removeClip(track.id, track.clips[track.clips.length - 1].id)}
                      className="text-gray-600 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  )}
                </div>

                {/* Track content */}
                <div className="relative flex-1 h-12 bg-white/[0.01]">
                  {track.clips.map((clip) => (
                    <div
                      key={clip.id}
                      className="timeline-clip group flex items-center gap-1.5 px-2"
                      style={{
                        left: `${clip.start * pixelsPerMs}px`,
                        width: `${clip.duration * pixelsPerMs}px`,
                        background: clip.color,
                      }}
                    >
                      <span className="truncate text-[10px] font-medium text-white/90">
                        {clip.label}
                      </span>
                      <span className="shrink-0 text-[9px] text-white/60 font-mono">
                        {formatTimeCompact(clip.duration)}
                      </span>
                      {/* Resize handle */}
                      <div className="absolute right-0 top-0 h-full w-1 cursor-col-resize bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity rounded-r" />
                    </div>
                  ))}

                  {/* Empty state */}
                  {track.clips.length === 0 && (
                    <div className="flex h-full items-center justify-center">
                      <button
                        onClick={() => addClip(track.id)}
                        className="flex items-center gap-1 text-[10px] text-gray-600 hover:text-gray-400 transition-colors"
                      >
                        <Plus className="h-3 w-3" />
                        Aggiungi clip
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Bottom bar */}
        <div className="flex items-center justify-between border-t border-white/10 px-4 py-2">
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>Durata: <strong className="text-white font-mono">{formatTimeCompact(totalDuration)}</strong></span>
            <span>Corrente: <strong className="text-brand-400 font-mono">{formatTimeCompact(currentTime)}</strong></span>
          </div>
          <div className="flex items-center gap-1 text-[10px] text-gray-600">
            <Clock className="h-3 w-3" />
            {formatTimeCompact(currentTime)} / {formatTimeCompact(totalDuration)}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
