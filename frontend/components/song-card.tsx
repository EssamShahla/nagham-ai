import Link from 'next/link'
import { Music2, User } from 'lucide-react'
import type { SongDifficulty, SongResponse } from '@/lib/types'
import { difficultyLabel, toSongDifficulty } from '@/lib/difficulty'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type LegacySongLevel = 'Beginner' | 'Intermediate' | 'Advanced'

type LegacySongShape = {
  id: string
  title: string
  artist: string
  maqam: string
  tonic: string
  rhythm: string
  difficulty: LegacySongLevel
}

export type SongCardSong = SongResponse | LegacySongShape

function isLegacySong(song: SongCardSong): song is LegacySongShape {
  return !('artist_name' in song)
}

type DifficultyLevel = SongDifficulty | LegacySongLevel | null | undefined

const DIFFICULTY_DOT_COLORS = {
  easy: 'bg-emerald-400/80',
  medium: 'bg-gold',
  hard: 'bg-rose-400/80',
} as const

export function DifficultyDot({ level }: { level: DifficultyLevel }) {
  const resolved = toSongDifficulty(level)
  const label = difficultyLabel(resolved)
  if (!resolved || !label) return null
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <span className={cn('size-1.5 rounded-full', DIFFICULTY_DOT_COLORS[resolved])} />
      {label}
    </span>
  )
}

export function SongCard({ song, className }: { song: SongCardSong; className?: string }) {
  const data = isLegacySong(song)
    ? {
        id: song.id,
        title: song.title,
        artist: song.artist,
        maqam: song.maqam,
        rhythm: song.rhythm,
        tonic: song.tonic,
        difficulty: song.difficulty as DifficultyLevel,
      }
    : {
        id: song.id,
        title: song.title,
        artist: song.artist_name,
        maqam: song.maqam_name,
        rhythm: song.rhythm_name,
        tonic: undefined as string | undefined,
        difficulty: song.difficulty as DifficultyLevel,
      }

  const hasMeta = Boolean(data.tonic) || Boolean(data.rhythm)
  const hasDifficulty = toSongDifficulty(data.difficulty) !== null

  return (
    <Link
      href={`/songs/${data.id}`}
      className={cn(
        'group relative flex flex-col gap-3 rounded-xl border border-border bg-card p-5 transition-all duration-300',
        'hover:-translate-y-0.5 hover:border-gold/40 hover:bg-surface hover:shadow-lg hover:shadow-black/20',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-lg border border-gold/25 bg-gold-muted text-gold transition-colors group-hover:bg-gold group-hover:text-gold-foreground">
          <Music2 className="size-5" />
        </div>
        {data.maqam && <Badge variant="gold">{data.maqam}</Badge>}
      </div>

      <div className="min-w-0">
        <h3 className="font-display text-lg leading-tight font-semibold text-balance">
          {data.title}
        </h3>
        <p className="mt-0.5 flex items-center gap-1.5 text-sm text-muted-foreground">
          <User className="size-3.5" />
          <span className="truncate">{data.artist ?? 'Unknown artist'}</span>
        </p>
      </div>

      <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-border/60 pt-3 text-xs text-muted-foreground">
        {data.tonic && <span>{data.tonic}</span>}
        {data.tonic && data.rhythm && <span className="text-border">|</span>}
        {data.rhythm && <span>{data.rhythm}</span>}
        {hasMeta && hasDifficulty && <span className="text-border">|</span>}
        <DifficultyDot level={data.difficulty} />
      </div>
    </Link>
  )
}