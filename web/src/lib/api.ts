// API client per il backend Sistema Video AI Automatico
// Backend: https://sistema-video-ai.vercel.app
// Docs: https://sistema-video-ai.vercel.app/docs

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

function getApiUrl(): string {
  // Priority: localStorage override > NEXT_PUBLIC_API_URL env > default
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('api_url')
    if (stored) return stored
  }
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL
  return 'https://sistema-video-ai.vercel.app'
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiUrl()
  const url = `${baseUrl}${endpoint}`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  const res = await fetch(url, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const body = await res.text()
    let message: string
    try {
      const parsed = JSON.parse(body)
      message = parsed.detail || parsed.message || body
    } catch {
      message = body || `Errore ${res.status}`
    }
    throw new ApiError(message, res.status)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

// ─── Types ──────────────────────────────────────────

export interface Project {
  id: number
  title: string
  description: string
  language: string
  status: string
  created_at: string
  updated_at: string
}

export interface Video {
  id: number
  project_id: number
  title: string
  script: string
  status: string
  progress_percent: number
  progress_step: string
  duration: number
  output_path: string
  output_url: string
  error_message: string
  created_at: string
  updated_at: string
}

export interface VideoDetail extends Video {
  scenes: Scene[]
}

export interface Scene {
  id: number
  video_id: number
  order: number
  content: string
  image_prompt: string
  image_path: string
  audio_path: string
  subtitle_text: string
  duration: number
}

export interface SocialAccount {
  id: number
  platform: string
  platform_user_id: string
  platform_username: string
  connected: boolean
  token_expiry: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

// ─── Projects ───────────────────────────────────────

export const projects = {
  list(page = 1, pageSize = 20) {
    return request<PaginatedResponse<Project>>(
      `/api/v1/projects/?page=${page}&page_size=${pageSize}`
    )
  },

  get(id: number) {
    return request<Project>(`/api/v1/projects/${id}`)
  },

  create(data: { title: string; description?: string; language?: string }) {
    return request<Project>('/api/v1/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  update(id: number, data: Partial<Project>) {
    return request<Project>(`/api/v1/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  delete(id: number) {
    return request<void>(`/api/v1/projects/${id}`, { method: 'DELETE' })
  },
}

// ─── Videos ─────────────────────────────────────────

export const videos = {
  list(projectId?: number, page = 1, pageSize = 20) {
    let endpoint = `/api/v1/videos/?page=${page}&page_size=${pageSize}`
    if (projectId) endpoint += `&project_id=${projectId}`
    return request<PaginatedResponse<Video>>(endpoint)
  },

  get(id: number) {
    return request<VideoDetail>(`/api/v1/videos/${id}`)
  },

  create(data: { project_id: number; title: string }) {
    return request<Video>('/api/v1/videos/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  delete(id: number) {
    return request<void>(`/api/v1/videos/${id}`, { method: 'DELETE' })
  },

  generateScript(id: number, data: { topic: string; duration_seconds?: number; style?: string; scene_count?: number }) {
    return request<{ video_id: number; script: string; scenes: any[] }>(
      `/api/v1/videos/${id}/generate-script`,
      { method: 'POST', body: JSON.stringify(data) }
    )
  },

  render(id: number) {
    return request<Video>(`/api/v1/videos/${id}/render`, { method: 'POST' })
  },

  compile(id: number) {
    return request<Video>(`/api/v1/videos/${id}/compile`, { method: 'POST' })
  },

  progress(id: number) {
    return request<{
      video_id: number
      status: string
      total_scenes: number
      current_scene: number
      current_step: string
      percent: number
      started_at: string
      errors: string[]
      finished_at: string | null
      error: string | null
    }>(`/api/v1/videos/${id}/progress`)
  },

  scenes(id: number) {
    return request<Scene[]>(`/api/v1/videos/${id}/scenes`)
  },
}

// ─── Social ─────────────────────────────────────────

export const social = {
  accounts() {
    return request<SocialAccount[]>('/api/v1/social/accounts')
  },

  authUrl(platform: string) {
    return request<{ url: string; state: string }>(`/api/v1/social/auth-url/${platform}`)
  },

  disconnect(accountId: number) {
    return request<void>(`/api/v1/social/accounts/${accountId}`, { method: 'DELETE' })
  },

  refresh(accountId: number) {
    return request<SocialAccount>(`/api/v1/social/refresh/${accountId}`, { method: 'POST' })
  },

  platformVideos(platform: string, accountId: number, maxResults = 10) {
    return request<any[]>(
      `/api/v1/social/videos/${platform}?account_id=${accountId}&max_results=${maxResults}`
    )
  },

  publish(data: { video_id: number; account_id: number; title?: string; description?: string }) {
    return request<{ success: boolean; platform_post_id?: string; url?: string; error?: string }>(
      '/api/v1/social/publish',
      { method: 'POST', body: JSON.stringify(data) }
    )
  },
}

// ─── Health ─────────────────────────────────────────

export async function checkHealth() {
  return request<any>('/health')
}

// ─── Auth (backend signup/login) ────────────────────

export async function signup(email: string, password: string) {
  return request<{ user_id: number; email: string; token: string; message: string }>(
    '/api/v1/auth/signup',
    { method: 'POST', body: JSON.stringify({ email, password }) }
  )
}

export async function login(email: string, password: string) {
  return request<{ user_id: number; email: string; token: string; message: string }>(
    '/api/v1/auth/login',
    { method: 'POST', body: JSON.stringify({ email, password }) }
  )
}

// ─── Verify token ──────────────────────────────────

export async function verifyToken(): Promise<boolean> {
  try {
    await projects.list(1, 1)
    return true
  } catch {
    return false
  }
}
