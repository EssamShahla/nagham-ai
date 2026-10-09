'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { MailCheck } from 'lucide-react'

import { AuthShell } from '@/components/auth-shell'
import { cn } from '@/lib/utils'
import { api, ApiError } from '@/lib/api'
import type { UserResponse } from '@/lib/types'

export default function VerifyPage() {
  const router = useRouter()

  const [digits, setDigits] = useState<string[]>(Array(6).fill(''))
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [cooldown, setCooldown] = useState(0)

  const inputs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    const savedEmail = localStorage.getItem('verification_email')

    if (!savedEmail) {
      router.push('/register')
      return
    }

    setEmail(savedEmail)
  }, [router])

  useEffect(() => {
    if (cooldown <= 0) return

    const timer = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }

        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [cooldown])

  function setDigit(index: number, value: string) {
    const clean = value.replace(/\D/g, '').slice(-1)

    setDigits((prev) => {
      const next = [...prev]
      next[index] = clean
      return next
    })

    if (clean && index < 5) {
      inputs.current[index + 1]?.focus()
    }
  }

  function onKeyDown(
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>
  ) {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputs.current[index - 1]?.focus()
    }
  }

  function onPaste(e: React.ClipboardEvent) {
    e.preventDefault()

    const text = e.clipboardData
      .getData('text')
      .replace(/\D/g, '')
      .slice(0, 6)

    if (!text) return

    const next = Array(6).fill('')

    text.split('').forEach((digit, index) => {
      next[index] = digit
    })

    setDigits(next)

    inputs.current[Math.min(text.length, 5)]?.focus()
  }

  const complete = digits.every((digit) => digit !== '')

  async function handleVerify() {
    if (!complete || !email) return

    setLoading(true)
    setError('')
    setMessage('')

    const otp = digits.join('')

    try {
      await api<UserResponse>('/auth/verify-otp', {
        method: 'POST',
        body: { email, otp },
      })

      localStorage.removeItem('verification_email')

      router.push('/login')
    } catch (err) {
      setError(
        err instanceof ApiError && typeof err.detail === 'string'
          ? err.detail
          : 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleResend() {
    if (!email || resending || cooldown > 0) return

    setResending(true)
    setError('')
    setMessage('')

    try {
      await api('/auth/resend-otp', {
        method: 'POST',
        body: { email },
      })

      setMessage('A new verification code has been sent.')
      setCooldown(60)
      setDigits(Array(6).fill(''))
      inputs.current[0]?.focus()
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        const detailText = typeof err.detail === 'string' ? err.detail : ''
        const match = detailText.match(/(\d+)/)
        const remainingSeconds = match ? Number(match[1]) : 60

        setCooldown(remainingSeconds)
        setError(`Please wait ${remainingSeconds} seconds before requesting another code.`)
      } else if (err instanceof ApiError && typeof err.detail === 'string') {
        setError(err.detail)
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setResending(false)
    }
  }

  return (
    <AuthShell
      quote={{
        text: 'Patience is the melody that carries the longest note.',
        source: 'Maqam wisdom',
      }}
    >
      <div className="flex size-14 items-center justify-center rounded-2xl border border-gold/25 bg-gold-muted text-gold">
        <MailCheck className="size-7" />
      </div>

      <h1 className="mt-6 font-display text-3xl font-semibold">
        Verify your email
      </h1>

      <p className="mt-2 text-sm text-muted-foreground">
        We sent a 6-digit code to{' '}
        <span className="font-medium text-foreground">
          {email || 'your email'}
        </span>
        . Enter it below.
      </p>

      <div
        className="mt-8 flex justify-between gap-2"
        onPaste={onPaste}
      >
        {digits.map((digit, i) => (
          <input
            key={i}
            ref={(el) => {
              inputs.current[i] = el
            }}
            value={digit}
            onChange={(e) => setDigit(i, e.target.value)}
            onKeyDown={(e) => onKeyDown(i, e)}
            inputMode="numeric"
            maxLength={1}
            aria-label={`Digit ${i + 1}`}
            className={cn(
              'h-14 w-full rounded-xl border bg-background/40 text-center font-display text-2xl font-semibold text-foreground shadow-sm transition-colors outline-none',
              'focus-visible:border-gold/60 focus-visible:ring-2 focus-visible:ring-ring',
              digit ? 'border-gold/50' : 'border-input',
            )}
          />
        ))}
      </div>

      {error && (
        <p className="mt-4 text-sm text-red-500">
          {error}
        </p>
      )}

      {message && (
        <p className="mt-4 text-sm text-green-600">
          {message}
        </p>
      )}

      <button
        onClick={handleVerify}
        disabled={!complete || loading}
        className={cn(
          'mt-8 h-11 w-full rounded-lg text-sm font-medium transition-colors',
          complete && !loading
            ? 'bg-gold text-gold-foreground hover:bg-gold/90'
            : 'cursor-not-allowed bg-secondary text-muted-foreground',
        )}
      >
        {loading ? 'Verifying...' : 'Verify & continue'}
      </button>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Didn&apos;t receive it?{' '}

        <button
          onClick={handleResend}
          disabled={resending || cooldown > 0}
          className={cn(
            'font-medium text-gold hover:underline',
            (resending || cooldown > 0) &&
              'cursor-not-allowed opacity-60'
          )}
        >
          {resending
            ? 'Sending...'
            : cooldown > 0
              ? `Resend in ${cooldown}s`
              : 'Resend code'}
        </button>
      </p>

      <p className="mt-3 text-center text-sm">
        <Link
          href="/login"
          className="text-muted-foreground hover:text-foreground"
        >
          Back to sign in
        </Link>
      </p>
    </AuthShell>
  )
}