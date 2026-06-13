import { useState, type ReactNode } from 'react'

interface CollapsibleProps {
  title: string
  children: ReactNode
  defaultOpen?: boolean
  badge?: string
}

export function Collapsible({ title, children, defaultOpen = false, badge }: CollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <section className="collapsible">
      <button
        type="button"
        className="collapsible-trigger"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className="collapsible-title">{title}</span>
        {badge && <span className="collapsible-badge">{badge}</span>}
        <span className="collapsible-chevron" aria-hidden>
          {open ? '−' : '+'}
        </span>
      </button>
      {open && <div className="collapsible-body">{children}</div>}
    </section>
  )
}
