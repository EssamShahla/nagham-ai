'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Mail, Lock } from 'lucide-react'

import { AuthShell } from '@/components/auth-shell'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { GoogleButton } from '@/components/auth/google-button'
import { AuthDivider } from '@/components/auth/auth-divider'
import { api, ApiError, formatValidationError } from '@/lib/api'

interface LoginResponse {
  access_token: string
  token_type: string
}

/** Reads one-time query params the backend's Google OAuth redirects add
 * (`google_error`, `google_link_token`). Isolated in its own component
 * because `useSearchParams` requires a Suspense boundary. */
function GoogleLoginParams({
  onGoogleError,
  onLinkToken,
}: {
  onGoogleError: (message: string) => void
  onLinkToken: (token: string) => void
}) {
  const searchParams = useSearchParams()

  useEffect(() => {
    const googleError = searchParams.get('google_error')
    const token = searchParams.get('google_link_token')

    if (googleError) onGoogleError(googleError)
    if (token) onLinkToken(token)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return null
}

export default function LoginPage() {
  const router = useRouter()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [linkToken, setLinkToken] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    setLoading(true)
    setError('')

    try {
      const data = await api<LoginResponse>('/auth/login', {
        method: 'POST',
        body: { email, password },
      })

      localStorage.setItem('access_token', data.access_token)

      if (linkToken) {
        try {
          await api('/auth/google/link', {
            method: 'POST',
            auth: true,
            body: { link_token: linkToken },
          })
        } catch {
          // The password login itself succeeded -- don't block the user
          // out over a failed linking attempt, just let them retry later.
        }
      }

      router.push('/dashboard')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status === 422
            ? formatValidationError(err.detail)
            : typeof err.detail === 'string'
              ? err.detail
              : 'Login failed',
        )
      } else {
        setError('Unable to connect to the server')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      quote={{
        text: 'Music is the language of the soul, and the maqam is its grammar.',
        source: 'Arabic musical proverb',
      }}
    >
      <Suspense fallback={null}>
        <GoogleLoginParams
          onGoogleError={setError}
          onLinkToken={setLinkToken}
        />
      </Suspense>

      <h1 className="font-display text-3xl font-semibold">
        Welcome back
      </h1>

      <p className="mt-2 text-sm text-muted-foreground">
        Sign in to continue discovering repertoire.
      </p>

      {linkToken && (
        <p className="mt-4 rounded-lg border border-gold/25 bg-gold-muted px-3 py-2.5 text-sm text-foreground">
          An account already exists with that email. Sign in with your password to link your Google account to it.
        </p>
      )}

      <div className="mt-8">
        <GoogleButton />
      </div>

      <AuthDivider />

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-5"
      >
        {/* Email */}
        <div>
          <Label htmlFor="email">Email</Label>

          <div className="relative">
            <Mail className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />

            <Input
              id="email"
              name="email"
              type="email"
              placeholder="you@example.com"
              className="pl-9"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        </div>

        {/* Password */}
        <div>
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link
              href="/forgot-password"
              className="text-xs font-medium text-gold hover:underline"
            >
              Forgot password?
            </Link>
          </div>

          <div className="relative">
            <Lock className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />

            <Input
              id="password"
              name="password"
              type="password"
              placeholder="••••••••"
              className="pl-9"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
        </div>

        {/* Error message */}
        {error && (
          <p className="text-sm text-red-500">
            {error}
          </p>
        )}

        {/* Submit button */}
        <Button
          type="submit"
          className="mt-1 h-11 w-full text-sm"
          disabled={loading}
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-muted-foreground">
        New to Nagham?{' '}
        <Link
          href="/register"
          className="font-medium text-gold hover:underline"
        >
          Create an account
        </Link>
      </p>
    </AuthShell>
  )
}
