import { SongLibrary } from '@/components/songs/song-library'
import { SectionHeading } from '@/components/section-heading'

type SongsSearchParams = {
  q?: string | string[]
  maqam_id?: string | string[]
  rhythm_id?: string | string[]
  difficulty?: string | string[]
  page?: string | string[]
}

function first(value: string | string[] | undefined): string | undefined {
  return typeof value === 'string' ? value : undefined
}

export default async function SongsPage({
  searchParams,
}: {
  searchParams: Promise<SongsSearchParams>
}) {
  const sp = await searchParams

  const page = Number(first(sp.page))
  const initialPage = Number.isInteger(page) && page >= 1 ? page : 1

  return (
    <div className="mx-auto max-w-6xl">
      <SectionHeading
        eyebrow="Library"
        title="Song search"
        description="Filter the archive by maqam, tonic, rhythm and difficulty to find exactly what you need."
      />
      <SongLibrary
        initialQuery={first(sp.q) ?? ''}
        initialMaqamId={first(sp.maqam_id) ?? 'all'}
        initialRhythmId={first(sp.rhythm_id) ?? 'all'}
        initialDifficulty={first(sp.difficulty) ?? 'all'}
        initialPage={initialPage}
      />
    </div>
  )
}