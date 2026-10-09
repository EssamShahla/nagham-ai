import { Music4 } from 'lucide-react'

import type { MaqamItem } from '@/lib/maqamat'
import type { SongResponse } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { SongCard } from '@/components/song-card'

const FIELD_LABELS: Record<string, string> = {
  tonic: 'Tonic',
  accidentals: 'Accidentals',
  ghammaz: 'Ghammaz',
  mood: 'Mood',
}

export function MaqamDetail({
  maqam,
  relatedSongs,
}: {
  maqam: MaqamItem
  relatedSongs: SongResponse[]
}) {
  const facts = (['tonic', 'accidentals', 'ghammaz', 'mood'] as const)
    .map((key) => ({ key, value: maqam[key] }))
    .filter((fact) => Boolean(fact.value))

  return (
    <div>
      {/* Hero */}
      <div className="overflow-hidden rounded-2xl border border-gold/20 bg-vignette p-6 md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            {(maqam.root_jins || maqam.branch_jins) && (
              <div className="flex flex-wrap items-center gap-2">
                {maqam.root_jins && <Badge variant="gold">Root: {maqam.root_jins.name_ar}</Badge>}
                {maqam.branch_jins && (
                  <Badge variant="outline">Branch: {maqam.branch_jins.name_ar}</Badge>
                )}
              </div>
            )}
            <h1 className="mt-3 font-display text-4xl font-semibold text-balance">
              {maqam.name_ar}
            </h1>
            {maqam.name_en && (
              <p className="mt-2 text-muted-foreground">{maqam.name_en}</p>
            )}
          </div>
          <span className="flex size-16 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
            <Music4 className="size-8" />
          </span>
        </div>

        {maqam.description && (
          <p className="mt-6 max-w-2xl leading-relaxed text-foreground/90">{maqam.description}</p>
        )}

        {facts.length > 0 && (
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {facts.map((fact) => (
              <div key={fact.key} className="rounded-xl border border-border bg-background/50 p-4">
                <p className="text-xs text-muted-foreground">{FIELD_LABELS[fact.key]}</p>
                <p className="mt-1 font-medium">{fact.value}</p>
              </div>
            ))}
          </div>
        )}

        {maqam.audio_sample_url && (
          <div className="mt-6">
            <p className="mb-2 text-xs text-muted-foreground">Audio sample</p>
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <audio controls src={maqam.audio_sample_url} className="w-full" />
          </div>
        )}
      </div>

      {/* Related songs */}
      <section className="mt-8">
        <h2 className="font-display text-xl font-semibold">Songs in this maqam</h2>

        {relatedSongs.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No songs are recorded in this maqam yet.
          </p>
        ) : (
          <div className="mt-4 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {relatedSongs.map((song) => (
              <SongCard key={song.id} song={song} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
