'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Sparkles,
  Music,
  Compass,
  ScanSearch,
  ArrowRight,
  Library,
  Waves,
  Loader2,
} from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { SongCard } from '@/components/song-card'
import { SectionHeading } from '@/components/section-heading'

import { api } from '@/lib/api'
import type {
  MaqamResponse,
  SongListResponse,
  SongResponse,
  UserResponse,
} from '@/lib/types'

import { SUGGESTED_PROMPTS } from '@/lib/mock-data'

const SHORTCUTS = [
  {
    href: '/assistant',
    title: 'Ask the AI Assistant',
    body: 'Find songs by mood, maqam or moment.',
    icon: Sparkles,
  },
  {
    href: '/discover',
    title: 'Discover repertoire',
    body: 'Browse curated collections by feeling.',
    icon: Compass,
  },
  {
    href: '/semantic',
    title: 'Search by meaning',
    body: 'Find songs by what their lyrics express.',
    icon: ScanSearch,
  },
  {
    href: '/songs',
    title: 'The full library',
    body: 'Filter by maqam, tonic and rhythm.',
    icon: Music,
  },
]

type MaqamSectionState = 'loading' | 'error' | 'ready'

export default function DashboardPage() {
  const router = useRouter()

  const [user, setUser] = useState<UserResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const [songs, setSongs] = useState<SongResponse[]>([])
  const [songsTotal, setSongsTotal] = useState<number | null>(null)
  const [songsSection, setSongsSection] = useState<MaqamSectionState>('loading')

  const [maqamat, setMaqamat] = useState<MaqamResponse[]>([])
  const [maqamSection, setMaqamSection] = useState<MaqamSectionState>('loading')

  useEffect(() => {
    async function loadCurrentUser() {
      const token = localStorage.getItem('access_token')

      // User is not logged in
      if (!token) {
        router.replace('/login')
        return
      }

      try {
        const me = await api<UserResponse>('/auth/me', { auth: true })
        setUser(me)
      } catch {
        // Token is invalid or expired
        localStorage.removeItem('access_token')
        router.replace('/login')
      } finally {
        setLoading(false)
      }
    }

    async function loadPublicData() {
      try {
        const [songList, maqamList] = await Promise.all([
          api<SongListResponse>('/songs', { query: { page: 1, page_size: 4 } }),
          api<MaqamResponse[]>('/maqamat'),
        ])
        setSongs(songList.items)
        setSongsTotal(songList.total)
        setSongsSection('ready')
        setMaqamat(maqamList)
        setMaqamSection('ready')
      } catch {
        setSongsSection('error')
        setMaqamSection('error')
      }
    }

    loadCurrentUser()
    loadPublicData()
  }, [router])

  // Wait until authentication is checked
  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-sm text-muted-foreground">
          Loading your dashboard...
        </p>
      </div>
    )
  }

  // Prevent dashboard from rendering before redirect
  if (!user) {
    return null
  }

  const firstName = user.name.split(' ')[0]

  const stats = [
    {
      label: 'Songs in library',
      value: songsTotal !== null ? songsTotal.toLocaleString() : '—',
      icon: Library,
    },
    {
      label: 'Maqamat mapped',
      value: maqamSection === 'ready' ? maqamat.length.toLocaleString() : '—',
      icon: Waves,
    },
  ]

  return (
    <div className="mx-auto max-w-6xl">

      {/* Greeting + ask bar */}
      <section className="animate-rise overflow-hidden rounded-2xl border border-gold/20 bg-vignette p-6 md:p-8">

        <p className="text-xs font-semibold tracking-[0.2em] text-gold uppercase">
          {user.instrument || 'Musician'}
          {user.city ? ` · ${user.city}` : ''}
        </p>

        <h1 className="mt-2 font-display text-3xl font-semibold text-balance md:text-4xl">
          Ahlan, {firstName}. What shall we play today?
        </h1>

        <p className="mt-2 max-w-xl text-sm text-muted-foreground md:text-base">
          Ask Nagham for anything — a maqam, a mood, or a song to follow another.
        </p>

        <Link
          href="/assistant"
          className="mt-6 flex items-center gap-3 rounded-xl border border-border bg-background/60 p-3 transition-colors hover:border-gold/40"
        >
          <span className="flex size-9 items-center justify-center rounded-lg bg-gold text-gold-foreground">
            <Sparkles className="size-5" />
          </span>

          <span className="text-sm text-muted-foreground">
            Ask the assistant… “emotional songs in Bayati”
          </span>

          <ArrowRight className="ml-auto size-4 text-muted-foreground" />
        </Link>

        <div className="mt-4 flex flex-wrap gap-2">
          {SUGGESTED_PROMPTS.slice(0, 4).map((prompt) => (
            <Link
              key={prompt}
              href="/assistant"
              className="rounded-full border border-border bg-card/60 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground"
            >
              {prompt}
            </Link>
          ))}
        </div>

      </section>

      {/* Stats */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {stats.map((stat) => (
          <Card
            key={stat.label}
            className="animate-rise-delay-1"
          >
            <CardContent className="flex items-center gap-4 p-5">

              <span className="flex size-11 items-center justify-center rounded-lg border border-gold/25 bg-gold-muted text-gold">
                <stat.icon className="size-5" />
              </span>

              <div>
                <p className="font-display text-2xl font-semibold">
                  {stat.value}
                </p>

                <p className="text-xs text-muted-foreground">
                  {stat.label}
                </p>
              </div>

            </CardContent>
          </Card>
        ))}
      </div>

      {/* Shortcuts */}
      <section className="mt-10">

        <SectionHeading
          eyebrow="Quick start"
          title="Jump back in"
        />

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          {SHORTCUTS.map((shortcut) => (
            <Link
              key={shortcut.href}
              href={shortcut.href}
              className="group rounded-xl border border-border bg-card p-5 transition-all hover:-translate-y-0.5 hover:border-gold/40 hover:bg-surface"
            >

              <span className="flex size-10 items-center justify-center rounded-lg border border-gold/25 bg-gold-muted text-gold transition-colors group-hover:bg-gold group-hover:text-gold-foreground">
                <shortcut.icon className="size-5" />
              </span>

              <h3 className="mt-4 font-display text-lg font-semibold">
                {shortcut.title}
              </h3>

              <p className="mt-1 text-sm text-muted-foreground">
                {shortcut.body}
              </p>

            </Link>
          ))}

        </div>

      </section>

      {/* Recently added songs */}
      <section className="mt-10">

        <SectionHeading
          eyebrow="Library"
          title="Recently added"
          description="Fresh additions to the library."
          actionLabel="See all"
          actionHref="/songs"
        />

        {songsSection === 'loading' && (
          <div className="flex items-center justify-center gap-2 rounded-xl border border-border bg-card py-12 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading songs...
          </div>
        )}

        {songsSection === 'error' && (
          <div className="rounded-xl border border-border bg-card py-12 text-center text-sm text-muted-foreground">
            We could not load songs right now.
          </div>
        )}

        {songsSection === 'ready' && songs.length === 0 && (
          <div className="rounded-xl border border-border bg-card py-12 text-center text-sm text-muted-foreground">
            No songs added yet.
          </div>
        )}

        {songsSection === 'ready' && songs.length > 0 && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

            {songs.map((song) => (
              <SongCard
                key={song.id}
                song={song}
              />
            ))}

          </div>
        )}

      </section>

      {/* Maqamat mapped */}
      <section className="mt-10">

        <SectionHeading
          eyebrow="Explore"
          title="Maqamat mapped"
          actionLabel="Browse songs"
          actionHref="/songs"
        />

        {maqamSection === 'loading' && (
          <div className="flex items-center justify-center gap-2 rounded-xl border border-border bg-card py-12 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading maqamat...
          </div>
        )}

        {maqamSection === 'error' && (
          <div className="rounded-xl border border-border bg-card py-12 text-center text-sm text-muted-foreground">
            We could not load maqamat right now.
          </div>
        )}

        {maqamSection === 'ready' && maqamat.length === 0 && (
          <div className="rounded-xl border border-border bg-card py-12 text-center text-sm text-muted-foreground">
            No maqamat mapped yet.
          </div>
        )}

        {maqamSection === 'ready' && maqamat.length > 0 && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">

            {maqamat.slice(0, 3).map((maqam) => (
              <Link
                key={maqam.id}
                href={`/songs?maqam_id=${maqam.id}`}
                className="group relative flex flex-col gap-2 overflow-hidden rounded-xl border border-border bg-card p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-gold/40 hover:bg-surface"
              >
                <div className="flex items-baseline justify-between">
                  <h3 className="font-display text-xl font-semibold">
                    {maqam.name_en ?? maqam.name_ar}
                  </h3>
                  <span className="font-display text-2xl text-gold/70 transition-colors group-hover:text-gold">
                    {maqam.name_ar}
                  </span>
                </div>
                {maqam.mood && (
                  <p className="text-xs font-medium tracking-wide text-gold/90 uppercase">
                    {maqam.mood}
                  </p>
                )}
                {maqam.description && (
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    {maqam.description}
                  </p>
                )}
                {maqam.tonic && (
                  <span className="mt-2 text-xs text-muted-foreground/80">
                    Tonic · {maqam.tonic}
                  </span>
                )}
              </Link>
            ))}

          </div>
        )}

      </section>

    </div>
  )
}