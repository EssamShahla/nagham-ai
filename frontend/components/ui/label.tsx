import * as React from 'react'
import { cn } from '@/lib/utils'

function Label({ className, ...props }: React.ComponentProps<'label'>) {
  return (
    <label
      data-slot="label"
      className={cn(
        'mb-2 flex items-center gap-1.5 text-sm font-medium text-foreground/90 select-none',
        className,
      )}
      {...props}
    />
  )
}

export { Label }
