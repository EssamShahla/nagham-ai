import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ArrowLeft, Music4 } from 'lucide-react'

import { api, ApiError } from '@/lib/api'
import { fetchRelatedSongs, type MaqamItem } from '@/lib/maqamat'
import { MaqamDetail } from '@/components/maqamat/maqam-detail'
import { ButtonLink } from '@/components/ui/button-link'

export const dynamic = 'force-dynamic'

function parseMaqamId(value: string): number | null {
  if (!/^\d+$/.test(value)) return null
  const id = Number(value)
  if (!Number.isSafeInteger(id)) return null
  return id
}

type MaqamLoadResult =
  | { ok: true; maqam: MaqamItem }
  | { ok: false; reason: 'not-found' | 'error' }

async function loadMaqam(id: number): Promise<MaqamLoadResult> {
  try {
    const maqam = await api<MaqamItem>(`/maqamat/${id}`)
    return { ok: true, maqam }
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return { ok: false, reason: 'not-found' }
    }
    return { ok: false, reason: 'error' }
  }
}

export default async function MaqamDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const maqamId = parseMaqamId(id)
  if (maqamId === null) notFound()

  const result = await loadMaqam(maqamId)
  if (!result.ok) {
    if (result.reason === 'not-found') notFound()

    return (
      <div className="mx-auto max-w-5xl">
        <Link
          href="/maqamat"
          className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-4" /> Back to maqamat
        </Link>

        <div className="flex flex-col items-center justify-center rounded-2xl border border-border bg-card py-20 text-center">
          <Music4 className="size-8 text-gold" />
          <h2 className="mt-4 font-display text-2xl font-semibold">Something went wrong</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            We could not load this maqam right now. Please try again in a moment.
          </p>
          <ButtonLink href="/maqamat" className="mt-6">
            Back to maqamat
          </ButtonLink>
        </div>
      </div>
    )
  }

  const { maqam } = result
  const relatedSongs = await fetchRelatedSongs(maqamId).catch(() => [])

  return (
    <div className="mx-auto max-w-5xl">
      <Link
        href="/maqamat"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" /> Back to maqamat
      </Link>

      <MaqamDetail maqam={maqam} relatedSongs={relatedSongs} />
    </div>
  )
}
