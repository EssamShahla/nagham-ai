import Link from 'next/link'
import { NaghamLogo } from '@/components/nagham-logo'

export function MarketingFooter() {
  return (
    <footer className="border-t border-border/60">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 md:grid-cols-4 md:px-6">
        <div className="md:col-span-2">
          <NaghamLogo />
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground">
            An intelligent companion for Oriental and Arabic musicians — discover repertoire by
            maqam, mood and meaning, powered by an AI that understands the language of tarab.
          </p>
        </div>
        <div>
          <h4 className="mb-3 text-sm font-semibold">Explore</h4>
          <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
            <li>
              <Link href="/discover" className="hover:text-foreground">
                Discover
              </Link>
            </li>
            <li>
              <Link href="/assistant" className="hover:text-foreground">
                AI Assistant
              </Link>
            </li>
            <li>
              <Link href="/songs" className="hover:text-foreground">
                Song Library
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <h4 className="mb-3 text-sm font-semibold">Account</h4>
          <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
            <li>
              <Link href="/login" className="hover:text-foreground">
                Sign in
              </Link>
            </li>
            <li>
              <Link href="/register" className="hover:text-foreground">
                Create account
              </Link>
            </li>
            <li>
              <Link href="/profile" className="hover:text-foreground">
                Profile
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-border/60">
        <div className="mx-auto max-w-6xl px-4 py-5 text-xs text-muted-foreground md:px-6">
          © {new Date().getFullYear()} Nagham AI. Preserving the maqam tradition through technology.
        </div>
      </div>
    </footer>
  )
}
