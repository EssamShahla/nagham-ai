import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export function SectionHeading({
  eyebrow,
  title,
  description,
  actionLabel,
  actionHref,
}: {
  eyebrow?: string
  title: string
  description?: string
  actionLabel?: string
  actionHref?: string
}) {
  return (
    <div className="mb-6 flex items-end justify-between gap-4">
      <div>
        {eyebrow && (
          <p className="mb-1.5 text-xs font-semibold tracking-[0.2em] text-gold uppercase">
            {eyebrow}
          </p>
        )}
        <h2 className="font-display text-2xl font-semibold text-balance md:text-3xl">{title}</h2>
        {description && (
          <p className="mt-2 max-w-xl text-sm text-muted-foreground md:text-base">{description}</p>
        )}
      </div>
      {actionLabel && actionHref && (
        <Link
          href={actionHref}
          className="hidden shrink-0 items-center gap-1.5 text-sm font-medium text-gold hover:underline sm:inline-flex"
        >
          {actionLabel}
          <ArrowRight className="size-4" />
        </Link>
      )}
    </div>
  )
}
