'use client'

import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import type { ArtistResponse, ComposerResponse, MaqamResponse, RhythmResponse } from './types'

export interface LookupData {
  artists: ArtistResponse[]
  composers: ComposerResponse[]
  maqamat: MaqamResponse[]
  rhythms: RhythmResponse[]
}

export function useSongLookups() {
  const [lookups, setLookups] = useState<LookupData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [artists, composers, maqamat, rhythms] = await Promise.all([
        api<ArtistResponse[]>('/artists'),
        api<ComposerResponse[]>('/composers'),
        api<MaqamResponse[]>('/maqamat'),
        api<RhythmResponse[]>('/rhythms'),
      ])
      setLookups({ artists, composers, maqamat, rhythms })
    } catch {
      setError('Could not load reference data. Check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  return { lookups, loading, error, retry: load }
}