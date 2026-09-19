import Link from 'next/link'
import { Sparkles, Heart, CloudRain, Flame, Sunrise, ArrowRight } from 'lucide-react'
import { SONGS, MAQAMAT } from '@/lib/mock-data'
import { SectionHeading } from '@/components/section-heading'
import { SongCard } from '@/components/song-card'
import { MaqamCard } from '@/components/maqam-card'

const COLLECTIONS = [
  {
    title: 'Songs of longing',
    body: 'Yearning, distance and the ache of separation.',
    icon: CloudRain,
    match: (theme: string) => /longing|separation|travel|home/i.test(theme),
  },
  {
    title: 'Tender & romantic',
    body: 'Love awakened, gentle affection and devotion.',
    icon: Heart,
    match: (theme: string) => /love|affection|beauty|grace/i.test(theme),
  },
  {
    title: 'Passionate & cinematic',
    body: 'Sweeping, dramatic pieces full of intensity.',
    icon: Flame,
    match: (_theme: string, mood: string) => /passionate|cinematic|dramatic/i.test(mood),
  },
]

export default function DiscoverPage() {
  return (
    <div className="mx-auto max-w-6xl">
      {/* Hero */}
      <section className="overflow-hidden rounded-2xl border border-gold/20 bg-vignette p-6 md:p-8">
        <span className="inline-flex items-center gap-2 rounded-full border border-gold/25 bg-gold-muted px-3 py-1 text-xs font-medium text-gold">
          <Sunrise className="size-3.5" /> Curated for you
        </span>
        <h1 className="mt-4 font-display text-3xl font-semibold text-balance md:text-4xl">
          Discover by feeling
        </h1>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground md:text-base">
          Collections that group the repertoire by emotion and theme — a starting point for your
          next set.
        </p>
        <Link
          href="/semantic"
          className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-gold hover:underline"
        >
          Or search lyrics by meaning <ArrowRight className="size-4" />
        </Link>
      </section>

      {/* Collections */}
      {COLLECTIONS.map((col) => {
        const songs = SONGS.filter((s) => col.match(s.theme, s.mood)).slice(0, 4)
        if (!songs.length) return null
        return (
          <section key={col.title} className="mt-10">
            <div className="mb-6 flex items-center gap-3">
              <span className="flex size-11 items-center justify-center rounded-xl border border-gold/25 bg-gold-muted text-gold">
                <col.icon className="size-5" />
              </span>
              <div>
                <h2 className="font-display text-2xl font-semibold">{col.title}</h2>
                <p className="text-sm text-muted-foreground">{col.body}</p>
              </div>
            </div>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {songs.map((s) => (
                <SongCard key={s.id} song={s} />
              ))}
            </div>
          </section>
        )
      })}

      {/* Explore maqamat */}
      <section className="mt-12">
        <SectionHeading
          eyebrow="By mode"
          title="Start from a maqam"
          description="Each mode opens a different emotional world."
          actionLabel="All songs"
          actionHref="/songs"
        />
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {MAQAMAT.map((m) => (
            <MaqamCard key={m.slug} maqam={m} />
          ))}
        </div>
      </section>
    </div>
  )
}
