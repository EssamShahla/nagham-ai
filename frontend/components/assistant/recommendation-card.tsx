import Link from 'next/link'
import { Music2, ArrowUpRight } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { DifficultyDot } from '@/components/song-card'

type AssistantSong = {
  id: number
  title: string
  artist: string | null
  maqam: string | null
  difficulty: 'easy' | 'medium' | 'hard' | null
  year: number | null
  description: string | null
  moods: string[] | null
  topics: string[] | null
  similarity: number | null
}

export function RecommendationCard({ song }: { song: AssistantSong }) {
  return (
    <Link
      href={`/songs/${song.id}`}
      className="group flex flex-col gap-2.5 rounded-xl border border-border bg-background/50 p-4 transition-colors hover:border-gold/40 hover:bg-surface"
    >
      <div className="flex items-start gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-gold/25 bg-gold-muted text-gold">
          <Music2 className="size-4" />
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h4 className="font-display text-base font-semibold">
              {song.title}
            </h4>

            <ArrowUpRight className="size-4 shrink-0 text-muted-foreground transition-colors group-hover:text-gold" />
          </div>

          {song.artist && (
            <p className="text-xs text-muted-foreground">
              {song.artist}
            </p>
          )}
        </div>
      </div>

      {song.description && (
        <p className="text-sm leading-relaxed text-foreground/85">
          {song.description}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 border-t border-border/60 pt-2.5 text-xs text-muted-foreground">
        {song.maqam && (
          <Badge variant="gold">
            {song.maqam}
          </Badge>
        )}

        {song.moods?.map((mood) => (
          <Badge key={mood} variant="outline">
              {mood}
            </Badge>
        ))}

        {song.difficulty && (
          <>
            <span className="text-border">|</span>
            <DifficultyDot level={song.difficulty} />
          </>
        )}
      </div>
    </Link>
  )
}