'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Mail, Lock } from 'lucide-react'

import { AuthShell } from '@/components/auth-shell'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export default function LoginPage() {
  const router = useRouter()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    setLoading(true)
    setError('')

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || 'Login failed')
        return
      }

      localStorage.setItem('access_token', data.access_token)

      router.push('/dashboard')
    } catch {
      setError('Unable to connect to the server')
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
      <h1 className="font-display text-3xl font-semibold">
        Welcome back
      </h1>

      <p className="mt-2 text-sm text-muted-foreground">
        Sign in to continue discovering repertoire.
      </p>

      <form
        onSubmit={handleSubmit}
        className="mt-8 flex flex-col gap-5"
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
          <Label htmlFor="password">Password</Label>

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