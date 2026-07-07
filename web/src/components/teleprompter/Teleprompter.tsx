'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { Play, Pause, ChevronUp, ChevronDown, Settings, RotateCcw, Type, Maximize2, Minimize2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'

interface TeleprompterProps {
  script?: string
  className?: string
}

const DEFAULT_SCRIPT = `Inizia il tuo video con un'introduzione coinvolgente...

Parla del contenuto principale con sicurezza e chiarezza.

Ricorda di mantenere un contatto visivo con la telecamera.

Concludi con un call to action efficace.`

export function Teleprompter({ script = DEFAULT_SCRIPT, className }: TeleprompterProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1.5)
  const [fontSize, setFontSize] = useState(28)
  const [mirrored, setMirrored] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const animationRef = useRef<number | null>(null)
  const lastTimeRef = useRef<number>(0)

  const stopScroll = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
      animationRef.current = null
    }
  }, [])

  const startScroll = useCallback(() => {
    lastTimeRef.current = performance.now()

    const animate = (currentTime: number) => {
      const delta = currentTime - lastTimeRef.current
      lastTimeRef.current = currentTime

      if (scrollRef.current) {
        const pxPerMs = speed * 0.02
        scrollRef.current.scrollTop += delta * pxPerMs

        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
        if (scrollTop + clientHeight >= scrollHeight - 5) {
          setIsPlaying(false)
          return
        }
      }

      animationRef.current = requestAnimationFrame(animate)
    }

    animationRef.current = requestAnimationFrame(animate)
  }, [speed])

  const togglePlay = useCallback(() => {
    if (isPlaying) {
      stopScroll()
      setIsPlaying(false)
    } else {
      setIsPlaying(true)
      startScroll()
    }
  }, [isPlaying, stopScroll, startScroll])

  const resetScroll = useCallback(() => {
    stopScroll()
    setIsPlaying(false)
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0
    }
  }, [stopScroll])

  const adjustSpeed = useCallback((delta: number) => {
    setSpeed(prev => Math.max(0.3, Math.min(10, prev + delta)))
  }, [])

  const toggleFullscreen = async () => {
    if (!isFullscreen) {
      await document.documentElement.requestFullscreen()
      setIsFullscreen(true)
    } else {
      await document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      switch (e.code) {
        case 'Space':
          e.preventDefault()
          togglePlay()
          break
        case 'ArrowUp':
          e.preventDefault()
          adjustSpeed(0.1)
          break
        case 'ArrowDown':
          e.preventDefault()
          adjustSpeed(-0.1)
          break
        case 'Escape':
          if (isPlaying) togglePlay()
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      stopScroll()
    }
  }, [togglePlay, adjustSpeed, stopScroll, isPlaying])

  return (
    <Card className={cn('overflow-hidden', isFullscreen && 'fixed inset-0 z-50 rounded-none', className)}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Type className="h-4 w-4 text-brand-400" />
          <h3 className="text-sm font-semibold text-white">Teleprompter</h3>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={() => setShowSettings(!showSettings)} className="h-8">
            <Settings className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="sm" onClick={toggleFullscreen} className="h-8">
            {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Script display */}
        <div
          ref={scrollRef}
          className={cn(
            'relative h-64 overflow-y-auto rounded-lg border border-white/10 bg-black/40 p-6 scrollbar-hide select-none',
            mirrored && 'scale-x-[-1]'
          )}
        >
          <p
            className="leading-relaxed text-white transition-all duration-300"
            style={{ fontSize: `${fontSize}px` }}
          >
            {script}
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => adjustSpeed(-0.2)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-all"
          >
            <ChevronDown className="h-4 w-4" />
          </button>

          <Button
            onClick={togglePlay}
            variant={isPlaying ? 'secondary' : 'default'}
            size="md"
            className="min-w-[100px]"
          >
            {isPlaying ? (
              <><Pause className="h-4 w-4" /> Pausa</>
            ) : (
              <><Play className="h-4 w-4" /> Avvia</>
            )}
          </Button>

          <button
            onClick={() => adjustSpeed(0.2)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-all"
          >
            <ChevronUp className="h-4 w-4" />
          </button>

          <Button variant="ghost" size="sm" onClick={resetScroll} className="h-8">
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Speed indicator */}
        <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
          <span>Velocità: <strong className="text-white font-mono">{speed.toFixed(1)}x</strong></span>
          <span>Dimensione: <strong className="text-white font-mono">{fontSize}px</strong></span>
        </div>

        {/* Settings panel */}
        {showSettings && (
          <div className="animate-slide-down space-y-3 border-t border-white/10 pt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-gray-400">Velocità</label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min="0.3"
                    max="10"
                    step="0.1"
                    value={speed}
                    onChange={(e) => setSpeed(parseFloat(e.target.value))}
                    className="flex-1 accent-brand-500"
                  />
                  <span className="w-10 text-right text-xs text-white font-mono">{speed.toFixed(1)}x</span>
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-gray-400">Dimensione testo</label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min="14"
                    max="72"
                    step="2"
                    value={fontSize}
                    onChange={(e) => setFontSize(parseInt(e.target.value))}
                    className="flex-1 accent-brand-500"
                  />
                  <span className="w-10 text-right text-xs text-white font-mono">{fontSize}px</span>
                </div>
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={mirrored}
                onChange={(e) => setMirrored(e.target.checked)}
                className="rounded border-white/20 bg-white/5 accent-brand-500"
              />
              Specchio (per vetri riflettenti)
            </label>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
