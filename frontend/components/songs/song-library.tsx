'use client'

import { useEffect, useState } from 'react'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import { api, ApiError } from '@/lib/api'
import type {
  MaqamResponse,
  RhythmResponse,
  SongDifficulty,
  SongListResponse,
  SongResponse,
} from '@/lib/types'
import { SONG_DIFFICULTY_OPTIONS } from '@/lib/difficulty'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { SongCard } from '@/components/song-card'

const PAGE_SIZE = 12
const VALID_DIFFICULTIES: SongDifficulty[] = ['easy', 'medium', 'hard']

function isNumeric(value: string): boolean {
  return /^\d+$/.test(value)
}

function parseDifficulty(value: string | undefined): string {
  return value && (VALID_DIFFICULTIES as string[]).includes(value) ? value : 'all'
}

function clampPage(value: number): number {
  return Number.isInteger(value) && value >= 1 ? value : 1
}

function friendlyApiError(err: unknown): string {
  if (err instanceof ApiError && err.message) return err.message
  return 'Unable to connect to the server. Please check your connection and try again.'
}

export function SongLibrary({
  initialQuery = '',
  initialMaqamId = 'all',
  initialRhythmId = 'all',
  initialDifficulty = 'all',
  initialPage = 1,
}: {
  initialQuery?: string
  initialMaqamId?: string
  initialRhythmId?: string
  initialDifficulty?: string
  initialPage?: number
}) {
  const [query, setQuery] = useState(initialQuery)
  const [maqamId, setMaqamId] = useState(isNumeric(initialMaqamId) ? initialMaqamId : 'all')
  const [rhythmId, setRhythmId] = useState(isNumeric(initialRhythmId) ? initialRhythmId : 'all')
  const [difficulty, setDifficulty] = useState(parseDifficulty(initialDifficulty))
  const [page, setPage] = useState(clampPage(initialPage))

  const [songs, setSongs] = useState<SongResponse[] | null>(null)
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  const [maqamat, setMaqamat] = useState<MaqamResponse[]>([])
  const [rhythms, setRhythms] = useState<RhythmResponse[]>([])
  const [lookupFailed, setLookupFailed] = useState(false)

  useEffect(() => {
    let cancelled = false

    api<MaqamResponse[]>('/maqamat')
      .then((data) => {
        if (!cancelled) setMaqamat(data)
      })
      .catch(() => {
        if (!cancelled) setLookupFailed(true)
      })

    api<RhythmResponse[]>('/rhythms')
      .then((data) => {
        if (!cancelled) setRhythms(data)
      })
      .catch(() => {
        if (!cancelled) setLookupFailed(true)
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    const timeout = window.setTimeout(() => {
      const params = {
        search: query.trim() || undefined,
        maqam_id: isNumeric(maqamId) ? Number(maqamId) : undefined,
        rhythm_id: isNumeric(rhythmId) ? Number(rhythmId) : undefined,
        difficulty: difficulty === 'all' ? undefined : (difficulty as SongDifficulty),
        page,
        page_size: PAGE_SIZE,
      }

      api<SongListResponse>('/songs', { query: params })
        .then((data) => {
          if (cancelled) return
          if (data.pages > 0 && data.page > data.pages) {
            setPage(data.pages)
            return
          }
          setSongs(data.items)
          setTotal(data.total)
          setPages(data.pages)
          setLoading(false)
        })
        .catch((err) => {
          if (cancelled) return
          setError(friendlyApiError(err))
          setLoading(false)
        })
    }, 250)

    return () => {
      cancelled = true
      window.clearTimeout(timeout)
    }
  }, [query, maqamId, rhythmId, difficulty, page, reloadKey])

  useEffect(() => {
    const searchParams = new URLSearchParams()
    if (query) searchParams.set('q', query)
    if (maqamId !== 'all') searchParams.set('maqam_id', maqamId)
    if (rhythmId !== 'all') searchParams.set('rhythm_id', rhythmId)
    if (difficulty !== 'all') searchParams.set('difficulty', difficulty)
    if (page > 1) searchParams.set('page', String(page))
    const qs = searchParams.toString()
    window.history.replaceState(null, '', qs ? `/songs?${qs}` : '/songs')
  }, [query, maqamId, rhythmId, difficulty, page])

  useEffect(() => {
    setQuery((prev) => (prev !== initialQuery ? initialQuery : prev))
    const normMaqam = isNumeric(initialMaqamId) ? initialMaqamId : 'all'
    setMaqamId((prev) => (prev !== normMaqam ? normMaqam : prev))
    const normRhythm = isNumeric(initialRhythmId) ? initialRhythmId : 'all'
    setRhythmId((prev) => (prev !== normRhythm ? normRhythm : prev))
    const normDifficulty = parseDifficulty(initialDifficulty)
    setDifficulty((prev) => (prev !== normDifficulty ? normDifficulty : prev))
    const normPage = clampPage(initialPage)
    setPage((prev) => (prev !== normPage ? normPage : prev))
  }, [initialQuery, initialMaqamId, initialRhythmId, initialDifficulty, initialPage])

  const selectedMaqam = maqamat.find((m) => String(m.id) === maqamId)
  const hasFilters = query !== '' || maqamId !== 'all' || rhythmId !== 'all' || difficulty !== 'all'

  function clear() {
    setQuery('')
    setMaqamId('all')
    setRhythmId('all')
    setDifficulty('all')
    setPage(1)
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[260px_1fr]">
      {/* Filters */}
      <aside className="lg:sticky lg:top-24 lg:self-start">
        <div className="rounded-2xl border border-border bg-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <SlidersHorizontal className="size-4 text-gold" />
            <h2 className="font-display text-lg font-semibold">Filters</h2>
            {hasFilters && (
              <button
                onClick={clear}
                className="ml-auto flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <X className="size-3.5" /> Clear
              </button>
            )}
          </div>

          <div className="flex flex-col gap-4">
            <div>
              <Label htmlFor="f-search">Search</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="f-search"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value)
                    setPage(1)
                  }}
                  placeholder="Title, artist…"
                  className="pl-9"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="f-maqam">Maqam</Label>
              <Select
                id="f-maqam"
                value={maqamId}
                onChange={(e) => {
                  setMaqamId(e.target.value)
                  setPage(1)
                }}
              >
                <option value="all">All maqamat</option>
                {maqamat.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name_ar || m.name_en || `Maqam ${m.id}`}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="f-rhythm">Rhythm</Label>
              <Select
                id="f-rhythm"
                value={rhythmId}
                onChange={(e) => {
                  setRhythmId(e.target.value)
                  setPage(1)
                }}
              >
                <option value="all">All rhythms</option>
                {rhythms.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name_ar || r.name_en || `Rhythm ${r.id}`}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="f-diff">Difficulty</Label>
              <Select
                id="f-diff"
                value={difficulty}
                onChange={(e) => {
                  setDifficulty(e.target.value)
                  setPage(1)
                }}
              >
                <option value="all">Any level</option>
                {SONG_DIFFICULTY_OPTIONS.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </Select>
            </div>
            {lookupFailed && (
              <p className="text-xs text-muted-foreground">
                Some filter options could not be loaded.
              </p>
            )}
          </div>
        </div>
      </aside>

      {/* Results */}
      <div>
        <p className="mb-5 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{total}</span>{' '}
          {total === 1 ? 'song' : 'songs'}
          {selectedMaqam && (
            <> in Maqam {selectedMaqam.name_ar || selectedMaqam.name_en}</>
          )}
        </p>

        {error ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center">
            <p className="font-display text-xl font-semibold">Could not load songs</p>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">{error}</p>
            <button
              onClick={() => setReloadKey((k) => k + 1)}
              className="mt-4 rounded-lg border border-gold/30 bg-gold-muted px-4 py-2 text-sm font-medium text-gold hover:bg-gold hover:text-gold-foreground"
            >
              Try again
            </button>
          </div>
        ) : loading && !songs ? (
          <div className="flex items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center">
            <p className="text-sm text-muted-foreground">Loading songs…</p>
          </div>
        ) : songs && songs.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center">
            <p className="font-display text-xl font-semibold">No songs match your filters</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Try broadening your search or clearing filters.
            </p>
            <button
              onClick={clear}
              className="mt-4 rounded-lg border border-gold/30 bg-gold-muted px-4 py-2 text-sm font-medium text-gold hover:bg-gold hover:text-gold-foreground"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <>
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {songs?.map((s) => (
                <SongCard key={s.id} song={s} />
              ))}
            </div>

            {pages > 1 && (
              <nav className="mt-8 flex items-center justify-center gap-3">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {pages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(pages, p + 1))}
                  disabled={page >= pages}
                  className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                </button>
              </nav>
            )}
          </>
        )}
      </div>
    </div>
  )
}