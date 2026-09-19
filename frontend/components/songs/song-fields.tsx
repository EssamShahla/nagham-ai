'use client'

import { Music2, Info } from 'lucide-react'
import type { LookupData } from '@/lib/use-song-lookups'
import { SONG_DIFFICULTY_OPTIONS } from '@/lib/difficulty'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

export interface SongFormValues {
  title: string
  artistId: string
  composerId: string
  year: string
  difficulty: string
  maqamId: string
  rhythmId: string
  lyrics: string
}

export const EMPTY_SONG_FORM: SongFormValues = {
  title: '',
  artistId: '',
  composerId: '',
  year: '',
  difficulty: '',
  maqamId: '',
  rhythmId: '',
  lyrics: '',
}

interface SongFieldsProps {
  lookups: LookupData
  values: SongFormValues
  onChange: (next: SongFormValues) => void
  disabled?: boolean
}

export function SongFields({ lookups, values, onChange, disabled = false }: SongFieldsProps) {
  const noArtists = lookups.artists.length === 0
  const set = (patch: Partial<SongFormValues>) => onChange({ ...values, ...patch })

  return (
    <>
      {noArtists && (
        <div className="rounded-xl border border-gold/30 bg-gold-muted/50 px-5 py-4 text-sm text-gold">
          An artist must exist in the system before a song can be created or edited.
        </div>
      )}

      {/* Basics */}
      <fieldset className="rounded-2xl border border-border bg-card p-6">
        <legend className="flex items-center gap-2 px-2 font-display text-lg font-semibold">
          <Music2 className="size-5 text-gold" /> Basics
        </legend>
        <div className="mt-4 grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Label htmlFor="title">Song title</Label>
            <Input
              id="title"
              required
              placeholder="e.g. Enta Omri"
              value={values.title}
              onChange={(e) => set({ title: e.target.value })}
              disabled={disabled}
            />
          </div>
          <div>
            <Label htmlFor="artist">Artist</Label>
            <Select
              id="artist"
              required
              value={values.artistId}
              onChange={(e) => set({ artistId: e.target.value })}
              disabled={disabled || noArtists}
            >
              <option value="">{noArtists ? 'No artists available' : 'Choose an artist'}</option>
              {lookups.artists.map((a) => (
                <option key={a.id} value={String(a.id)}>
                  {a.name_ar || a.name_en || `Artist ${a.id}`}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="composer">Composer</Label>
            <Select
              id="composer"
              value={values.composerId}
              onChange={(e) => set({ composerId: e.target.value })}
              disabled={disabled}
            >
              <option value="">No composer selected</option>
              {lookups.composers.map((c) => (
                <option key={c.id} value={String(c.id)}>
                  {c.name_ar || c.name_en || `Composer ${c.id}`}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="year">Year</Label>
            <Input
              id="year"
              type="number"
              min={1800}
              max={new Date().getFullYear()}
              placeholder="e.g. 1964"
              value={values.year}
              onChange={(e) => set({ year: e.target.value })}
              disabled={disabled}
            />
          </div>
          <div>
            <Label htmlFor="difficulty">Difficulty</Label>
            <Select
              id="difficulty"
              value={values.difficulty}
              onChange={(e) => set({ difficulty: e.target.value })}
              disabled={disabled}
            >
              <option value="">Not sure</option>
              {SONG_DIFFICULTY_OPTIONS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </fieldset>

      {/* Maqam & rhythm */}
      <fieldset className="rounded-2xl border border-border bg-card p-6">
        <legend className="flex items-center gap-2 px-2 font-display text-lg font-semibold">
          <Info className="size-5 text-gold" /> Maqam &amp; rhythm
        </legend>
        <div className="mt-4 grid gap-5 sm:grid-cols-2">
          <div>
            <Label htmlFor="maqam">Primary maqam</Label>
            <Select
              id="maqam"
              value={values.maqamId}
              onChange={(e) => set({ maqamId: e.target.value })}
              disabled={disabled}
            >
              <option value="">No maqam selected</option>
              {lookups.maqamat.map((m) => (
                <option key={m.id} value={String(m.id)}>
                  {m.name_ar || m.name_en || `Maqam ${m.id}`}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="rhythm">Rhythm</Label>
            <Select
              id="rhythm"
              value={values.rhythmId}
              onChange={(e) => set({ rhythmId: e.target.value })}
              disabled={disabled}
            >
              <option value="">{lookups.rhythms.length === 0 ? 'No rhythms in system' : 'No rhythm selected'}</option>
              {lookups.rhythms.map((r) => (
                <option key={r.id} value={String(r.id)}>
                  {r.name_ar || r.name_en || `Rhythm ${r.id}`}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </fieldset>

      {/* Lyrics */}
      <fieldset className="rounded-2xl border border-border bg-card p-6">
        <legend className="flex items-center gap-2 px-2 font-display text-lg font-semibold">
          <Info className="size-5 text-gold" /> Lyrics
        </legend>
        <div className="mt-4">
          <Label htmlFor="lyrics">Lyrics</Label>
          <Textarea
            id="lyrics"
            placeholder="Paste the full lyrics here (with translation if possible)…"
            className="min-h-36"
            value={values.lyrics}
            onChange={(e) => set({ lyrics: e.target.value })}
            disabled={disabled}
          />
        </div>
      </fieldset>
    </>
  )
}