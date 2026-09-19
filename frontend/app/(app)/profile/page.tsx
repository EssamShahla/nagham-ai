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
} from 'lucide-react'
import { CURRENT_USER, SONGS } from '@/lib/mock-data'
import { api } from '@/lib/api'
import type { UserResponse } from '@/lib/types'
import { SongCard } from '@/components/song-card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { SectionHeading } from '@/components/section-heading'

export default function ProfilePage() {
  const router = useRouter()
  const [user, setUser] = useState<UserResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    name: '',
    bio: '',
    instrument: '',
    city: '',
    country: '',
  })
  const [draft, setDraft] = useState(form)

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
        setForm({
          name: me.name,
          bio: me.bio ?? '',
          instrument: me.instrument ?? '',
          city: me.city ?? '',
          country: me.country ?? '',
        })
        setUser(me)
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

  const initials = (form.name || '?')
    .split(' ')
    .map((n) => n[0])
    .join('')

  const contributed = SONGS.filter((s) => s.artist === 'Umm Kulthum').slice(0, 3)

  const stats = [
    { icon: Guitar, label: 'Instrument', value: form.instrument },
    { icon: Award, label: 'Contributions', value: String(CURRENT_USER.contributions) },
    { icon: CalendarClock, label: 'Experience', value: `${CURRENT_USER.experience} years` },
  ]

  function save() {
    setForm(draft)
    setEditing(false)
  }
  function cancel() {
    setDraft(form)
    setEditing(false)
  }

  if (loading || !user) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading your profile...</p>
      </div>
    )
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
                <h1 className="font-display text-3xl font-semibold">{form.name}</h1>
                <p className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Music className="size-4" /> {user.music_role || user.instrument || 'Musician'}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <MapPin className="size-4" /> {form.city}, {form.country}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Mail className="size-4" /> {user.email}
                  </span>
                </p>
              </div>
            </div>
            {!editing && (
              <button
                onClick={() => {
                  setDraft(form)
                  setEditing(true)
                }}
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
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <Label htmlFor="p-name">Name</Label>
                <Input
                  id="p-name"
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="p-instrument">Instrument</Label>
                <Input
                  id="p-instrument"
                  value={draft.instrument}
                  onChange={(e) => setDraft({ ...draft, instrument: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="p-city">City</Label>
                <Input
                  id="p-city"
                  value={draft.city}
                  onChange={(e) => setDraft({ ...draft, city: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="p-country">Country</Label>
                <Input
                  id="p-country"
                  value={draft.country}
                  onChange={(e) => setDraft({ ...draft, country: e.target.value })}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="p-bio">Bio</Label>
              <Textarea
                id="p-bio"
                value={draft.bio}
                onChange={(e) => setDraft({ ...draft, bio: e.target.value })}
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={cancel}
                className="flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                <X className="size-4" /> Cancel
              </button>
              <button
                onClick={save}
                className="flex items-center gap-2 rounded-lg bg-gold px-4 py-2 text-sm font-medium text-gold-foreground hover:bg-gold/90"
              >
                <Check className="size-4" /> Save changes
              </button>
            </div>
          </div>
        ) : (
          <>
            <h2 className="font-display text-xl font-semibold">About</h2>
            <p className="mt-3 text-sm leading-relaxed text-foreground/85">{form.bio}</p>
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
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {contributed.map((s) => (
            <SongCard key={s.id} song={s} />
          ))}
        </div>
      </section>
    </div>
  )
}
