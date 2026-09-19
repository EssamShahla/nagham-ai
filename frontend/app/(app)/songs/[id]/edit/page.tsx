'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Loader2, AlertCircle, Save } from 'lucide-react'
import { api, ApiError, formatValidationError } from '@/lib/api'
import { useSongLookups } from '@/lib/use-song-lookups'
import { SongFields, EMPTY_SONG_FORM, type SongFormValues } from '@/components/songs/song-fields'
import type { SongResponse, UserResponse } from '@/lib/types'
import { SectionHeading } from '@/components/section-heading'
import { ButtonLink } from '@/components/ui/button-link'

const CURRENT_YEAR = new Date().getFullYear()

type EditStatus = 'loading' | 'unauth' | 'forbidden' | 'not-found' | 'error' | 'ready'

export default function EditSongPage() {
  const router = useRouter()
  const params = useParams()
  const id = (Array.isArray(params.id) ? params.id[0] : params.id) ?? ''

  const { lookups, loading: lookupsLoading, error: lookupError, retry } = useSongLookups()

  const [status, setStatus] = useState<EditStatus>('loading')
  const [songId, setSongId] = useState<number | null>(null)
  const [values, setValues] = useState<SongFormValues>(EMPTY_SONG_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      if (!/^\d+$/.test(id)) {
        setStatus('not-found')
        return
      }
      const numericId = Number(id)
      if (!Number.isSafeInteger(numericId)) {
        setStatus('not-found')
        return
      }

      let token: string | null = null
      try {
        token = window.localStorage.getItem('access_token')
      } catch {}

      if (!token) {
        setStatus('unauth')
        return
      }

      try {
        const [me, song] = await Promise.all([
          api<UserResponse>('/auth/me', { auth: true }),
          api<SongResponse>(`/songs/${numericId}`),
        ])
        if (cancelled) return
        if (!(me.id === song.created_by || me.role === 'admin')) {
          setStatus('forbidden')
          return
        }
        setSongId(numericId)
        setValues({
          title: song.title,
          artistId: String(song.artist_id),
          composerId: song.composer_id != null ? String(song.composer_id) : '',
          year: song.year != null ? String(song.year) : '',
          difficulty: song.difficulty ?? '',
          maqamId: song.maqam_id != null ? String(song.maqam_id) : '',
          rhythmId: song.rhythm_id != null ? String(song.rhythm_id) : '',
          lyrics: song.lyrics ?? '',
        })
        setStatus('ready')
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          setStatus('unauth')
          return
        }
        if (err instanceof ApiError && err.status === 404) {
          setStatus('not-found')
          return
        }
        setStatus('error')
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [id])

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (submitting || songId === null) return

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
      await api<SongResponse>(`/songs/${songId}`, { method: 'PATCH', body: payload, auth: true })
      router.push(`/songs/${songId}`)
      router.refresh()
    } catch (err) {
      if (err instanceof ApiError) {
        switch (err.status) {
          case 401:
            setError('Your session has expired. Please log in again.')
            window.setTimeout(() => router.push('/login'), 1500)
            return
          case 403:
            setError('You do not have permission to edit this song.')
            return
          case 404:
            setError('This song no longer exists.')
            return
          case 409:
            setError('Another song with this title and artist already exists.')
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

  const backLink = (label: string, href: string) => (
    <Link
      href={href}
      className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
    >
      <ArrowLeft className="size-4" /> {label}
    </Link>
  )

  const centerCard = (title: string, message: string, cta?: React.ReactNode) => (
    <div className="mx-auto max-w-3xl">
      {backLink('Back', '/songs')}
      <div className="flex flex-col items-center rounded-2xl border border-border bg-card py-20 text-center">
        <AlertCircle className="size-8 text-gold" />
        <h2 className="mt-4 font-display text-xl font-semibold">{title}</h2>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">{message}</p>
        {cta}
      </div>
    </div>
  )

  if (status === 'unauth') {
    return centerCard(
      'Sign in required',
      'You need to be logged in to edit a song.',
      <ButtonLink href="/login" className="mt-6">
        Log in
      </ButtonLink>,
    )
  }

  if (status === 'forbidden') {
    return centerCard(
      'No access',
      'You do not have permission to edit this song.',
      <ButtonLink href={`/songs/${id}`} className="mt-6" variant="outline">
        View song
      </ButtonLink>,
    )
  }

  if (status === 'not-found') {
    return centerCard('Song not found', 'The song you are trying to edit does not exist.')
  }

  if (status === 'error') {
    return centerCard(
      'Something went wrong',
      'We could not load this song right now. Please try again in a moment.',
      <ButtonLink href={`/songs/${id}`} className="mt-6" variant="outline">
        Back to song
      </ButtonLink>,
    )
  }

  return (
    <div className="mx-auto max-w-3xl">
      {backLink(`Back to song`, `/songs/${id}`)}
      <SectionHeading
        eyebrow="Manage"
        title="Edit song"
        description="Update the song details. Changes appear on the public detail page immediately."
      />

      {status === 'loading' || lookupsLoading || !lookups ? (
        <div className="flex items-center justify-center gap-3 rounded-2xl border border-border bg-card py-20 text-center">
          <Loader2 className="size-5 animate-spin text-gold" />
          <span className="text-sm text-muted-foreground">Loading song…</span>
        </div>
      ) : lookupError ? (
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
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          {error && (
            <div
              role="alert"
              className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-5 py-4 text-sm text-rose-400"
            >
              {error}
            </div>
          )}

          <SongFields lookups={lookups} values={values} onChange={setValues} disabled={submitting} />

          <div className="flex flex-wrap items-center justify-end gap-3">
            <ButtonLink href={`/songs/${id}`} variant="outline">
              Cancel
            </ButtonLink>
            <button
              type="submit"
              disabled={submitting || lookups.artists.length === 0}
              className="flex items-center gap-2 rounded-lg bg-gold px-5 py-2.5 text-sm font-medium text-gold-foreground transition-colors hover:bg-gold/90 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Saving…
                </>
              ) : (
                <>
                  <Save className="size-4" /> Save changes
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}