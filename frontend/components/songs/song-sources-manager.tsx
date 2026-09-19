'use client'

import { useEffect, useState } from 'react'
import { Plus, Trash2, ExternalLink, Loader2 } from 'lucide-react'
import { api, ApiError } from '@/lib/api'
import type { SongSourceResponse, UserResponse } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

const SOURCE_TYPE_OPTIONS = [
  { value: 'website', label: 'Website' },
  { value: 'book', label: 'Book' },
  { value: 'article', label: 'Article' },
  { value: 'database', label: 'Database' },
  { value: 'user_contribution', label: 'User contribution' },
  { value: 'other', label: 'Other' },
] as const

const TYPE_LABELS: Record<string, string> = Object.fromEntries(
  SOURCE_TYPE_OPTIONS.map((o) => [o.value, o.label]),
)

interface Props {
  songId: number
  createdBy: number
  initialSources: SongSourceResponse[]
}

export function SongSourcesManager({ songId, createdBy, initialSources }: Props) {
  const [sources, setSources] = useState<SongSourceResponse[]>(initialSources)
  const [canManage, setCanManage] = useState(false)
  const [checked, setChecked] = useState(false)
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null)

  const [showForm, setShowForm] = useState(false)
  const [srcType, setSrcType] = useState('website')
  const [srcTitle, setSrcTitle] = useState('')
  const [srcUrl, setSrcUrl] = useState('')
  const [srcDesc, setSrcDesc] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function check() {
      let token: string | null = null
      try {
        token = window.localStorage.getItem('access_token')
      } catch {}
      if (!token) {
        setChecked(true)
        return
      }
      try {
        const me = await api<UserResponse>('/auth/me', { auth: true })
        if (!cancelled) {
          setCurrentUser(me)
          setCanManage(me.id === createdBy || me.role === 'admin')
        }
      } catch {}
      if (!cancelled) setChecked(true)
    }
    check()
    return () => {
      cancelled = true
    }
  }, [createdBy])

  function canDeleteSource(source: SongSourceResponse): boolean {
    if (!checked || !currentUser) return false
    return canManage || currentUser.id === source.created_by
  }

  async function handleAddSource(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (submitting) return

    setSubmitError(null)

    const payload = {
      source_type: srcType as SongSourceResponse['source_type'],
      title: srcTitle.trim() || null,
      source_url: srcUrl.trim() || null,
      description: srcDesc.trim() || null,
    }

    setSubmitting(true)
    try {
      const created = await api<SongSourceResponse>(`/songs/${songId}/sources`, {
        method: 'POST',
        body: payload,
        auth: true,
      })
      setSources((prev) => [created, ...prev])
      setSrcTitle('')
      setSrcUrl('')
      setSrcDesc('')
      setShowForm(false)
    } catch (err) {
      if (err instanceof ApiError) {
        switch (err.status) {
          case 401:
            setSubmitError('You need to be logged in to add a source.')
            break
          case 403:
            setSubmitError('You do not have permission to add sources to this song.')
            break
          case 404:
            setSubmitError('This song no longer exists.')
            break
          case 409:
            setSubmitError('This source URL has already been added for this song.')
            break
          case 422:
            setSubmitError(typeof err.detail === 'string' ? err.detail : 'Please check the form and try again.')
            break
          default:
            setSubmitError('Something went wrong. Please try again.')
        }
      } else {
        setSubmitError('Could not reach the server. Check your connection and try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDeleteSource(sourceId: number) {
    if (deletingId !== null) return

    setDeleteError(null)
    setDeletingId(sourceId)
    try {
      await api<undefined>(`/songs/${songId}/sources/${sourceId}`, {
        method: 'DELETE',
        auth: true,
      })
      setSources((prev) => prev.filter((s) => s.id !== sourceId))
      setDeletingId(null)
    } catch (err) {
      if (err instanceof ApiError) {
        switch (err.status) {
          case 401:
            setDeleteError('You need to be logged in to delete sources.')
            break
          case 403:
            setDeleteError('You do not have permission to delete this source.')
            break
          case 404:
            setDeleteError('This source no longer exists.')
            setSources((prev) => prev.filter((s) => s.id !== sourceId))
            break
          default:
            setDeleteError('Something went wrong. Please try again.')
        }
      } else {
        setDeleteError('Could not reach the server. Check your connection and try again.')
      }
      setDeletingId(null)
    }
  }

  return (
    <section>
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-display text-xl font-semibold">Sources</h2>
        {checked && canManage && !showForm && (
          <button
            type="button"
            onClick={() => { setShowForm(true); setSubmitError(null) }}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gold/30 bg-gold-muted px-3 py-1.5 text-xs font-medium text-gold transition-colors hover:bg-gold-muted/80"
          >
            <Plus className="size-3.5" /> Add a source
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleAddSource} className="mt-4 rounded-xl border border-border bg-card p-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="src-type">Source type</Label>
              <Select
                id="src-type"
                value={srcType}
                onChange={(e) => setSrcType(e.target.value)}
                disabled={submitting}
              >
                {SOURCE_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="src-title">Title</Label>
              <Input
                id="src-title"
                placeholder="e.g. Arabic Music Archive"
                value={srcTitle}
                onChange={(e) => setSrcTitle(e.target.value)}
                disabled={submitting}
              />
            </div>
            <div className="sm:col-span-2">
              <Label htmlFor="src-url">URL</Label>
              <Input
                id="src-url"
                type="url"
                placeholder="https://example.com/reference"
                value={srcUrl}
                onChange={(e) => setSrcUrl(e.target.value)}
                disabled={submitting}
              />
            </div>
            <div className="sm:col-span-2">
              <Label htmlFor="src-desc">Description</Label>
              <Textarea
                id="src-desc"
                placeholder="A brief note about this source…"
                className="min-h-20"
                value={srcDesc}
                onChange={(e) => setSrcDesc(e.target.value)}
                disabled={submitting}
              />
            </div>
          </div>
          {submitError && (
            <p role="alert" className="mt-3 rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-xs text-rose-400">
              {submitError}
            </p>
          )}
          <div className="mt-4 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => { setShowForm(false); setSubmitError(null) }}
              disabled={submitting}
              className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-1.5 rounded-lg bg-gold px-3.5 py-1.5 text-xs font-medium text-gold-foreground transition-colors hover:bg-gold/90 disabled:opacity-50"
            >
              {submitting ? (
                <><Loader2 className="size-3.5 animate-spin" /> Saving…</>
              ) : (
                <><Plus className="size-3.5" /> Add source</>
              )}
            </button>
          </div>
        </form>
      )}

      {deleteError && (
        <p role="alert" className="mt-3 rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-xs text-rose-400">
          {deleteError}
        </p>
      )}

      {sources.length > 0 ? (
        <div className="mt-3 flex flex-col gap-2">
          {sources.map((s) => (
            <div
              key={s.id}
              className="group/source rounded-lg border border-border bg-card px-4 py-3 text-sm"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-medium">{s.title ?? 'Source'}</p>
                  <p className="text-xs text-muted-foreground">
                    {TYPE_LABELS[s.source_type] ?? s.source_type}
                    {s.description ? ` · ${s.description}` : ''}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {s.source_url ? (
                    <a
                      href={s.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-gold transition-colors hover:underline"
                    >
                      Visit <ExternalLink className="size-3.5" />
                    </a>
                  ) : null}
                  {checked && canDeleteSource(s) && (
                    deletingId === s.id ? (
                      <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleDeleteSource(s.id)}
                        className="inline-flex items-center gap-1 rounded border border-rose-400/30 bg-rose-400/10 px-1.5 py-0.5 text-[11px] font-medium text-rose-400 opacity-0 transition-opacity group-hover/source:opacity-100 hover:bg-rose-400/20"
                      >
                        <Trash2 className="size-3" /> Delete
                      </button>
                    )
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">No sources available</p>
      )}
    </section>
  )
}