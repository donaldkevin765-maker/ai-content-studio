'use client'

import { useState, useRef, useEffect } from 'react'
import {
  Send,
  Bot,
  User,
  Film,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Clock,
  ExternalLink,
  Sparkles,
  Youtube,
  Instagram,
  Music,
  Brain,
  ArrowRight,
  Play,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/lib/auth'

// ─── Types ──────────────────────────────────────────

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  task?: AgentTask
}

interface AgentTask {
  task_id: string
  project_id: number
  video_id: number
  topic: string
  status: string
  progress_percent: number
  progress_step: string
  output_url: string | null
  schedule: any | null
  error: string | null
  created_at: string
}

interface AgentResponse {
  task_id: string
  project_id: number
  video_id: number
  topic: string
  status: string
  schedule: any | null
  message: string
}

// ─── Quick actions ───────────────────────────────────

const quickActions = [
  { label: 'Video 30s sull\'IA', prompt: 'Fammi un video di 30 secondi sull\'intelligenza artificiale' },
  { label: 'Video motivazionale', prompt: 'Crea un video motivazionale di 60 secondi sul successo' },
  { label: 'Spiegazione 45s', prompt: 'Fammi un video di 45 secondi che spiega cos\'è il machine learning' },
  { label: 'Ogni giorno', prompt: 'Ogni giorno creami un video di 30 secondi sulle ultime novità tech' },
]

// ─── API call ────────────────────────────────────────

function getApiUrl(): string {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('api_url') || process.env.NEXT_PUBLIC_API_URL || 'https://backend-azure-kappa-69.vercel.app'
  }
  return 'https://backend-azure-kappa-69.vercel.app'
}

async function agentChat(prompt: string): Promise<AgentResponse> {
  const baseUrl = getApiUrl()
  const url = `${baseUrl}/api/v1/agent/chat?prompt=${encodeURIComponent(prompt)}`
  const res = await fetch(url, { method: 'POST' })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body ? JSON.parse(body).detail || body : `Errore ${res.status}`)
  }
  return res.json()
}

async function getTaskStatus(taskId: string): Promise<AgentTask> {
  const baseUrl = getApiUrl()
  const url = `${baseUrl}/api/v1/agent/tasks/${taskId}`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Task non trovato')
  return res.json()
}

