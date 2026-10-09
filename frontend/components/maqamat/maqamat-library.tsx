'use client'

import { useEffect, useState } from 'react'
import { Search, PlusCircle } from 'lucide-react'

import { fetchMaqamat, type MaqamItem } from '@/lib/maqamat'
import { ApiError } from '@/lib/api'
import { MaqamCard } from '@/components/maqamat/maqam-card'
import { useCurrentUser } from '@/components/use-current-user'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ButtonLink } from '@/components/ui/button-link'

function friendlyApiError(err: unknown): string {
  if (err instanceof ApiError && err.message) return err.message
  return 'Unable to connect to the server. Please check your connection and try again.'
}

export function MaqamatLibrary({ initialQuery }: { initialQuery: string }) {
  const [query, setQuery] = useState(initialQuery)
  const [items, setItems] = useState<MaqamItem[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  const currentUser = useCurrentUser()
  const isAdmin = currentUser.data?.role === 'admin'

  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()
    setLoading(true)
    setError(null)

    const timeout = window.setTimeout(() => {
      fetchMaqamat({ search: query.trim() || undefined }, controller.signal)
        .then((data) => {
          if (cancelled) return
          setItems(data)
          setLoading(false)
        })
        .catch((err) => {
          if (cancelled || (err as Error).name === 'AbortError') return
          setError(friendlyApiError(err))
          setLoading(false)
        })
    }, 250)

    return () => {
      cancelled = true
      controller.abort()
      window.clearTimeout(timeout)
    }
  }, [query, reloadKey])

  useEffect(() => {
    const searchParams = new URLSearchParams()
    if (query) searchParams.set('q', query)
    const qs = searchParams.toString()
    window.history.replaceState(null, '', qs ? `/maqamat?${qs}` : '/maqamat')
  }, [query])

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <div className="relative max-w-sm flex-1 sm:flex-none sm:w-80">
          <Label htmlFor="maqam-search" className="sr-only">
            Search maqamat
          </Label>
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="maqam-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by Arabic or English name…"
            className="pl-9"
          />
        </div>

        {isAdmin && (
          <ButtonLink href="/maqamat/new" className="ml-auto gap-1.5">
            <PlusCircle className="size-4" /> Add maqam
          </ButtonLink>
        )}
      </div>

      {error ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center">
          <p className="font-display text-xl font-semibold">Could not load maqamat</p>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">{error}</p>
          <button
            onClick={() => setReloadKey((k) => k + 1)}
            className="mt-4 rounded-lg border border-gold/30 bg-gold-muted px-4 py-2 text-sm font-medium text-gold hover:bg-gold hover:text-gold-foreground"
          >
            Try again
          </button>
        </div>
      ) : loading && !items ? (
        <div className="flex items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center">
          <p className="text-sm text-muted-foreground">Loading maqamat…</p>
        </div>
      ) : items && items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center">
          <p className="font-display text-xl font-semibold">No maqamat found</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {query.trim()
              ? `Nothing matches “${query.trim()}”.`
              : 'The maqam library is empty.'}
          </p>
          {query.trim() && (
            <button
              onClick={() => setQuery('')}
              className="mt-4 rounded-lg border border-gold/30 bg-gold-muted px-4 py-2 text-sm font-medium text-gold hover:bg-gold hover:text-gold-foreground"
            >
              Clear search
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items?.map((item) => (
            <MaqamCard key={item.id} maqam={item} />
          ))}
        </div>
      )}
    </div>
  )
}
