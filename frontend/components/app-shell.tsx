'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Sparkles,
  Music,
  Music4,
  Compass,
  PlusCircle,
  UserRound,
  ScanSearch,
  Menu,
  X,
  Search,
} from 'lucide-react'
import { NaghamLogo } from '@/components/nagham-logo'
import { UserMenu } from '@/components/user-menu'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/discover', label: 'Discover', icon: Compass },
  { href: '/assistant', label: 'AI Assistant', icon: Sparkles },
  { href: '/songs', label: 'Songs', icon: Music },
  { href: '/maqamat', label: 'Maqamat', icon: Music4 },
  { href: '/semantic', label: 'Lyrics Search', icon: ScanSearch },
  { href: '/add-song', label: 'Add Song', icon: PlusCircle },
  { href: '/profile', label: 'Profile', icon: UserRound },
]

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map((item) => {
        const active =
          pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
              active
                ? 'bg-gold-muted text-gold'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground',
            )}
          >
            {active && (
              <span className="absolute top-1/2 left-0 h-5 w-0.5 -translate-y-1/2 rounded-full bg-gold" />
            )}
            <item.icon className="size-[18px]" />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-border bg-sidebar px-4 py-6 lg:flex">
        <Link href="/" className="px-2">
          <NaghamLogo />
        </Link>
        <div className="mt-8 flex-1">
          <NavLinks />
        </div>
        <div className="rounded-xl border border-gold/20 bg-gold-muted/40 p-4">
          <p className="font-display text-base font-semibold">Ask Nagham</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Discover repertoire through natural conversation.
          </p>
          <Link
            href="/assistant"
            className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-gold hover:underline"
          >
            <Sparkles className="size-4" /> Open Assistant
          </Link>
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <div className="animate-rise absolute inset-y-0 left-0 w-72 border-r border-border bg-sidebar px-4 py-6">
            <div className="flex items-center justify-between px-2">
              <NaghamLogo />
              <button
                onClick={() => setMobileOpen(false)}
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent"
                aria-label="Close menu"
              >
                <X className="size-5" />
              </button>
            </div>
            <div className="mt-8">
              <NavLinks onNavigate={() => setMobileOpen(false)} />
            </div>
          </div>
        </div>
      )}

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur-md md:px-8">
          <button
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-2 text-muted-foreground hover:bg-accent lg:hidden"
            aria-label="Open menu"
          >
            <Menu className="size-5" />
          </button>

          <form action="/songs" className="relative hidden max-w-md flex-1 md:block">
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              name="q"
              placeholder="Search songs, maqamat, artists..."
              className="h-10 pl-9"
            />
          </form>

          <div className="ml-auto">
            <UserMenu />
          </div>
        </header>

        <main className="flex-1 px-4 py-6 md:px-8 md:py-10">{children}</main>
      </div>
    </div>
  )
}
