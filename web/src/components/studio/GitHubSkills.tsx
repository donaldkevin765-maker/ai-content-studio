'use client'

import { useState } from 'react'
import { Github, Download, Star, GitFork, ExternalLink, Search, Code, Zap, Film, Music, Image as ImageIcon, Type, Sparkles, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'

interface Skill {
  id: string
  name: string
  description: string
  author: string
  repo: string
  stars: number
  forks: number
  installed: boolean
  category: 'effect' | 'transition' | 'text' | 'audio' | 'export' | 'ai'
  icon: typeof Code
}

const availableSkills: Skill[] = [
  {
    id: 'glitch-effect',
    name: 'Glitch Effect',
    description: 'Effetto glitch/glitch-art per transizioni video',
    author: 'videops',
    repo: 'glitch-effect',
    stars: 342,
    forks: 56,
    installed: false,
    category: 'effect',
    icon: Zap,
  },
  {
    id: 'custom-text-overlay',
    name: 'Custom Text Overlay',
    description: 'Overlay testuali animati con font personalizzati',
    author: 'typemaster',
    repo: 'text-overlay',
    stars: 189,
    forks: 23,
    installed: true,
    category: 'text',
    icon: Type,
  },
  {
    id: 'smooth-transition',
    name: 'Smooth Transition Pack',
    description: '20 transizioni fluide (dissolvenza, swipe, zoom)',
    author: 'editflow',
    repo: 'smooth-transitions',
    stars: 567,
    forks: 89,
    installed: false,
    category: 'transition',
    icon: Film,
  },
  {
    id: 'background-music',
    name: 'Background Music Kit',
    description: 'Tracce musicali royalty-free per video',
    author: 'audiocraft',
    repo: 'bg-music',
    stars: 1234,
    forks: 234,
    installed: false,
    category: 'audio',
    icon: Music,
  },
  {
    id: 'chroma-key',
    name: 'Chroma Key Pro',
    description: 'Green screen avanzato con edge refinement',
    author: 'visionary',
    repo: 'chroma-key',
    stars: 891,
    forks: 145,
    installed: false,
    category: 'effect',
    icon: ImageIcon,
  },
  {
    id: 'auto-caption',
    name: 'Auto Caption AI',
    description: 'Sottotitoli automatici con traduzione AI',
    author: 'linguaai',
    repo: 'auto-caption',
    stars: 2341,
    forks: 456,
    installed: false,
    category: 'ai',
    icon: Sparkles,
  },
  {
    id: 'speed-ramp',
    name: 'Speed Ramp',
    description: 'Velocità variabile con rampe fluide',
    author: 'motionpro',
    repo: 'speed-ramp',
    stars: 456,
    forks: 67,
    installed: false,
    category: 'effect',
    icon: Zap,
  },
  {
    id: 'youtube-export',
    name: 'YouTube Export Preset',
    description: 'Preset di esportazione ottimizzato per YouTube',
    author: 'contenthub',
    repo: 'yt-export',
    stars: 789,
    forks: 123,
    installed: true,
    category: 'export',
    icon: Download,
  },
]

const categoryLabels: Record<string, string> = {
  effect: 'Effetti',
  transition: 'Transizioni',
  text: 'Testo',
  audio: 'Audio',
  export: 'Esportazione',
  ai: 'AI',
}

export function GitHubSkills() {
  const [skills, setSkills] = useState<Skill[]>(availableSkills)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  const filteredSkills = skills.filter(skill => {
    const matchesSearch = searchQuery === '' ||
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.author.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesCategory = activeCategory === null || skill.category === activeCategory

    return matchesSearch && matchesCategory
  })

  const installedCount = skills.filter(s => s.installed).length
  const categories = Array.from(new Set(skills.map(s => s.category)))

  const toggleInstall = (skillId: string) => {
    setSkills(prev => prev.map(s =>
      s.id === skillId ? { ...s, installed: !s.installed } : s
    ))
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Github className="h-4 w-4 text-brand-400" />
          <h3 className="text-sm font-semibold text-white">GitHub Skills</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{skills.length} disponibili</span>
          <span className="text-brand-400">{installedCount} installati</span>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            placeholder="Cerca skill..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="glass-input pl-10"
          />
        </div>

        {/* Category filters */}
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => setActiveCategory(null)}
            className={cn(
              'rounded-lg px-3 py-1.5 text-xs font-medium transition-all',
              activeCategory === null
                ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                : 'text-gray-500 hover:text-white hover:bg-white/5 border border-transparent'
            )}
          >
            Tutti
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(activeCategory === cat ? null : cat)}
              className={cn(
                'rounded-lg px-3 py-1.5 text-xs font-medium transition-all',
                activeCategory === cat
                  ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                  : 'text-gray-500 hover:text-white hover:bg-white/5 border border-transparent'
              )}
            >
              {categoryLabels[cat] || cat}
            </button>
          ))}
        </div>

        {/* Skills list */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {filteredSkills.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-gray-600">
              <Github className="h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">Nessuna skill trovata</p>
              <p className="text-xs mt-1">Prova a modificare la ricerca</p>
            </div>
          ) : (
            filteredSkills.map((skill) => {
              const Icon = skill.icon
              return (
                <div
                  key={skill.id}
                  className="flex items-start gap-3 rounded-lg border border-white/10 p-3 transition-all hover:bg-white/[0.02]"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5">
                    <Icon className="h-4 w-4 text-gray-400" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-medium text-white truncate">{skill.name}</h4>
                      <span className="shrink-0 text-[10px] text-gray-600 bg-white/5 px-1.5 py-0.5 rounded">
                        {categoryLabels[skill.category]}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{skill.description}</p>
                    <div className="flex items-center gap-3 mt-1.5">
                      <span className="text-[10px] text-gray-600">{skill.author}/{skill.repo}</span>
                      <span className="flex items-center gap-0.5 text-[10px] text-gray-600">
                        <Star className="h-3 w-3" />
                        {skill.stars}
                      </span>
                      <span className="flex items-center gap-0.5 text-[10px] text-gray-600">
                        <GitFork className="h-3 w-3" />
                        {skill.forks}
                      </span>
                    </div>
                  </div>

                  <Button
                    variant={skill.installed ? 'secondary' : 'default'}
                    size="sm"
                    onClick={() => toggleInstall(skill.id)}
                    className="shrink-0"
                  >
                    {skill.installed ? (
                      <><Check className="h-3.5 w-3.5" /> Installato</>
                    ) : (
                      <><Download className="h-3.5 w-3.5" /> Installa</>
                    )}
                  </Button>
                </div>
              )
            })
          )}
        </div>
      </CardContent>
    </Card>
  )
}
