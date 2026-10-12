import { ExternalLink, Music4, Sparkles } from 'lucide-react'

import type { MaqamItem } from '@/lib/maqamat'
import type { SongResponse } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { ButtonLink } from '@/components/ui/button-link'
import { buttonVariants } from '@/components/ui/button'
import { SongCard } from '@/components/song-card'
import { MaqamNotation } from '@/components/maqamat/maqam-notation'

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

  const hasVerifiedScale = Boolean(maqam.tonic && maqam.scale_pattern && maqam.scale_pattern.length > 0)

  const maqamWorldSlug = maqam.name_en?.toLowerCase().replace(/[^a-z]/g, '')
  const maqamWorldUrl = maqamWorldSlug ? `https://maqamworld.com/en/maqam/${maqamWorldSlug}.php` : null

  const askNaghamHref = `/assistant?q=${encodeURIComponent(`اشرحلي مقام ${maqam.name_ar}`)}`

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

        <div className="mt-6 flex flex-wrap gap-2">
          <ButtonLink href={askNaghamHref} size="sm" variant="default">
            <Sparkles className="size-3.5" /> اسأل نغم AI عن هذا المقام
          </ButtonLink>
          {maqamWorldUrl && (
            <a
              href={maqamWorldUrl}
              target="_blank"
              rel="noreferrer noopener"
              className={buttonVariants({ size: 'sm', variant: 'outline' })}
            >
              <ExternalLink className="size-3.5" /> المصدر على Maqam World
            </a>
          )}
        </div>
      </div>

      {/* Interactive notation + audio */}
      <section className="mt-8">
        <h2 className="font-display text-xl font-semibold">السلم التفاعلي</h2>

        {hasVerifiedScale ? (
          <div className="mt-4">
            <MaqamNotation
              tonic={maqam.tonic!}
              scalePattern={maqam.scale_pattern!}
              degreeNames={maqam.degree_names}
            />
          </div>
        ) : (
          <div className="mt-4 rounded-xl border border-dashed border-border bg-background/40 p-6 text-center text-sm text-muted-foreground">
            لم يتم التحقق من بيانات السلم الموسيقي لهذا المقام بعد. سيتم إضافتها بعد مراجعة
            مصادر موثوقة، تفاديًا لعرض معلومات غير دقيقة.
          </div>
        )}
      </section>

      {/* Ajnas breakdown */}
      {maqam.ajnas_breakdown.length > 0 && (
        <section className="mt-8">
          <h2 className="font-display text-xl font-semibold">تفكيك الأجناس</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {maqam.ajnas_breakdown.map((entry, index) => (
              <div
                key={index}
                className="rounded-xl border border-border bg-background/50 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">
                    {entry.jins.name_ar}
                    {entry.jins.name_en && (
                      <span className="text-muted-foreground"> ({entry.jins.name_en})</span>
                    )}
                  </p>
                  <Badge variant={entry.is_primary_alternative ? 'gold' : 'outline'}>
                    الدرجة {entry.start_degree}
                  </Badge>
                </div>
                {!entry.is_primary_alternative && (
                  <p className="mt-1 text-xs text-muted-foreground">بديل موثّق (غير أساسي)</p>
                )}
                {entry.jins.scale_pattern ? (
                  entry.jins.description && (
                    <p className="mt-2 text-sm text-muted-foreground">{entry.jins.description}</p>
                  )
                ) : (
                  <p className="mt-2 text-xs text-muted-foreground">
                    بيانات هذا الجنس غير مكتملة التحقق بعد.
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

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
