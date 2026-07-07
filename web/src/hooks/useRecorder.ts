'use client'

import { useState, useRef, useEffect, useCallback } from 'react'

export type MediaSource = 'webcam' | 'screen' | 'both'

interface RecordingState {
  isRecording: boolean
  isPaused: boolean
  duration: number
  blob: Blob | null
  stream: MediaStream | null
  error: string | null
  source: MediaSource
}

export function useRecorder() {
  const [state, setState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    blob: null,
    stream: null,
    error: null,
    source: 'webcam',
  })

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const startTimeRef = useRef<number>(0)
  const pausedDurationRef = useRef<number>(0)
  const streamRef = useRef<MediaStream | null>(null)

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const stopAllTracks = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
  }, [])

  const updateDuration = useCallback(() => {
    const elapsed = pausedDurationRef.current + (Date.now() - startTimeRef.current)
    setState(prev => ({ ...prev, duration: Math.max(0, elapsed) }))
  }, [])

  const getMediaStream = useCallback(async (source: MediaSource): Promise<MediaStream> => {
    if (source === 'webcam') {
      return navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: true,
      })
    }

    if (source === 'screen') {
      return navigator.mediaDevices.getDisplayMedia({
        video: { cursor: 'always' } as MediaTrackConstraints,
        audio: true,
      })
    }

    // both: screen + webcam picture-in-picture
    const [displayStream, userStream] = await Promise.all([
      navigator.mediaDevices.getDisplayMedia({
        video: { cursor: 'always' } as MediaTrackConstraints,
        audio: true,
      }),
      navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      }),
    ])

    const canvas = document.createElement('canvas')
    canvas.width = 1920
    canvas.height = 1080
    const ctx = canvas.getContext('2d')!

    const screenVideo = document.createElement('video')
    screenVideo.srcObject = displayStream
    await screenVideo.play()

    const userVideo = document.createElement('video')
    userVideo.srcObject = userStream
    await userVideo.play()

    const compositeStream = canvas.captureStream(30)
    const audioTrack = displayStream.getAudioTracks()[0]
    if (audioTrack) compositeStream.addTrack(audioTrack)

    let running = true
    const draw = () => {
      if (!running) return
      ctx.drawImage(screenVideo, 0, 0, canvas.width, canvas.height)
      const pipW = 320
      const pipH = 240
      const pipX = canvas.width - pipW - 20
      const pipY = canvas.height - pipH - 20
      ctx.fillStyle = 'rgba(99, 102, 241, 0.5)'
      ctx.fillRect(pipX - 2, pipY - 2, pipW + 4, pipH + 4)
      ctx.drawImage(userVideo, pipX, pipY, pipW, pipH)
      requestAnimationFrame(draw)
    }
    draw()

    displayStream.getVideoTracks()[0].onended = () => {
      running = false
      userStream.getTracks().forEach(t => t.stop())
    }

    return compositeStream
  }, [])

  const startRecording = useCallback(async (source: MediaSource = 'webcam') => {
    try {
      setState(prev => ({ ...prev, error: null, blob: null }))
      stopAllTracks()

      const stream = await getMediaStream(source)
      streamRef.current = stream

      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
        ? 'video/webm;codecs=vp9'
        : MediaRecorder.isTypeSupported('video/webm;codecs=vp8')
        ? 'video/webm;codecs=vp8'
        : 'video/webm'

      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType })
        stopAllTracks()
        clearTimer()
        setState(prev => ({
          ...prev,
          blob,
          isRecording: false,
          isPaused: false,
          stream: null,
        }))
      }

      recorder.start(100)
      startTimeRef.current = Date.now()
      pausedDurationRef.current = 0

      setState(prev => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        stream,
        source,
        duration: 0,
      }))

      timerRef.current = setInterval(updateDuration, 100)
    } catch (err: any) {
      stopAllTracks()
      setState(prev => ({
        ...prev,
        error: err.message === 'Permission denied'
          ? 'Permesso negato. Accedi a webcam/microfono nelle impostazioni.'
          : err.message || 'Errore avvio registrazione',
        stream: null,
      }))
    }
  }, [getMediaStream, stopAllTracks, updateDuration])

  const pauseRecording = useCallback(() => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== 'recording') return
    mediaRecorderRef.current.pause()
    pausedDurationRef.current += Date.now() - startTimeRef.current
    clearTimer()
    setState(prev => ({ ...prev, isPaused: true }))
  }, [clearTimer])

  const resumeRecording = useCallback(() => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== 'paused') return
    mediaRecorderRef.current.resume()
    startTimeRef.current = Date.now()
    setState(prev => ({ ...prev, isPaused: false }))
    timerRef.current = setInterval(updateDuration, 100)
  }, [updateDuration])

  const stopRecording = useCallback(() => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') return
    mediaRecorderRef.current.stop()
  }, [])

  const resetRecording = useCallback(() => {
    clearTimer()
    stopAllTracks()
    mediaRecorderRef.current = null
    chunksRef.current = []
    startTimeRef.current = 0
    pausedDurationRef.current = 0
    setState({
      isRecording: false,
      isPaused: false,
      duration: 0,
      blob: null,
      stream: null,
      error: null,
      source: 'webcam',
    })
  }, [clearTimer, stopAllTracks])

  const downloadRecording = useCallback(() => {
    if (!state.blob) return
    const url = URL.createObjectURL(state.blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `recording-${Date.now()}.webm`
    a.click()
    URL.revokeObjectURL(url)
  }, [state.blob])

  useEffect(() => {
    return () => {
      clearTimer()
      stopAllTracks()
    }
  }, [clearTimer, stopAllTracks])

  return {
    ...state,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecording,
    resetRecording,
    downloadRecording,
  }
}

export function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  const centiseconds = Math.floor((ms % 1000) / 10)
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`
  }
  return `${minutes}:${seconds.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`
}