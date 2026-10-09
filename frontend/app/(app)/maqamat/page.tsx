import type { Metadata } from 'next'

import { SectionHeading } from '@/components/section-heading'
import { MaqamatLibrary } from '@/components/maqamat/maqamat-library'

export const metadata: Metadata = {
  title: 'Maqamat | Nagham AI',
  description:
    'Browse the Oriental maqam library: names, tonic, root and branch jins, mood, and notation.',
}

type MaqamatSearchParams = {
  q?: string | string[]
}

function first(value: string | string[] | undefined): string | undefined {
  return typeof value === 'string' ? value : undefined
}

export default async function MaqamatPage({
  searchParams,
}: {
  searchParams: Promise<MaqamatSearchParams>
}) {
  const sp = await searchParams

  return (
    <div className="mx-auto max-w-6xl">
      <SectionHeading
        eyebrow="Oriental Music Theory"
        title="Maqamat"
        description="Browse the full maqam library, or search by Arabic or English name."
      />

      <MaqamatLibrary initialQuery={first(sp.q) ?? ''} />
    </div>
  )
}
