import Link from 'next/link'
import { Music4 } from 'lucide-react'

import type { MaqamItem } from '@/lib/maqamat'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export function MaqamCard({ maqam, className }: { maqam: MaqamItem; className?: string }) {
  return (
    <Link
      href={`/maqamat/${maqam.id}`}
      className={cn(
        'group relative flex flex-col gap-3 rounded-xl border border-border bg-card p-5 transition-all duration-300',
        'hover:-translate-y-0.5 hover:border-gold/40 hover:bg-surface hover:shadow-lg hover:shadow-black/20',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-lg border border-gold/25 bg-gold-muted text-gold transition-colors group-hover:bg-gold group-hover:text-gold-foreground">
          <Music4 className="size-5" />
        </div>
        {maqam.tonic && <Badge variant="gold">{maqam.tonic}</Badge>}
      </div>

      <div className="min-w-0">
        <h3 className="font-display text-lg leading-tight font-semibold text-balance">
          {maqam.name_ar}
        </h3>
        {maqam.name_en && (
          <p className="mt-0.5 truncate text-sm text-muted-foreground">{maqam.name_en}</p>
        )}
      </div>

      {maqam.mood && (
        <p className="line-clamp-2 text-sm text-muted-foreground">{maqam.mood}</p>
      )}

      {(maqam.root_jins || maqam.branch_jins) && (
        <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-border/60 pt-3 text-xs text-muted-foreground">
          {maqam.root_jins && <span>Root jins: {maqam.root_jins.name_ar}</span>}
          {maqam.branch_jins && <span>Branch jins: {maqam.branch_jins.name_ar}</span>}
        </div>
      )}
    </Link>
  )
}
