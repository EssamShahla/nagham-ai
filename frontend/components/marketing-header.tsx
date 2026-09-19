import Link from 'next/link'
import { NaghamLogo } from '@/components/nagham-logo'
import { ButtonLink } from '@/components/ui/button-link'

const LINKS = [
  { href: '#features', label: 'Features' },
  { href: '#maqamat', label: 'Maqamat' },
  { href: '#songs', label: 'Songs' },
]

export function MarketingHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/70 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 md:px-6">
        <Link href="/">
          <NaghamLogo />
        </Link>
        <nav className="hidden items-center gap-8 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <ButtonLink
            href="/login"
            variant="ghost"
            className="hidden h-10 px-4 sm:inline-flex"
          >
            Sign in
          </ButtonLink>
          <ButtonLink href="/register" className="h-10 px-4">
            Get started
          </ButtonLink>
        </div>
      </div>
    </header>
  )
}
