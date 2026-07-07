'use client'

import { useState } from 'react'
import { Sparkles, Layers, Palette, Blend, Sun, Contrast, Droplets, Wind, FlipHorizontal, FlipVertical, RotateCw, Check, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'

interface Effect {
  id: string
  name: string
  icon: typeof Sparkles
  category: 'filter' | 'transform' | 'overlay'
  preview?: string
}

const effects: Effect[] = [
  // Filters
  { id: 'normal', name: 'Normale', icon: Palette, category: 'filter' },
  { id: 'vintage', name: 'Vintage', icon: Sun, category: 'filter' },
  { id: 'noir', name: 'Noir', icon: Contrast, category: 'filter' },
  { id: 'vivid', name: 'Vivid', icon: Droplets, category: 'filter' },
  { id: 'soft', name: 'Soft', icon: Wind, category: 'filter' },
  { id: 'warm', name: 'Caldo', icon: Sun, category: 'filter' },
  { id: 'cool', name: 'Freddo', icon: Droplets, category: 'filter' },
  { id: 'dramatic', name: 'Drammatico', icon: Contrast, category: 'filter' },
  // Transforms
  { id: 'flip-h', name: 'Flip H', icon: FlipHorizontal, category: 'transform' },
  { id: 'flip-v', name: 'Flip V', icon: FlipVertical, category: 'transform' },
  { id: 'rotate-90', name: 'Ruota 90°', icon: RotateCw, category: 'transform' },
  // Overlays
  { id: 'grid', name: 'Griglia', icon: Layers, category: 'overlay' },
  { id: 'scanlines', name: 'Scanlines', icon: Layers, category: 'overlay' },
  { id: 'vignette', name: 'Vignetta', icon: Blend, category: 'overlay' },
]

const categories = [
  { id: 'filter' as const, label: 'Filtri', icon: Palette },
  { id: 'transform' as const, label: 'Trasformazioni', icon: FlipHorizontal },
  { id: 'overlay' as const, label: 'Overlay', icon: Layers },
]

export function EffectsPanel() {
  const [activeCategory, setActiveCategory] = useState<'filter' | 'transform' | 'overlay'>('filter')
  const [activeEffect, setActiveEffect] = useState<string>('normal')
  const [opacity, setOpacity] = useState(100)

  const filteredEffects = effects.filter(e => e.category === activeCategory)
  const currentEffect = effects.find(e => e.id === activeEffect)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-brand-400" />
          <h3 className="text-sm font-semibold text-white">Effetti</h3>
        </div>
        {activeEffect !== 'normal' && (
          <Button variant="ghost" size="sm" onClick={() => setActiveEffect('normal')} className="h-7 text-xs">
            <X className="h-3 w-3" />
            Rimuovi
          </Button>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Category tabs */}
        <div className="flex gap-1 bg-white/5 rounded-lg p-1">
          {categories.map((cat) => {
            const Icon = cat.icon
            const isActive = activeCategory === cat.id
            return (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={cn(
                  'flex-1 flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all',
                  isActive
                    ? 'bg-brand-500/20 text-brand-400'
                    : 'text-gray-500 hover:text-gray-300'
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {cat.label}
              </button>
            )
          })}
        </div>

        {/* Effects grid */}
        <div className="grid grid-cols-4 gap-2">
          {filteredEffects.map((effect) => {
            const Icon = effect.icon
            const isActive = activeEffect === effect.id

            return (
              <button
                key={effect.id}
                onClick={() => setActiveEffect(effect.id)}
                className={cn(
                  'flex flex-col items-center justify-center gap-1.5 rounded-lg border p-3 transition-all',
                  isActive
                    ? 'border-brand-500/30 bg-brand-500/10'
                    : 'border-white/10 hover:bg-white/5'
                )}
              >
                <div className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-lg',
                  isActive ? 'bg-brand-500/20 text-brand-400' : 'text-gray-400'
                )}>
                  <Icon className="h-4 w-4" />
                </div>
                <span className={cn(
                  'text-[10px] font-medium',
                  isActive ? 'text-brand-400' : 'text-gray-500'
                )}>
                  {effect.name}
                </span>
              </button>
            )
          })}
        </div>

        {/* Opacity slider (only when effect is active) */}
        {activeEffect !== 'normal' && (
          <div className="space-y-2 pt-2 border-t border-white/10">
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-400">Opacità</label>
              <span className="text-xs text-white font-mono">{opacity}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={opacity}
              onChange={(e) => setOpacity(parseInt(e.target.value))}
              className="w-full accent-brand-500"
            />
          </div>
        )}

        {/* No effects state */}
        {filteredEffects.length === 0 && (
          <div className="flex flex-col items-center justify-center py-6 text-gray-600">
            <Sparkles className="h-6 w-6 mb-2 opacity-50" />
            <p className="text-xs">Nessun effetto disponibile</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
