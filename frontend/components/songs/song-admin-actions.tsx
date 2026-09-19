'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Pencil, Trash2, Loader2 } from 'lucide-react'
import { api, ApiError } from '@/lib/api'
import type { UserResponse } from '@/lib/types'
import { ButtonLink } from '@/components/ui/button-link'

export function SongAdminActions({
  songId,
  createdBy,
  songTitle,
}: {
  songId: number
  createdBy: number
  songTitle: string
}) {
  const router = useRouter()
  const [canManage, setCanManage] = useState(false)
  const [checked, setChecked] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
        if (!cancelled) setCanManage(me.id === createdBy || me.role === 'admin')
      } catch {}
      if (!cancelled) setChecked(true)
    }
    check()
    return () => {
      cancelled = true
    }
  }, [createdBy])

  if (!checked) return null

  if (!canManage) return null

  async function confirmDelete() {
    if (deleting) return
    setDeleting(true)
    setError(null)
    try {
      await api<undefined>(`/songs/${songId}`, { method: 'DELETE', auth: true })
      setConfirmOpen(false)
      router.push('/songs')
      router.refresh()
    } catch (err) {
      if (err instanceof ApiError) {
        switch (err.status) {
          case 401:
            setError('You need to be logged in to delete this song.')
            break
          case 403:
            setError('You do not have permission to delete this song.')
            break
          case 404:
            setError('This song no longer exists.')
            break
          default:
            setError('Something went wrong. Please try again.')
        }
      } else {
        setError('Could not reach the server. Check your connection and try again.')
      }
    } finally {
      setDeleting(false)
    }
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <ButtonLink
          href={`/songs/${songId}/edit`}
          variant="outline"
          size="sm"
          className="gap-1.5"
        >
          <Pencil className="size-3.5" /> Edit
        </ButtonLink>
        <button
          type="button"
          onClick={() => {
            setError(null)
            setConfirmOpen(true)
          }}
          className="inline-flex items-center gap-1.5 rounded-lg border border-rose-400/40 bg-rose-400/10 px-2.5 py-1.5 text-sm font-medium text-rose-400 transition-colors hover:bg-rose-400/20"
        >
          <Trash2 className="size-3.5" /> Delete
        </button>
      </div>

      {confirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-song-title"
        >
          <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-lg">
            <h3 id="delete-song-title" className="font-display text-lg font-semibold">
              Delete this song?
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              “{songTitle}” and all of its sources will be permanently deleted. This action cannot be
              undone.
            </p>
            {error && (
              <p
                role="alert"
                className="mt-3 rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-400"
              >
                {error}
              </p>
            )}
            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setConfirmOpen(false)}
                disabled={deleting}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                disabled={deleting}
                className="inline-flex items-center gap-2 rounded-lg bg-rose-400/15 px-4 py-2 text-sm font-medium text-rose-400 transition-colors hover:bg-rose-400/25 disabled:opacity-50"
              >
                {deleting ? (
                  <>
                    <Loader2 className="size-4 animate-spin" /> Deleting…
                  </>
                ) : (
                  'Delete song'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}