'use client'

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

const API_BASE = 'https://sistema-video-ai.vercel.app'

function getInitialUrl(): string {
  if (typeof window === 'undefined') return API_BASE
  return localStorage.getItem('api_url') || API_BASE
}

interface AuthContextType {
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string) => void
  logout: () => void
  apiUrl: string
  setApiUrl: (url: string) => void
}

const AuthContext = createContext<AuthContextType>({
  token: 'anonymous',
  isAuthenticated: true,
  isLoading: false,
  login: () => {},
  logout: () => {},
  apiUrl: getInitialUrl(),
  setApiUrl: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiUrl, setApiUrl] = useState(getInitialUrl)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Sync apiUrl from localStorage on mount
  useEffect(() => {
    if (!mounted) return
    const stored = localStorage.getItem('api_url')
    if (stored && stored !== apiUrl) {
      setApiUrl(stored)
    }
  }, [mounted])

  return (
    <AuthContext.Provider
      value={{
        token: 'anonymous',
        isAuthenticated: true,
        isLoading: false,
        login: () => {},
        logout: () => {},
        apiUrl,
        setApiUrl: (url: string) => {
          setApiUrl(url)
          localStorage.setItem('api_url', url)
        },
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
