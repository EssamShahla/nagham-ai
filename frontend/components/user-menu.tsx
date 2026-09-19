'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { LogOut, Settings, User } from 'lucide-react'
import { api } from '@/lib/api'
import type { UserResponse } from '@/lib/types'
import { cn } from '@/lib/utils'

export function UserMenu() {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [user, setUser] = useState<UserResponse | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  useEffect(() => {
    let cancelled = false
    const token = localStorage.getItem('access_token')

    if (!token) {
      router.replace('/login')
      return
    }

    async function loadCurrentUser() {
      try {
        const me = await api<UserResponse>('/auth/me', { auth: true })
        if (!cancelled) setUser(me)
      } catch {
        localStorage.removeItem('access_token')
        router.replace('/login')
      }
    }

    loadCurrentUser()
    return () => {
      cancelled = true
    }
  }, [router])

  const initials = (user?.name ?? '')
    .split(' ')
    .map((n) => n[0])
    .join('')

  function signOut() {
    localStorage.removeItem('access_token')
    router.replace('/login')
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2.5 rounded-full border border-border bg-card py-1 pr-3 pl-1 transition-colors hover:border-gold/40"
      >
        <span className="flex size-8 items-center justify-center rounded-full bg-gold text-sm font-semibold text-gold-foreground">
          {initials || '?'}
        </span>
        <span className="hidden text-sm font-medium sm:inline">{user?.name ?? 'Account'}</span>
      </button>

      {open && (
        <div
          role="menu"
          className="animate-rise absolute right-0 z-50 mt-2 w-56 overflow-hidden rounded-xl border border-border bg-popover p-1.5 shadow-xl shadow-black/40"
        >
          <div className="px-3 py-2">
            <p className="text-sm font-medium">{user?.name ?? ''}</p>
            <p className="truncate text-xs text-muted-foreground">{user?.email ?? ''}</p>
          </div>
          <div className="my-1 h-px bg-border" />
          {[
            { href: '/profile', label: 'My Profile', icon: User },
            { href: '/profile', label: 'Settings', icon: Settings },
          ].map((item, i) => (
            <Link
              key={i}
              href={item.href}
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/90 transition-colors hover:bg-accent"
            >
              <item.icon className="size-4 text-muted-foreground" />
              {item.label}
            </Link>
          ))}
          <div className="my-1 h-px bg-border" />
          <button
            type="button"
            role="menuitem"
            onClick={signOut}
            className={cn(
              'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/90 transition-colors hover:bg-accent',
            )}
          >
            <LogOut className="size-4 text-muted-foreground" />
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}