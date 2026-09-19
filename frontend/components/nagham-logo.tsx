import { cn } from '@/lib/utils'

export function NaghamMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 40 40"
      className={cn('size-9', className)}
      fill="none"
      aria-hidden="true"
    >
      <circle cx="20" cy="20" r="18.5" stroke="var(--gold)" strokeWidth="1.2" opacity="0.55" />
      {/* Stylized sound wave / maqam contour */}
      <path
        d="M7 20c2.4 0 2.4-7 4.8-7s2.4 14 4.8 14 2.4-11 4.8-11 2.4 8 4.8 8 2.4-4 4.8-4"
        stroke="var(--gold)"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="20" cy="20" r="2.4" fill="var(--gold)" />
    </svg>
  )
}

export function NaghamLogo({
  className,
  showText = true,
}: {
  className?: string
  showText?: boolean
}) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <NaghamMark />
      {showText && (
        <span className="flex flex-col leading-none">
          <span className="font-display text-lg font-semibold tracking-tight text-foreground">
            Nagham <span className="text-gold">AI</span>
          </span>
          <span className="text-[10px] font-medium tracking-[0.22em] text-muted-foreground uppercase">
            Oriental Music
          </span>
        </span>
      )}
    </span>
  )
}