// ─── Page ────────────────────────────────────────────

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Ciao! Sono il tuo assistente AI per la creazione video. Dimmi cosa vuoi creare e io mi occupo di tutto.\n\nEsempi: "fammi un video di 60 secondi sull\'IA", "ogni giorno un video sulle news tech", "crea un video motivazionale".',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [pollingTaskId, setPollingTaskId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Polling progress
  useEffect(() => {
    if (!pollingTaskId) return
    const interval = setInterval(async () => {
      try {
        const task = await getTaskStatus(pollingTaskId)
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, task }]
          }
          return prev
        })

        if (task.status === 'completed' || task.status === 'error') {
          setPollingTaskId(null)
        }
      } catch {
        setPollingTaskId(null)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [pollingTaskId])

  const sendMessage = async (prompt?: string) => {
    const text = (prompt || input).trim()
    if (!text || sending) return

    setInput('')
    setSending(true)

    // Add user message
    const userMsg: ChatMessage = { role: 'user', content: text, timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])

    // Add placeholder assistant message
    const assistantMsg: ChatMessage = {
      role: 'assistant',
      content: 'Analizzo la tua richiesta e preparo tutto...',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, assistantMsg])

    try {
      const response = await agentChat(text)
      const task: AgentTask = {
        task_id: response.task_id,
        project_id: response.project_id,
        video_id: response.video_id,
        topic: response.topic,
        status: 'generating',
        progress_percent: 10,
        progress_step: 'Pianificazione completata, avvio generazione...',
        output_url: null,
        schedule: response.schedule,
        error: null,
        created_at: new Date().toISOString(),
      }

      // Update assistant message with task
      setMessages(prev => {
        const last = prev[prev.length - 1]
        if (last.role === 'assistant') {
          return [...prev.slice(0, -1), {
            ...last,
            content: response.schedule
              ? `✅ Ho pianificato una routine!\n\n**Argomento:** ${response.topic}\n📅 **Frequenza:** ogni ${response.schedule.interval_seconds >= 604800 ? 'settimana' : response.schedule.interval_seconds >= 86400 ? 'giorno' : `${response.schedule.interval_seconds / 3600} ore`}\n\nIl primo video è in generazione...`
              : `✅ Richiesta ricevuta!\n\n**Argomento:** ${response.topic}\n⏱️ Generazione video in corso...\n\nTi tengo aggiornato sullo stato.`,
            task,
          }]
        }
        return prev
      })

      setPollingTaskId(response.task_id)
    } catch (err: any) {
      setMessages(prev => {
        const last = prev[prev.length - 1]
        if (last.role === 'assistant') {
          return [...prev.slice(0, -1), {
            ...last,
            content: `❌ Errore: ${err.message || 'Impossibile contattare il backend'}`,
            role: 'assistant',
          }]
        }
        return prev
      })
    } finally {
      setSending(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
      case 'generating':
        return <Badge variant="outline" className="bg-yellow-500/10 text-yellow-400 border-yellow-500/20"><Loader2 className="h-3 w-3 mr-1 animate-spin" /> In elaborazione</Badge>
      case 'rendering':
        return <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20"><Loader2 className="h-3 w-3 mr-1 animate-spin" /> Render in corso</Badge>
      case 'completed':
        return <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20"><CheckCircle2 className="h-3 w-3 mr-1" /> Completato</Badge>
      case 'error':
        return <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20"><AlertCircle className="h-3 w-3 mr-1" /> Errore</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bot className="h-6 w-6 text-brand-400" />
            Assistente AI
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Raccontami cosa vuoi creare e mi occupo di tutto
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-500/10">
                <Bot className="h-4 w-4 text-brand-400" />
              </div>
            )}

            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
              {/* Message bubble */}
              <div className={`rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-brand-500/10 text-white border border-brand-500/20'
                  : 'bg-[#1a1a24] text-gray-300 border border-white/5'
              }`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>

              {/* Task progress card */}
              {msg.task && msg.task.status !== 'completed' && msg.task.status !== 'error' && (
                <Card className="mt-3 bg-[#1a1a24] border-white/5">
                  <div className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">{getStatusBadge(msg.task.status)}</span>
                      <span className="text-xs text-gray-500">{msg.task.progress_percent}%</span>
                    </div>
                    <Progress value={msg.task.progress_percent} className="h-1.5" />
                    <p className="text-xs text-gray-500 flex items-center gap-1">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      {msg.task.progress_step}
                    </p>
                  </div>
                </Card>
              )}

              {/* Result card (completed) */}
              {msg.task?.status === 'completed' && (
                <Card className="mt-3 bg-emerald-500/5 border-emerald-500/20">
                  <div className="p-4 space-y-3">
                    <div className="flex items-center gap-2 text-emerald-400">
                      <CheckCircle2 className="h-5 w-5" />
                      <span className="text-sm font-semibold">Video pronto!</span>
                    </div>

                    {msg.task.output_url && (
                      <a
                        href={msg.task.output_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-brand-400 hover:text-brand-300 transition-colors"
                      >
                        <Play className="h-4 w-4" />
                        Guarda il video
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}

                    <div className="flex gap-2">
                      <a
                        href={`/projects/${msg.task.project_id}`}
                        className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
                      >
                        <Film className="h-3 w-3" />
                        Vedi progetto
                        <ArrowRight className="h-3 w-3" />
                      </a>
                    </div>

                    {/* Schedule info */}
                    {msg.task.schedule && (
                      <div className="flex items-center gap-2 text-xs text-gray-500 pt-2 border-t border-white/5">
                        <Calendar className="h-3 w-3" />
                        Prossimo video in {msg.task.schedule.interval_seconds >= 86400
                          ? `${Math.round(msg.task.schedule.interval_seconds / 86400)} giorni`
                          : `${Math.round(msg.task.schedule.interval_seconds / 3600)} ore`}
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* Error card */}
              {msg.task?.status === 'error' && (
                <Card className="mt-3 bg-red-500/5 border-red-500/20">
                  <div className="p-4 space-y-2">
                    <div className="flex items-center gap-2 text-red-400">
                      <AlertCircle className="h-5 w-5" />
                      <span className="text-sm font-semibold">Qualcosa è andato storto</span>
                    </div>
                    {msg.task.error && (
                      <p className="text-xs text-red-300/70">{msg.task.error}</p>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => sendMessage(msg.task?.topic || input)}
                      className="text-xs"
                    >
                      Riprova
                    </Button>
                  </div>
                </Card>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-500/20">
                <User className="h-4 w-4 text-brand-400" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick actions */}
      {messages.length <= 1 && (
        <div className="mb-4">
          <p className="text-xs text-gray-600 mb-2 flex items-center gap-1">
            <Sparkles className="h-3 w-3" />
            Azioni rapide
          </p>
          <div className="flex flex-wrap gap-2">
            {quickActions.map((action, i) => (
              <button
                key={i}
                onClick={() => sendMessage(action.prompt)}
                className="text-xs px-3 py-1.5 rounded-full bg-[#1a1a24] border border-white/5 text-gray-400 hover:text-white hover:border-brand-500/30 hover:bg-brand-500/5 transition-all"
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
          placeholder="Descrivi il video che vuoi creare..."
          className="flex-1 glass-input rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 border border-white/10 focus:border-brand-500/50 focus:outline-none transition-colors"
          disabled={sending}
        />
        <Button
          onClick={() => sendMessage()}
          disabled={!input.trim() || sending}
          className="shrink-0"
        >
          {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  )
}
