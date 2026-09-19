import Link from 'next/link'
import { notFound } from 'next/navigation'
import {
  ArrowLeft,
  Music2,
  Sparkles,
  Clock,
  User,
  Gauge,
  Waves,
} from 'lucide-react'
import { api, ApiError } from '@/lib/api'
import type { SongResponse, SongSourceResponse } from '@/lib/types'
import { difficultyLabel } from '@/lib/difficulty'
import { Badge } from '@/components/ui/badge'
import { DifficultyDot } from '@/components/song-card'
import { ButtonLink } from '@/components/ui/button-link'
import { SongAdminActions } from '@/components/songs/song-admin-actions'
import { SongSourcesManager } from '@/components/songs/song-sources-manager'

export const dynamic = 'force-dynamic'

function parseSongId(value: string): number | null {
  if (!/^\d+$/.test(value)) return null
  const id = Number(value)
  if (!Number.isSafeInteger(id)) return null
  return id
}

type SongLoadResult =
  | { ok: true; song: SongResponse }
  | { ok: false; reason: 'not-found' | 'error' }

async function loadSong(id: number): Promise<SongLoadResult> {
  try {
    const song = await api<SongResponse>(`/songs/${id}`)
    return { ok: true, song }
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return { ok: false, reason: 'not-found' }
    }
    return { ok: false, reason: 'error' }
  }
}

async function fetchSources(id: number): Promise<SongSourceResponse[]> {
  try {
    return await api<SongSourceResponse[]>(`/songs/${id}/sources`)
  } catch {
    return []
  }
}

export default async function SongDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const songId = parseSongId(id)
  if (songId === null) notFound()

  const result = await loadSong(songId)
  if (!result.ok) {
    if (result.reason === 'not-found') notFound()
    return (
      <div className="mx-auto max-w-5xl">
        <Link
          href="/songs"
          className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-4" /> Back to library
        </Link>

        <div className="flex flex-col items-center justify-center rounded-2xl border border-border bg-card py-20 text-center">
          <Music2 className="size-8 text-gold" />
          <h2 className="mt-4 font-display text-2xl font-semibold">Something went wrong</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            We could not load this song right now. Please try again in a moment.
          </p>
          <ButtonLink href="/songs" className="mt-6">
            Back to library
          </ButtonLink>
        </div>
      </div>
    )
  }

  const song = result.song
  const sources = await fetchSources(songId)

  const meta = [
    { icon: User, label: 'Composer', value: song.composer_name },
    { icon: Clock, label: 'Year', value: song.year !== null && song.year !== undefined ? String(song.year) : null },
    { icon: Waves, label: 'Rhythm', value: song.rhythm_name },
    { icon: Music2, label: 'Maqam', value: song.maqam_name },
  ].filter((m) => m.value !== null && m.value !== undefined && m.value !== '')

  const difficulty = difficultyLabel(song.difficulty)

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Link
          href="/songs"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-4" /> Back to library
        </Link>
        <SongAdminActions songId={song.id} createdBy={song.created_by} songTitle={song.title} />
      </div>

      {/* Hero */}
      <div className="overflow-hidden rounded-2xl border border-gold/20 bg-vignette p-6 md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              {song.maqam_name ? <Badge variant="gold">{song.maqam_name}</Badge> : null}
              {difficulty ? (
                <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Gauge className="size-3.5" />
                  <DifficultyDot level={song.difficulty} />
                  {difficulty}
                </span>
              ) : null}
            </div>
            <h1 className="mt-3 font-display text-4xl font-semibold text-balance">{song.title}</h1>
            <p className="mt-2 flex items-center gap-1.5 text-muted-foreground">
              <User className="size-4" />
              {song.artist_name}
            </p>
          </div>
          <span className="flex size-16 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
            <Music2 className="size-8" />
          </span>
        </div>

        {meta.length > 0 && (
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {meta.map((m) => (
              <div key={m.label} className="rounded-xl border border-border bg-background/50 p-4">
                <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <m.icon className="size-3.5" />
                  {m.label}
                </p>
                <p className="mt-1 font-medium">{m.value}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_300px]">
        <div className="flex flex-col gap-8">
          {/* Lyrics */}
          <section>
            <h2 className="font-display text-xl font-semibold">Lyrics</h2>
            {song.lyrics?.trim() ? (
              <blockquote className="mt-3 rounded-xl border border-border bg-card p-4">
                <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-line">
                  {song.lyrics}
                </p>
              </blockquote>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">No lyrics available</p>
            )}
          </section>

          {/* Sources */}
          <SongSourcesManager
            songId={song.id}
            createdBy={song.created_by}
            initialSources={sources}
          />
        </div>

        {/* Sidebar: ask */}
        <aside className="flex flex-col gap-6">
          <div className="rounded-2xl border border-gold/20 bg-gold-muted/40 p-5">
            <Sparkles className="size-6 text-gold" />
            <h3 className="mt-3 font-display text-lg font-semibold">Ask about this song</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              What can I play after {song.title}? Ask Nagham for smooth transitions.
            </p>
            <ButtonLink href="/assistant" className="mt-4 h-10 w-full text-sm">
              Ask the assistant
            </ButtonLink>
          </div>
        </aside>
      </div>
    </div>
  )
}