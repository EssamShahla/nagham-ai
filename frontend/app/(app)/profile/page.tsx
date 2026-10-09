'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  MapPin,
  Music,
  Mail,
  Pencil,
  Check,
  X,
  Award,
  Guitar,
  CalendarClock,
  Loader2,
} from 'lucide-react'
import { api, ApiError, formatValidationError } from '@/lib/api'
import type { SongListResponse, SongResponse, UserResponse } from '@/lib/types'
import { SongCard } from '@/components/song-card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { SectionHeading } from '@/components/section-heading'

type ProfileForm = {
  name: string
  bio: string
  instrument: string
  city: string
  country: string
}

function toForm(user: UserResponse): ProfileForm {
  return {
    name: user.name,
    bio: user.bio ?? '',
    instrument: user.instrument ?? '',
    city: user.city ?? '',
    country: user.country ?? '',
  }
}

export default function ProfilePage() {
  const router = useRouter()
  const [user, setUser] = useState<UserResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<ProfileForm>({
    name: '',
    bio: '',
    instrument: '',
    city: '',
    country: '',
  })
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [contributions, setContributions] = useState<SongResponse[]>([])
  const [contributionsTotal, setContributionsTotal] = useState<number | null>(null)
  const [contributionsState, setContributionsState] = useState<'loading' | 'ready' | 'error'>(
    'loading',
  )

  useEffect(() => {
    let cancelled = false

    async function loadCurrentUser() {
      const token = localStorage.getItem('access_token')

      if (!token) {
        router.replace('/login')
        return
      }

      try {
        const me = await api<UserResponse>('/auth/me', { auth: true })
        if (cancelled) return
        setUser(me)

        api<SongListResponse>('/songs', { query: { created_by: me.id, page_size: 3 } })
          .then((data) => {
            if (cancelled) return
            setContributions(data.items)
            setContributionsTotal(data.total)
            setContributionsState('ready')
          })
          .catch(() => {
            if (!cancelled) setContributionsState('error')
          })
      } catch {
        localStorage.removeItem('access_token')
        router.replace('/login')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadCurrentUser()
    return () => {
      cancelled = true
    }
  }, [router])

  if (loading || !user) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading your profile...</p>
      </div>
    )
  }

  const initials = (user.name || '?')
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  const stats = [
    { icon: Guitar, label: 'Instrument', value: user.instrument || '—' },
    {
      icon: Award,
      label: 'Contributions',
      value: contributionsTotal !== null ? String(contributionsTotal) : '—',
    },
    {
      icon: CalendarClock,
      label: 'Experience',
      value:
        user.years_of_experience !== null && user.years_of_experience !== undefined
          ? `${user.years_of_experience} years`
          : '—',
    },
  ]

  function startEditing() {
    if (!user) return
    setDraft(toForm(user))
    setSaveError(null)
    setEditing(true)
  }

  function cancel() {
    setSaveError(null)
    setEditing(false)
  }

  async function save() {
    if (saving) return
    setSaving(true)
    setSaveError(null)

    try {
      const updated = await api<UserResponse>('/auth/me', {
        method: 'PATCH',
        auth: true,
        body: {
          name: draft.name.trim(),
          bio: draft.bio.trim() || null,
          instrument: draft.instrument.trim() || null,
          city: draft.city.trim() || null,
          country: draft.country.trim() || null,
        },
      })
      setUser(updated)
      setEditing(false)
    } catch (err) {
      if (err instanceof ApiError) {
        setSaveError(err.status === 422 ? formatValidationError(err.detail) : err.message)
      } else {
        setSaveError('Could not reach the server. Check your connection and try again.')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      {/* Header card */}
      <div className="overflow-hidden rounded-2xl border border-gold/20 bg-vignette">
        <div className="h-28 bg-gradient-to-r from-gold/20 via-gold/5 to-transparent" />
        <div className="px-6 pb-6 md:px-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="flex items-end gap-4">
              <span className="-mt-10 flex size-24 items-center justify-center rounded-2xl border-4 border-background bg-gold font-display text-3xl font-semibold text-gold-foreground">
                {initials}
              </span>
              <div className="pb-1">
                <h1 className="font-display text-3xl font-semibold">{user.name}</h1>
                <p className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Music className="size-4" /> {user.music_role || user.instrument || 'Musician'}
                  </span>
                  {(user.city || user.country) && (
                    <span className="flex items-center gap-1.5">
                      <MapPin className="size-4" />
                      {[user.city, user.country].filter(Boolean).join(', ')}
                    </span>
                  )}
                  <span className="flex items-center gap-1.5">
                    <Mail className="size-4" /> {user.email}
                  </span>
                </p>
              </div>
            </div>
            {!editing && (
              <button
                onClick={startEditing}
                className="flex items-center gap-2 rounded-lg border border-gold/30 bg-gold-muted px-4 py-2 text-sm font-medium text-gold transition-colors hover:bg-gold hover:text-gold-foreground"
              >
                <Pencil className="size-4" /> Edit profile
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <div
            key={s.label}
            className="flex items-center gap-4 rounded-xl border border-border bg-card p-5"
          >
            <span className="flex size-11 items-center justify-center rounded-lg border border-gold/25 bg-gold-muted text-gold">
              <s.icon className="size-5" />
            </span>
            <div>
              <p className="font-display text-xl font-semibold">{s.value}</p>
              <p className="text-xs text-muted-foreground">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* About / edit */}
      <div className="mt-6 rounded-2xl border border-border bg-card p-6">
        {editing ? (
          <div className="flex flex-col gap-5">
            <h2 className="font-display text-xl font-semibold">Edit profile</h2>

            {saveError && (
              <div role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-5 py-4 text-sm text-rose-400">
                {saveError}
              </div>
            )}

            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <Label htmlFor="p-name">Name</Label>
                <Input
                  id="p-name"
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                  disabled={saving}
                />
              </div>
              <div>
                <Label htmlFor="p-instrument">Instrument</Label>
                <Input
                  id="p-instrument"
                  value={draft.instrument}
                  onChange={(e) => setDraft({ ...draft, instrument: e.target.value })}
                  disabled={saving}
                />
              </div>
              <div>
                <Label htmlFor="p-city">City</Label>
                <Input
                  id="p-city"
                  value={draft.city}
                  onChange={(e) => setDraft({ ...draft, city: e.target.value })}
                  disabled={saving}
                />
              </div>
              <div>
                <Label htmlFor="p-country">Country</Label>
                <Input
                  id="p-country"
                  value={draft.country}
                  onChange={(e) => setDraft({ ...draft, country: e.target.value })}
                  disabled={saving}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="p-bio">Bio</Label>
              <Textarea
                id="p-bio"
                value={draft.bio}
                onChange={(e) => setDraft({ ...draft, bio: e.target.value })}
                disabled={saving}
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={cancel}
                disabled={saving}
                className="flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground disabled:opacity-50"
              >
                <X className="size-4" /> Cancel
              </button>
              <button
                onClick={save}
                disabled={saving || !draft.name.trim()}
                className="flex items-center gap-2 rounded-lg bg-gold px-4 py-2 text-sm font-medium text-gold-foreground hover:bg-gold/90 disabled:opacity-50"
              >
                {saving ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Check className="size-4" />
                )}
                Save changes
              </button>
            </div>
          </div>
        ) : (
          <>
            <h2 className="font-display text-xl font-semibold">About</h2>
            <p className="mt-3 text-sm leading-relaxed text-foreground/85">
              {user.bio || 'No bio yet.'}
            </p>
          </>
        )}
      </div>

      {/* Contributions */}
      <section className="mt-10">
        <SectionHeading
          eyebrow="Library"
          title="Your contributions"
          description="Songs you have added to the archive."
          actionLabel="Add a song"
          actionHref="/add-song"
        />

        {contributionsState === 'loading' && (
          <div className="flex items-center justify-center gap-2 rounded-xl border border-border bg-card py-12 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading your contributions...
          </div>
        )}

        {contributionsState === 'error' && (
          <div className="rounded-xl border border-border bg-card py-12 text-center text-sm text-muted-foreground">
            We could not load your contributions right now.
          </div>
        )}

        {contributionsState === 'ready' && contributions.length === 0 && (
          <div className="rounded-xl border border-border bg-card py-12 text-center text-sm text-muted-foreground">
            You have not added any songs yet.
          </div>
        )}

        {contributionsState === 'ready' && contributions.length > 0 && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {contributions.map((s) => (
              <SongCard key={s.id} song={s} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
