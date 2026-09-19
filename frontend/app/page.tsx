import Image from 'next/image'
import Link from 'next/link'
import {
  Sparkles,
  ScanSearch,
  Music4,
  ArrowRight,
  Waves,
  Languages,
} from 'lucide-react'
import { MarketingHeader } from '@/components/marketing-header'
import { MarketingFooter } from '@/components/marketing-footer'
import { ButtonLink } from '@/components/ui/button-link'
import { SongCard } from '@/components/song-card'
import { MaqamCard } from '@/components/maqam-card'
import { SectionHeading } from '@/components/section-heading'
import { SONGS, MAQAMAT, SUGGESTED_PROMPTS } from '@/lib/mock-data'

const FEATURES = [
  {
    icon: Sparkles,
    title: 'AI Music Assistant',
    body: 'Ask in plain language — "emotional songs in Bayati" or "what to play after Enta Omri" — and get curated repertoire with reasoning.',
  },
  {
    icon: Waves,
    title: 'Maqam-Aware Discovery',
    body: 'Filter by maqam, tonic, rhythm and modulation. Every result understands the modal structure that defines Oriental music.',
  },
  {
    icon: Languages,
    title: 'Meaning & Lyrics Search',
    body: 'Search by theme and feeling. Semantic search reads the meaning of lyrics, not just keywords, across the Arabic repertoire.',
  },
]

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <MarketingHeader />

      <main className="flex-1">
        {/* Hero */}
        <section className="bg-vignette relative overflow-hidden">
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 md:px-6 md:py-28 lg:grid-cols-2">
            <div className="animate-rise">
              <span className="inline-flex items-center gap-2 rounded-full border border-gold/25 bg-gold-muted px-3 py-1 text-xs font-medium text-gold">
                <Sparkles className="size-3.5" />
                Intelligent Oriental music discovery
              </span>
              <h1 className="mt-6 font-display text-4xl leading-[1.05] font-semibold text-balance md:text-6xl">
                Find the right song in the language of{' '}
                <span className="text-gold">maqam</span>.
              </h1>
              <p className="mt-5 max-w-lg text-base leading-relaxed text-muted-foreground md:text-lg">
                Nagham AI helps Arabic and Oriental musicians discover repertoire by maqam, mood
                and meaning — with an assistant that truly understands tarab.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <ButtonLink href="/register" className="h-12 gap-2 px-6 text-base">
                  Start exploring
                  <ArrowRight className="size-4" />
                </ButtonLink>
                <ButtonLink
                  href="/assistant"
                  variant="outline"
                  className="h-12 gap-2 px-6 text-base"
                >
                  <Sparkles className="size-4" />
                  Try the assistant
                </ButtonLink>
              </div>
              <div className="mt-8 flex flex-wrap gap-2">
                {SUGGESTED_PROMPTS.slice(0, 3).map((p) => (
                  <Link
                    key={p}
                    href="/assistant"
                    className="rounded-full border border-border bg-card/60 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground"
                  >
                    “{p}”
                  </Link>
                ))}
              </div>
            </div>

            <div className="animate-rise-delay-1 relative">
              <div className="relative aspect-[4/5] overflow-hidden rounded-2xl border border-gold/20 shadow-2xl shadow-black/40">
                <Image
                  src="/hero-oud.png"
                  alt="A traditional Arabic oud lit dramatically in gold against darkness"
                  fill
                  priority
                  className="object-cover"
                  sizes="(max-width: 1024px) 100vw, 45vw"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background/70 via-transparent to-transparent" />
                <div className="absolute right-4 bottom-4 left-4 rounded-xl border border-white/10 bg-background/70 p-4 backdrop-blur-md">
                  <p className="text-xs tracking-[0.18em] text-gold uppercase">Now understanding</p>
                  <p className="mt-1 font-display text-lg">
                    “Songs of longing in Maqam Bayati”
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="mx-auto max-w-6xl px-4 py-16 md:px-6 md:py-20">
          <SectionHeading
            eyebrow="Why Nagham"
            title="Built for the way Oriental musicians actually think"
            description="Not a generic music search. Nagham understands maqamat, modulations, rhythm and the emotional weight of Arabic lyrics."
          />
          <div className="grid gap-5 md:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="group rounded-2xl border border-border bg-card p-6 transition-colors hover:border-gold/40"
              >
                <div className="flex size-12 items-center justify-center rounded-xl border border-gold/25 bg-gold-muted text-gold transition-colors group-hover:bg-gold group-hover:text-gold-foreground">
                  <f.icon className="size-6" />
                </div>
                <h3 className="mt-5 font-display text-xl font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Maqamat */}
        <section id="maqamat" className="border-y border-border/60 bg-surface/30">
          <div className="mx-auto max-w-6xl px-4 py-16 md:px-6 md:py-20">
            <SectionHeading
              eyebrow="The modal system"
              title="Explore the maqamat"
              description="Each maqam carries its own emotional world. Start from a mode and find the songs that live within it."
              actionLabel="Browse all songs"
              actionHref="/songs"
            />
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {MAQAMAT.slice(0, 6).map((m) => (
                <MaqamCard key={m.slug} maqam={m} />
              ))}
            </div>
          </div>
        </section>

        {/* Featured songs */}
        <section id="songs" className="mx-auto max-w-6xl px-4 py-16 md:px-6 md:py-20">
          <SectionHeading
            eyebrow="From the archive"
            title="Featured repertoire"
            description="Timeless pieces annotated with maqam, tonic, rhythm and difficulty."
            actionLabel="Open library"
            actionHref="/songs"
          />
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {SONGS.slice(0, 4).map((s) => (
              <SongCard key={s.id} song={s} />
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-6xl px-4 pb-20 md:px-6">
          <div className="relative overflow-hidden rounded-3xl border border-gold/20 bg-vignette px-6 py-14 text-center md:px-16 md:py-20">
            <div className="mx-auto flex size-14 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
              <Music4 className="size-7" />
            </div>
            <h2 className="mx-auto mt-6 max-w-2xl font-display text-3xl font-semibold text-balance md:text-4xl">
              Your next performance starts with the right nagham
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
              Join a growing community of musicians preserving and expanding the maqam tradition.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <ButtonLink href="/register" className="h-12 gap-2 px-6 text-base">
                Create your account
                <ArrowRight className="size-4" />
              </ButtonLink>
              <ButtonLink
                href="/semantic"
                variant="outline"
                className="h-12 gap-2 px-6 text-base"
              >
                <ScanSearch className="size-4" />
                Try lyrics search
              </ButtonLink>
            </div>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  )
}
