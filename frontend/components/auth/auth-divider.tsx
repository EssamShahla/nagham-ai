export function AuthDivider({ label = 'or' }: { label?: string }) {
  return (
    <div className="my-6 flex items-center gap-3">
      <div className="h-px flex-1 bg-border" />
      <span className="text-xs tracking-wide text-muted-foreground uppercase">{label}</span>
      <div className="h-px flex-1 bg-border" />
    </div>
  )
}
