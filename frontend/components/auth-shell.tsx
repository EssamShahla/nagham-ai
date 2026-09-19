import Image from 'next/image'
import Link from 'next/link'
import { NaghamLogo } from '@/components/nagham-logo'

export function AuthShell({
  children,
  quote,
}: {
  children: React.ReactNode
  quote?: { text: string; source: string }
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Branded panel */}
      <div className="relative hidden overflow-hidden lg:block">
        <Image
          src="/hero-oud.png"
          alt=""
          fill
          className="object-cover"
          sizes="50vw"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-background/30" />
        <div className="relative flex h-full flex-col justify-between p-10">
          <Link href="/">
            <NaghamLogo />
          </Link>
          {quote && (
            <blockquote className="max-w-md">
              <p className="font-display text-2xl leading-snug text-balance">“{quote.text}”</p>
              <footer className="mt-3 text-sm text-gold">— {quote.source}</footer>
            </blockquote>
          )}
        </div>
      </div>

      {/* Form panel */}
      <div className="bg-vignette flex flex-col justify-center px-4 py-12 sm:px-8">
        <div className="mx-auto w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Link href="/">
              <NaghamLogo />
            </Link>
          </div>
          {children}
        </div>
      </div>
    </div>
  )
}
