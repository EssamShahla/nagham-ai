'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { PlusCircle, Loader2, AlertCircle } from 'lucide-react'
import { api, ApiError, formatValidationError } from '@/lib/api'
import { useSongLookups } from '@/lib/use-song-lookups'
import { SongFields, EMPTY_SONG_FORM, type SongFormValues } from '@/components/songs/song-fields'
import type { SongResponse } from '@/lib/types'
import { SectionHeading } from '@/components/section-heading'

const CURRENT_YEAR = new Date().getFullYear()

export default function AddSongPage() {
  const router = useRouter()
  const { lookups, loading, error: lookupError, retry } = useSongLookups()

  const [values, setValues] = useState<SongFormValues>(EMPTY_SONG_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl">
        <SectionHeading
          eyebrow="Contribute"
          title="Add a song"
          description="Help grow the archive. Provide the song details so the AI can recommend it accurately."
        />
        <div className="flex items-center justify-center gap-3 rounded-2xl border border-border bg-card py-20 text-center">
          <Loader2 className="size-5 animate-spin text-gold" />
          <span className="text-sm text-muted-foreground">Loading data…</span>
        </div>
      </div>
    )
  }

  if (lookupError) {
    return (
      <div className="mx-auto max-w-3xl">
        <SectionHeading
          eyebrow="Contribute"
          title="Add a song"
          description="Help grow the archive. Provide the song details so the AI can recommend it accurately."
        />
        <div className="flex flex-col items-center rounded-2xl border border-border bg-card py-20 text-center">
          <AlertCircle className="size-8 text-gold" />
          <h2 className="mt-4 font-display text-xl font-semibold">Could not load reference data</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">{lookupError}</p>
          <button
            onClick={retry}
            className="mt-5 rounded-lg bg-gold px-5 py-2.5 text-sm font-medium text-gold-foreground transition-colors hover:bg-gold/90"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (submitting) return

    setError(null)

    if (!values.artistId) {
      setError('Please select an artist.')
      return
    }

    const yearTrimmed = values.year.trim()
    let parsedYear: number | null = null
    if (yearTrimmed !== '') {
      const n = Number(yearTrimmed)
      if (!Number.isInteger(n) || n < 1800 || n > CURRENT_YEAR) {
        setError(`Year must be between 1800 and ${CURRENT_YEAR}.`)
        return
      }
      parsedYear = n
    }

    const payload = {
      title: values.title.trim(),
      lyrics: values.lyrics.trim() || null,
      year: parsedYear,
      difficulty: (values.difficulty as 'easy' | 'medium' | 'hard') || null,
      artist_id: Number(values.artistId),
      composer_id: values.composerId ? Number(values.composerId) : null,
      maqam_id: values.maqamId ? Number(values.maqamId) : null,
      rhythm_id: values.rhythmId ? Number(values.rhythmId) : null,
    }

    setSubmitting(true)
    try {
      const created = await api<SongResponse>('/songs', { method: 'POST', body: payload, auth: true })
      router.push(`/songs/${created.id}`)
    } catch (err) {
      if (err instanceof ApiError) {
        switch (err.status) {
          case 401:
            setError('You need to be logged in to add a song.')
            window.setTimeout(() => router.push('/login'), 1500)
            return
          case 409:
            setError('This song already exists in the library.')
            return
          case 404:
            setError('A selected reference no longer exists. Refresh the page and try again.')
            return
          case 422:
            setError(formatValidationError(err.detail))
            return
          default:
            setError(typeof err.detail === 'string' ? err.detail : `Something went wrong (status ${err.status}). Please try again.`)
        }
      } else {
        setError('Could not reach the server. Check your connection and try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <SectionHeading
        eyebrow="Contribute"
        title="Add a song"
        description="Help grow the archive. Provide the song details so the AI can recommend it accurately."
      />

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {error && (
          <div role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-5 py-4 text-sm text-rose-400">
            {error}
          </div>
        )}

        <SongFields lookups={lookups!} values={values} onChange={setValues} disabled={submitting} />

        <div className="flex flex-wrap items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => { setValues(EMPTY_SONG_FORM); setError(null) }}
            disabled={submitting}
            className="rounded-lg border border-border px-5 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
          >
            Reset
          </button>
          <button
            type="submit"
            disabled={submitting || lookups!.artists.length === 0}
            className="flex items-center gap-2 rounded-lg bg-gold px-5 py-2.5 text-sm font-medium text-gold-foreground transition-colors hover:bg-gold/90 disabled:opacity-50"
          >
            {submitting ? (
              <><Loader2 className="size-4 animate-spin" /> Submitting…</>
            ) : (
              <><PlusCircle className="size-4" /> Submit song</>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}