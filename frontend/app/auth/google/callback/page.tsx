'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { AlertTriangle, Loader2 } from 'lucide-react'

import { AuthShell } from '@/components/auth-shell'
import { api, ApiError } from '@/lib/api'

interface ExchangeResponse {
  access_token: string
  token_type: string
}

function GoogleCallbackInner() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [error, setError] = useState('')

  useEffect(() => {
    const code = searchParams.get('code')

    if (!code) {
      setError('Google did not return a sign-in code. Please try again.')
      return
    }

    let cancelled = false

    async function run() {
      try {
        const data = await api<ExchangeResponse>('/auth/google/exchange', {
          method: 'POST',
          body: { code },
        })

        if (cancelled) return

        localStorage.setItem('access_token', data.access_token)
        router.push('/dashboard')
      } catch (err) {
        if (cancelled) return

        setError(
          err instanceof ApiError && typeof err.detail === 'string'
            ? err.detail
            : 'Could not complete Google sign-in. Please try again.',
        )
      }
    }

    void run()

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (error) {
    return (
      <>
        <div className="flex size-14 items-center justify-center rounded-2xl border border-destructive/30 bg-destructive/10 text-destructive">
          <AlertTriangle className="size-7" />
        </div>

        <h1 className="mt-6 font-display text-3xl font-semibold">Sign-in failed</h1>

        <p className="mt-2 text-sm text-muted-foreground">{error}</p>

        <Link
          href="/login"
          className="mt-6 inline-block text-sm font-medium text-gold hover:underline"
        >
          Back to sign in
        </Link>
      </>
    )
  }

  return (
    <>
      <div className="flex size-14 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
        <Loader2 className="size-7 animate-spin" />
      </div>

      <h1 className="mt-6 font-display text-3xl font-semibold">Signing you in...</h1>

      <p className="mt-2 text-sm text-muted-foreground">
        Just a moment while we confirm your Google account.
      </p>
    </>
  )
}

export default function GoogleCallbackPage() {
  return (
    <AuthShell>
      <Suspense
        fallback={
          <div className="flex size-14 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
            <Loader2 className="size-7 animate-spin" />
          </div>
        }
      >
        <GoogleCallbackInner />
      </Suspense>
    </AuthShell>
  )
}
