'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Sparkles, ArrowRight, Sunrise, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import type { MaqamResponse, SongListResponse, SongResponse } from '@/lib/types'
import { SectionHeading } from '@/components/section-heading'
import { SongCard } from '@/components/song-card'
import { MaqamCard } from '@/components/maqamat/maqam-card'

type LoadState = 'loading' | 'ready' | 'error'

function groupByMood(songs: SongResponse[]): { mood: string; songs: SongResponse[] }[] {
  const groups = new Map<string, SongResponse[]>()

  for (const song of songs) {
    for (const mood of song.moods ?? []) {
      const list = groups.get(mood) ?? []
      list.push(song)
      groups.set(mood, list)
    }
  }

  return Array.from(groups.entries())
    .map(([mood, items]) => ({ mood, songs: items }))
    .sort((a, b) => b.songs.length - a.songs.length)
    .slice(0, 3)
}

export default function DiscoverPage() {
  const [songs, setSongs] = useState<SongResponse[]>([])
  const [maqamat, setMaqamat] = useState<MaqamResponse[]>([])
  const [state, setState] = useState<LoadState>('loading')

  useEffect(() => {
    let cancelled = false

    Promise.all([
      api<SongListResponse>('/songs', { query: { page: 1, page_size: 100 } }),
      api<MaqamResponse[]>('/maqamat'),
    ])
      .then(([songList, maqamList]) => {
        if (cancelled) return
        setSongs(songList.items)
        setMaqamat(maqamList)
        setState('ready')
      })
      .catch(() => {
        if (!cancelled) setState('error')
      })

    return () => {
      cancelled = true
    }
  }, [])

  const moodCollections = groupByMood(songs)

  return (
    <div className="mx-auto max-w-6xl">
      {/* Hero */}
      <section className="overflow-hidden rounded-2xl border border-gold/20 bg-vignette p-6 md:p-8">
        <span className="inline-flex items-center gap-2 rounded-full border border-gold/25 bg-gold-muted px-3 py-1 text-xs font-medium text-gold">
          <Sunrise className="size-3.5" /> Explore the archive
        </span>
        <h1 className="mt-4 font-display text-3xl font-semibold text-balance md:text-4xl">
          Discover by feeling
        </h1>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground md:text-base">
          Collections grouped by mood and maqam — a starting point for your next set.
        </p>
        <Link
          href="/semantic"
          className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-gold hover:underline"
        >
          Or search lyrics by meaning <ArrowRight className="size-4" />
        </Link>
      </section>

      {state === 'loading' && (
        <div className="mt-10 flex items-center justify-center gap-2 rounded-xl border border-border bg-card py-16 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading the archive…
        </div>
      )}

      {state === 'error' && (
        <div className="mt-10 rounded-xl border border-border bg-card py-16 text-center text-sm text-muted-foreground">
          We could not load the archive right now. Please try again in a moment.
        </div>
      )}

      {state === 'ready' && (
        <>
          {/* Mood collections */}
          {moodCollections.length === 0 ? (
            <div className="mt-10 rounded-xl border border-dashed border-border bg-card py-16 text-center text-sm text-muted-foreground">
              No songs have moods tagged yet — add some via the song library to build
              collections here.
            </div>
          ) : (
            moodCollections.map((col) => (
              <section key={col.mood} className="mt-10">
                <div className="mb-6 flex items-center gap-3">
                  <span className="flex size-11 items-center justify-center rounded-xl border border-gold/25 bg-gold-muted text-gold">
                    <Sparkles className="size-5" />
                  </span>
                  <div>
                    <h2 className="font-display text-2xl font-semibold capitalize">
                      {col.mood}
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      {col.songs.length} song{col.songs.length === 1 ? '' : 's'} with this mood
                    </p>
                  </div>
                </div>
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
                  {col.songs.slice(0, 4).map((s) => (
                    <SongCard key={s.id} song={s} />
                  ))}
                </div>
              </section>
            ))
          )}

          {/* Explore maqamat */}
          <section className="mt-12">
            <SectionHeading
              eyebrow="By mode"
              title="Start from a maqam"
              description="Each mode opens a different emotional world."
              actionLabel="All maqamat"
              actionHref="/maqamat"
            />
            {maqamat.length === 0 ? (
              <p className="text-sm text-muted-foreground">No maqamat in the library yet.</p>
            ) : (
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {maqamat.slice(0, 6).map((m) => (
                  <MaqamCard key={m.id} maqam={m} />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
