import type { Charter, CharterPriority } from '../types'

interface CharterPanelProps {
  charter: Charter
  highlightedPriority?: number | null
}

export function CharterPanel({ charter, highlightedPriority }: CharterPanelProps) {
  const sorted = [...charter.priorities].sort((a, b) => a.rank - b.rank)

  return (
    <section className="panel charter-panel">
      <header className="panel-header">
        <h2>Patient Charter</h2>
        <p className="panel-subtitle">Three ranked priorities. Every recommendation is checked against these.</p>
      </header>

      <ol className="charter-list">
        {sorted.map((priority) => (
          <CharterItem
            key={priority.rank}
            priority={priority}
            highlighted={highlightedPriority === priority.rank}
          />
        ))}
      </ol>
    </section>
  )
}

function CharterItem({
  priority,
  highlighted,
}: {
  priority: CharterPriority
  highlighted: boolean
}) {
  return (
    <li className={`charter-item ${highlighted ? 'charter-item--highlighted' : ''}`}>
      <span className="charter-rank">#{priority.rank}</span>
      <span className="charter-statement">{priority.statement}</span>
      {highlighted && <span className="charter-flag-badge">Referenced</span>}
    </li>
  )
}
