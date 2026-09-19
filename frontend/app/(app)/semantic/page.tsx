'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ScanSearch, Sparkles, Loader2, ArrowUpRight, Quote } from 'lucide-react'
import { SEMANTIC_RESULTS } from '@/lib/mock-data'
import { SectionHeading } from '@/components/section-heading'
import { Badge } from '@/components/ui/badge'

const EXAMPLES = [
  'Missing someone who is far away',
  'The pain of parting and distance',
  'Joyful celebration of love',
  'Nostalgia for a lost homeland',
]

export default function SemanticSearchPage() {
  const [query, setQuery] = useState('')
  const [state, setState] = useState<'idle' | 'loading' | 'done'>('idle')

  function search(text: string) {
    const t = text.trim()
    if (!t) return
    setQuery(t)
    setState('loading')
    setTimeout(() => setState('done'), 1000)
  }

  return (
    <div className="mx-auto max-w-4xl">
      <SectionHeading
        eyebrow="Meaning search"
        title="Search lyrics by meaning"
        description="Describe a feeling or theme in your own words. Nagham reads the meaning of the lyrics — not just keywords — to find songs that truly express it."
      />

      {/* Search box */}
      <div className="rounded-2xl border border-gold/20 bg-vignette p-5 md:p-6">
        <div className="flex items-start gap-3 rounded-xl border border-input bg-background/40 p-3 focus-within:border-gold/60 focus-within:ring-2 focus-within:ring-ring">
          <ScanSearch className="mt-2 size-5 shrink-0 text-gold" />
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                if (e.nativeEvent.isComposing || e.keyCode === 229) return
                e.preventDefault()
                search(query)
              }
            }}
            rows={2}
            placeholder="e.g. Songs about longing for someone far away…"
            className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-sm text-foreground outline-none placeholder:text-muted-foreground/70"
          />
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => search(ex)}
                className="rounded-full border border-border bg-card/60 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground"
              >
                {ex}
              </button>
            ))}
          </div>
          <button
            onClick={() => search(query)}
            disabled={!query.trim() || state === 'loading'}
            className="flex items-center gap-1.5 rounded-lg bg-gold px-4 py-2 text-sm font-medium text-gold-foreground transition-colors hover:bg-gold/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {state === 'loading' ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Sparkles className="size-4" />
            )}
            Search
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="mt-8">
        {state === 'idle' && (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-16 text-center">
            <ScanSearch className="size-10 text-muted-foreground/50" />
            <p className="mt-4 font-display text-lg font-semibold">Describe what you feel</p>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Semantic search finds songs by the meaning of their lyrics, ranked by relevance.
            </p>
          </div>
        )}

        {state === 'loading' && (
          <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Reading the meaning of the repertoire…
          </div>
        )}

        {state === 'done' && (
          <>
            <p className="mb-5 text-sm text-muted-foreground">
              {SEMANTIC_RESULTS.length} songs ranked by relevance to{' '}
              <span className="font-medium text-foreground">“{query}”</span>
            </p>
            <div className="flex flex-col gap-4">
              {SEMANTIC_RESULTS.map(({ song, relevance, theme, explanation }) => (
                <Link
                  key={song.id}
                  href={`/songs/${song.id}`}
                  className="group rounded-2xl border border-border bg-card p-5 transition-colors hover:border-gold/40 hover:bg-surface"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-display text-xl font-semibold">{song.title}</h3>
                        <ArrowUpRight className="size-4 text-muted-foreground transition-colors group-hover:text-gold" />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {song.artist} · {song.year}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                      <span className="font-display text-lg font-semibold text-gold">
                        {Math.round(relevance * 100)}%
                      </span>
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-secondary">
                        <div
                          className="h-full rounded-full bg-gold"
                          style={{ width: `${relevance * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <Badge variant="gold">{song.maqam}</Badge>
                    <Badge variant="outline">{theme}</Badge>
                  </div>

                  <p className="mt-3 flex gap-2 text-sm leading-relaxed text-foreground/85">
                    <Sparkles className="mt-0.5 size-4 shrink-0 text-gold" />
                    {explanation}
                  </p>

                  <p className="mt-3 flex gap-2 border-t border-border/60 pt-3 text-sm text-muted-foreground italic">
                    <Quote className="mt-0.5 size-4 shrink-0 text-gold/60" />
                    {song.lyricsExcerpt}
                  </p>
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
