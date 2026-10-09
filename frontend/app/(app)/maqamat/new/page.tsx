'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Music4, Loader2, ShieldAlert, PlusCircle } from 'lucide-react'

import { api, ApiError, formatValidationError } from '@/lib/api'
import type { JinsResponse, MaqamResponse } from '@/lib/types'
import { useCurrentUser } from '@/components/use-current-user'
import { SectionHeading } from '@/components/section-heading'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { ButtonLink } from '@/components/ui/button-link'

interface FormValues {
  nameAr: string
  nameEn: string
  tonic: string
  accidentals: string
  ghammaz: string
  mood: string
  rootJinsId: string
  branchJinsId: string
  audioSampleUrl: string
  description: string
  notes: string
}

const EMPTY_FORM: FormValues = {
  nameAr: '',
  nameEn: '',
  tonic: '',
  accidentals: '',
  ghammaz: '',
  mood: '',
  rootJinsId: '',
  branchJinsId: '',
  audioSampleUrl: '',
  description: '',
  notes: '',
}

export default function AddMaqamPage() {
  const router = useRouter()
  const currentUser = useCurrentUser()

  const [ajnas, setAjnas] = useState<JinsResponse[]>([])
  const [ajnasError, setAjnasError] = useState(false)

  const [values, setValues] = useState<FormValues>(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    api<JinsResponse[]>('/ajnas')
      .then((data) => {
        if (!cancelled) setAjnas(data)
      })
      .catch(() => {
        if (!cancelled) setAjnasError(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (currentUser.isLoading) {
    return (
      <div className="mx-auto max-w-3xl">
        <SectionHeading eyebrow="Contribute" title="Add a maqam" />
        <div className="flex items-center justify-center gap-3 rounded-2xl border border-border bg-card py-20 text-center">
          <Loader2 className="size-5 animate-spin text-gold" />
          <span className="text-sm text-muted-foreground">Checking your account…</span>
        </div>
      </div>
    )
  }

  if (!currentUser.data || currentUser.data.role !== 'admin') {
    return (
      <div className="mx-auto max-w-3xl">
        <SectionHeading eyebrow="Contribute" title="Add a maqam" />
        <div className="flex flex-col items-center rounded-2xl border border-border bg-card py-20 text-center">
          <ShieldAlert className="size-8 text-gold" />
          <h2 className="mt-4 font-display text-xl font-semibold">Admin access required</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Only administrators can add new maqamat to the library.
          </p>
          <ButtonLink href="/maqamat" className="mt-6">
            Back to maqamat
          </ButtonLink>
        </div>
      </div>
    )
  }

  const set = (patch: Partial<FormValues>) => setValues((prev) => ({ ...prev, ...patch }))

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (submitting) return
    setError(null)

    const nameAr = values.nameAr.trim()
    if (!nameAr) {
      setError('Arabic name is required.')
      return
    }

    const payload = {
      name_ar: nameAr,
      name_en: values.nameEn.trim() || null,
      tonic: values.tonic.trim() || null,
      accidentals: values.accidentals.trim() || null,
      ghammaz: values.ghammaz.trim() || null,
      mood: values.mood.trim() || null,
      root_jins_id: values.rootJinsId ? Number(values.rootJinsId) : null,
      branch_jins_id: values.branchJinsId ? Number(values.branchJinsId) : null,
      audio_sample_url: values.audioSampleUrl.trim() || null,
      description: values.description.trim() || null,
      notes: values.notes.trim() || null,
    }

    setSubmitting(true)
    try {
      const created = await api<MaqamResponse>('/maqamat', { method: 'POST', body: payload, auth: true })
      router.push(`/maqamat/${created.id}`)
    } catch (err) {
      if (err instanceof ApiError) {
        switch (err.status) {
          case 401:
            setError('You need to be logged in to add a maqam.')
            window.setTimeout(() => router.push('/login'), 1500)
            return
          case 403:
            setError('You do not have permission to add a maqam.')
            return
          case 409:
            setError('A maqam with this name already exists.')
            return
          case 404:
            setError('A selected jins no longer exists. Refresh the page and try again.')
            return
          case 422:
            setError(formatValidationError(err.detail))
            return
          default:
            setError(
              typeof err.detail === 'string'
                ? err.detail
                : `Something went wrong (status ${err.status}). Please try again.`,
            )
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
        title="Add a maqam"
        description="Add verified musical information only. Leave fields empty if the information isn't confirmed."
      />

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {error && (
          <div role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-5 py-4 text-sm text-rose-400">
            {error}
          </div>
        )}

        <fieldset className="rounded-2xl border border-border bg-card p-6">
          <legend className="flex items-center gap-2 px-2 font-display text-lg font-semibold">
            <Music4 className="size-5 text-gold" /> Basics
          </legend>
          <div className="mt-4 grid gap-5 sm:grid-cols-2">
            <div>
              <Label htmlFor="name_ar">Arabic name</Label>
              <Input
                id="name_ar"
                required
                placeholder="e.g. بياتي"
                value={values.nameAr}
                onChange={(e) => set({ nameAr: e.target.value })}
                disabled={submitting}
              />
            </div>
            <div>
              <Label htmlFor="name_en">English name</Label>
              <Input
                id="name_en"
                placeholder="e.g. Bayati"
                value={values.nameEn}
                onChange={(e) => set({ nameEn: e.target.value })}
                disabled={submitting}
              />
            </div>
            <div>
              <Label htmlFor="tonic">Tonic</Label>
              <Input
                id="tonic"
                placeholder="e.g. Re / ري"
                value={values.tonic}
                onChange={(e) => set({ tonic: e.target.value })}
                disabled={submitting}
              />
            </div>
            <div>
              <Label htmlFor="ghammaz">Ghammaz</Label>
              <Input
                id="ghammaz"
                value={values.ghammaz}
                onChange={(e) => set({ ghammaz: e.target.value })}
                disabled={submitting}
              />
            </div>
            <div className="sm:col-span-2">
              <Label htmlFor="accidentals">Accidentals</Label>
              <Input
                id="accidentals"
                placeholder="e.g. half-flat E, half-flat B"
                value={values.accidentals}
                onChange={(e) => set({ accidentals: e.target.value })}
                disabled={submitting}
              />
            </div>
            <div className="sm:col-span-2">
              <Label htmlFor="mood">Mood</Label>
              <Input
                id="mood"
                placeholder="e.g. warm and emotional"
                value={values.mood}
                onChange={(e) => set({ mood: e.target.value })}
                disabled={submitting}
              />
            </div>
          </div>
        </fieldset>

        <fieldset className="rounded-2xl border border-border bg-card p-6">
          <legend className="flex items-center gap-2 px-2 font-display text-lg font-semibold">
            <Music4 className="size-5 text-gold" /> Ajnas
          </legend>
          <div className="mt-4 grid gap-5 sm:grid-cols-2">
            <div>
              <Label htmlFor="root_jins">Root jins</Label>
              <Select
                id="root_jins"
                value={values.rootJinsId}
                onChange={(e) => set({ rootJinsId: e.target.value })}
                disabled={submitting}
              >
                <option value="">No root jins selected</option>
                {ajnas.map((j) => (
                  <option key={j.id} value={String(j.id)}>
                    {j.name_ar || j.name_en || `Jins ${j.id}`}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="branch_jins">Branch jins</Label>
              <Select
                id="branch_jins"
                value={values.branchJinsId}
                onChange={(e) => set({ branchJinsId: e.target.value })}
                disabled={submitting}
              >
                <option value="">No branch jins selected</option>
                {ajnas.map((j) => (
                  <option key={j.id} value={String(j.id)}>
                    {j.name_ar || j.name_en || `Jins ${j.id}`}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          {ajnasError && (
            <p className="mt-3 text-xs text-muted-foreground">
              Ajnas options could not be loaded. You can still submit without them.
            </p>
          )}
        </fieldset>

        <fieldset className="rounded-2xl border border-border bg-card p-6">
          <legend className="flex items-center gap-2 px-2 font-display text-lg font-semibold">
            <Music4 className="size-5 text-gold" /> Notes &amp; media
          </legend>
          <div className="mt-4 flex flex-col gap-5">
            <div>
              <Label htmlFor="audio_sample_url">Audio sample URL</Label>
              <Input
                id="audio_sample_url"
                type="url"
                placeholder="https://…"
                value={values.audioSampleUrl}
                onChange={(e) => set({ audioSampleUrl: e.target.value })}
                disabled={submitting}
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                className="min-h-24"
                value={values.description}
                onChange={(e) => set({ description: e.target.value })}
                disabled={submitting}
              />
            </div>
            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                className="min-h-24"
                value={values.notes}
                onChange={(e) => set({ notes: e.target.value })}
                disabled={submitting}
              />
            </div>
          </div>
        </fieldset>

        <div className="flex flex-wrap items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => {
              setValues(EMPTY_FORM)
              setError(null)
            }}
            disabled={submitting}
            className="rounded-lg border border-border px-5 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
          >
            Reset
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="flex items-center gap-2 rounded-lg bg-gold px-5 py-2.5 text-sm font-medium text-gold-foreground transition-colors hover:bg-gold/90 disabled:opacity-50"
          >
            {submitting ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Submitting…
              </>
            ) : (
              <>
                <PlusCircle className="size-4" /> Submit maqam
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
