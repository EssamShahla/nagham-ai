'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { KeyRound, Lock, Mail, CheckCircle2 } from 'lucide-react'

import { AuthShell } from '@/components/auth-shell'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { api, ApiError, formatValidationError } from '@/lib/api'

type Step = 'request' | 'reset' | 'done'

export default function ForgotPasswordPage() {
  const router = useRouter()

  const [step, setStep] = useState<Step>('request')
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  async function handleRequestCode(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    setLoading(true)
    setError('')

    try {
      const data = await api<{ message: string }>('/auth/forgot-password', {
        method: 'POST',
        body: { email },
      })

      setInfo(data.message)
      setStep('reset')
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.status === 422
            ? formatValidationError(err.detail)
            : 'Something went wrong. Please try again.'
          : 'Unable to connect to the server',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleResetPassword(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    setError('')

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      await api('/auth/reset-password', {
        method: 'POST',
        body: { email, otp, new_password: newPassword },
      })

      setStep('done')
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.status === 422
            ? formatValidationError(err.detail)
            : typeof err.detail === 'string'
              ? err.detail
              : 'Something went wrong. Please try again.'
          : 'Unable to connect to the server',
      )
    } finally {
      setLoading(false)
    }
  }

  if (step === 'done') {
    return (
      <AuthShell>
        <div className="flex size-14 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
          <CheckCircle2 className="size-7" />
        </div>
        <h1 className="mt-6 font-display text-3xl font-semibold">Password reset</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Your password has been updated. You can now sign in with your new password.
        </p>
        <Button className="mt-8 h-11 w-full text-sm" onClick={() => router.push('/login')}>
          Back to sign in
        </Button>
      </AuthShell>
    )
  }

  if (step === 'reset') {
    return (
      <AuthShell>
        <div className="flex size-14 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
          <KeyRound className="size-7" />
        </div>

        <h1 className="mt-6 font-display text-3xl font-semibold">Enter your reset code</h1>

        <p className="mt-2 text-sm text-muted-foreground">{info}</p>

        <form onSubmit={handleResetPassword} className="mt-8 flex flex-col gap-5">
          <div>
            <Label htmlFor="otp">Reset code</Label>
            <Input
              id="otp"
              name="otp"
              inputMode="numeric"
              placeholder="123456"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              required
            />
          </div>

          <div>
            <Label htmlFor="new-password">New password</Label>
            <div className="relative">
              <Lock className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="new-password"
                name="new-password"
                type="password"
                placeholder="Create a new password"
                className="pl-9"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={6}
                required
              />
            </div>
          </div>

          <div>
            <Label htmlFor="confirm-password">Confirm new password</Label>
            <div className="relative">
              <Lock className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="confirm-password"
                name="confirm-password"
                type="password"
                placeholder="Re-enter your new password"
                className="pl-9"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={6}
                required
              />
            </div>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button type="submit" className="mt-1 h-11 w-full text-sm" disabled={loading}>
            {loading ? 'Resetting...' : 'Reset password'}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm">
          <button
            type="button"
            onClick={() => setStep('request')}
            className="text-muted-foreground hover:text-foreground"
          >
            Use a different email
          </button>
        </p>
      </AuthShell>
    )
  }

  return (
    <AuthShell>
      <div className="flex size-14 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
        <KeyRound className="size-7" />
      </div>

      <h1 className="mt-6 font-display text-3xl font-semibold">Reset your password</h1>

      <p className="mt-2 text-sm text-muted-foreground">
        Enter your account email and we&apos;ll send you a code to reset your password.
      </p>

      <form onSubmit={handleRequestCode} className="mt-8 flex flex-col gap-5">
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

        {error && <p className="text-sm text-red-500">{error}</p>}

        <Button type="submit" className="mt-1 h-11 w-full text-sm" disabled={loading}>
          {loading ? 'Sending...' : 'Send reset code'}
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-muted-foreground">
        <Link href="/login" className="font-medium text-gold hover:underline">
          Back to sign in
        </Link>
      </p>
    </AuthShell>
  )
}
