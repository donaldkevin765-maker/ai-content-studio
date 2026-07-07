'use client'

import { useRef, useEffect, useState } from 'react'
import {
  Video,
  Monitor,
  Camera,
  Square,
  Download,
  Trash2,
  RotateCcw,
  Pause,
  Play,
  Settings,
  Maximize2,
  Minimize2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { useRecorder, formatTime } from '@/hooks/useRecorder'
import type { MediaSource } from '@/hooks/useRecorder'

export function Recorder() {
  const [selectedSource, setSelectedSource] = useState<MediaSource>('webcam')
  const [showSettings, setShowSettings] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const {
    isRecording,
    isPaused,
    duration,
    blob,
    stream,
    error,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecording,
    resetRecording,
    downloadRecording,
  } = useRecorder()

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  useEffect(() => {
    if (blob) {
      const url = URL.createObjectURL(blob)
      setPreviewUrl(url)
      return () => URL.revokeObjectURL(url)
    }
    setPreviewUrl(null)
  }, [blob])

  const handleStart = () => startRecording(selectedSource)

  const toggleFullscreen = async () => {
    if (!containerRef.current) return
    if (!document.fullscreenElement) {
      await containerRef.current.requestFullscreen()
      setIsFullscreen(true)
    } else {
      await document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const sourceOptions: { value: MediaSource; label: string; icon: typeof Video }[] = [
    { value: 'webcam', label: 'Webcam', icon: Camera },
    { value: 'screen', label: 'Schermo', icon: Monitor },
    { value: 'both', label: 'Entrambi', icon: Video },
  ]

  return (
    <div ref={containerRef} className="relative">
      <Card className={cn('overflow-hidden', isFullscreen && 'fixed inset-0 z-50 rounded-none')}>
        {/* Video Preview */}
        <div className="relative aspect-video bg-black overflow-hidden">
          {stream ? (
            <video
              ref={videoRef}
              className="h-full w-full object-cover"
              autoPlay
              muted
              playsInline
            />
          ) : previewUrl ? (
            <video
              className="h-full w-full object-cover"
              src={previewUrl}
              controls
              autoPlay
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-600">
              <Video className="h-16 w-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">Nessuna sorgente video</p>
              <p className="text-sm mt-1">Seleziona una sorgente e premi Registra</p>
            </div>
          )}

          {/* Recording indicator */}
          {isRecording && (
            <div className="absolute top-3 left-3 flex items-center gap-2">
              <span className="recording-indicator">{formatTime(duration)}</span>
              {isPaused && (
                <span className="bg-yellow-500/90 text-white px-3 py-1 rounded-full text-xs font-medium shadow-lg">
                  In pausa
                </span>
              )}
            </div>
          )}

          <button
            onClick={toggleFullscreen}
            className="absolute top-3 right-3 flex h-8 w-8 items-center justify-center rounded-lg bg-black/50 text-white/70 hover:bg-black/70 hover:text-white transition-all"
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>

          {/* Recording complete overlay */}
          {blob && !isRecording && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm">
              <div className="text-center p-6">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20">
                  <Download className="h-8 w-8 text-emerald-400" />
                </div>
                <p className="text-lg font-semibold text-white">Registrazione completata</p>
                <p className="mt-1 font-mono text-sm text-gray-400">{formatTime(duration)}</p>
              </div>
            </div>
          )}
        </div>

        {/* Controls */}
        <CardContent className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500/20 text-[10px] font-bold">!</span>
              {error}
            </div>
          )}

          {/* Source selector */}
          {!isRecording && !blob && (
            <>
              <div className="flex items-center gap-2">
                {sourceOptions.map((opt) => {
                  const Icon = opt.icon
                  return (
                    <button
                      key={opt.value}
                      onClick={() => setSelectedSource(opt.value)}
                      className={cn(
                        'flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all',
                        selectedSource === opt.value
                          ? 'border border-brand-500/30 bg-brand-500/20 text-brand-400'
                          : 'border border-transparent text-gray-400 hover:bg-white/5 hover:text-white'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {opt.label}
                    </button>
                  )
                })}
                <div className="ml-auto">
                  <button
                    onClick={() => setShowSettings(!showSettings)}
                    className={cn(
                      'flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm transition-all',
                      showSettings ? 'bg-white/10 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-white'
                    )}
                  >
                    <Settings className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Recording controls */}
          <div className="flex items-center justify-center gap-4">
            {!isRecording && !blob && (
              <Button onClick={handleStart} size="xl" className="h-16 w-16 rounded-full">
                <Video className="h-7 w-7" />
                <span className="sr-only">Registra</span>
              </Button>
            )}

            {isRecording && !isPaused && (
              <>
                <Button variant="secondary" onClick={pauseRecording} size="lg" className="h-14 w-14 rounded-full">
                  <Pause className="h-6 w-6" />
                  <span className="sr-only">Pausa</span>
                </Button>
                <Button variant="destructive" onClick={stopRecording} size="lg" className="h-14 w-14 rounded-full">
                  <Square className="h-6 w-6" />
                  <span className="sr-only">Ferma</span>
                </Button>
              </>
            )}

            {isPaused && (
              <>
                <Button variant="secondary" onClick={resumeRecording} size="lg" className="h-14 w-14 rounded-full">
                  <Play className="h-6 w-6" />
                  <span className="sr-only">Riprendi</span>
                </Button>
                <Button variant="destructive" onClick={stopRecording} size="lg" className="h-14 w-14 rounded-full">
                  <Square className="h-6 w-6" />
                  <span className="sr-only">Ferma</span>
                </Button>
              </>
            )}

            {blob && !isRecording && (
              <>
                <Button variant="secondary" onClick={resetRecording} size="lg" className="h-14 w-14 rounded-full">
                  <RotateCcw className="h-6 w-6" />
                  <span className="sr-only">Nuova</span>
                </Button>
                <Button variant="destructive" onClick={resetRecording} size="lg" className="h-14 w-14 rounded-full">
                  <Trash2 className="h-6 w-6" />
                  <span className="sr-only">Elimina</span>
                </Button>
                <Button onClick={downloadRecording} size="lg" className="h-14 w-14 rounded-full">
                  <Download className="h-6 w-6" />
                  <span className="sr-only">Scarica</span>
                </Button>
              </>
            )}
          </div>

          {/* Settings panel */}
          {showSettings && !isRecording && (
            <div className="animate-slide-down space-y-3 border-t border-white/10 pt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-gray-400">Risoluzione</label>
                  <select className="glass-input text-xs">
                    <option value="1920">1920×1080 (Full HD)</option>
                    <option value="1280">1280×720 (HD)</option>
                    <option value="640">640×480 (SD)</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-gray-400">FPS</label>
                  <select className="glass-input text-xs">
                    <option value="30">30 fps</option>
                    <option value="60">60 fps</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Post-recording actions */}
      {blob && !isRecording && (
        <div className="mt-4 flex animate-slide-up items-center justify-center gap-3">
          <Button variant="secondary" size="sm" onClick={downloadRecording}>
            <Download className="h-4 w-4" />
            Scarica Video
          </Button>
          <Button size="sm">
            <Video className="h-4 w-4" />
            Aggiungi a Timeline
          </Button>
        </div>
      )}
    </div>
  )
}
