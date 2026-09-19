import Link from 'next/link'
import type { Maqam } from '@/lib/mock-data'
import { cn } from '@/lib/utils'

export function MaqamCard({ maqam, className }: { maqam: Maqam; className?: string }) {
  return (
    <Link
      href={`/songs?maqam=${maqam.name}`}
      className={cn(
        'group relative flex flex-col gap-2 overflow-hidden rounded-xl border border-border bg-card p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-gold/40 hover:bg-surface',
        className,
      )}
    >
      <div className="flex items-baseline justify-between">
        <h3 className="font-display text-xl font-semibold">{maqam.name}</h3>
        <span className="font-display text-2xl text-gold/70 transition-colors group-hover:text-gold">
          {maqam.arabic}
        </span>
      </div>
      <p className="text-xs font-medium tracking-wide text-gold/90 uppercase">{maqam.mood}</p>
      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{maqam.description}</p>
      <span className="mt-2 text-xs text-muted-foreground/80">Tonic · {maqam.tonic}</span>
    </Link>
  )
}
