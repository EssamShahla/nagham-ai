import * as React from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

type SelectProps = React.ComponentProps<'select'>

function Select({ className, children, ...props }: SelectProps) {
  return (
    <div className="relative">
      <select
        data-slot="select"
        className={cn(
          'h-11 w-full appearance-none rounded-lg border border-input bg-background/40 px-3.5 pr-9 text-sm text-foreground shadow-sm transition-colors outline-none',
          'focus-visible:border-gold/60 focus-visible:ring-2 focus-visible:ring-ring',
          'disabled:cursor-not-allowed disabled:opacity-50',
          '[&>option]:bg-popover [&>option]:text-popover-foreground',
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted-foreground" />
    </div>
  )
}

export { Select }
