import type { Charter } from '../types'
import { CHARTER_PRIORITY_OPTIONS, DEFAULT_CHARTER, charterFromStatements } from '../types'

interface CharterBuilderProps {
  charter: Charter
  onChange: (charter: Charter) => void
  disabled: boolean
}

export function CharterBuilder({ charter, onChange, disabled }: CharterBuilderProps) {
  const selected = charter.priorities
    .slice()
    .sort((a, b) => a.rank - b.rank)
    .map((p) => p.statement)

  const toggle = (statement: string) => {
    if (disabled) return

    if (selected.includes(statement)) {
      onChange(charterFromStatements(selected.filter((s) => s !== statement)))
      return
    }

    if (selected.length >= 3) return
    onChange(charterFromStatements([...selected, statement]))
  }

  const useDemoCharter = () => onChange(DEFAULT_CHARTER)
  const clear = () => onChange(charterFromStatements([]))

  return (
    <section className="charter-builder">
      <header className="charter-builder-header">
        <div>
          <h2>Build your Patient Charter</h2>
          <p className="charter-builder-subtitle">
            Pick three priorities in order — rank #1 is most important. APO checks every
            recommendation against these.
          </p>
        </div>
        <div className="charter-builder-actions">
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={useDemoCharter}
            disabled={disabled}
          >
            Use demo charter
          </button>
          {selected.length > 0 && (
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={clear}
              disabled={disabled}
            >
              Clear
            </button>
          )}
        </div>
      </header>

      <div className="charter-options">
        {CHARTER_PRIORITY_OPTIONS.map((option) => {
          const index = selected.indexOf(option)
          const isSelected = index >= 0
          const rank = isSelected ? index + 1 : null

          return (
            <button
              key={option}
              type="button"
              className={`charter-option ${isSelected ? 'charter-option--selected' : ''}`}
              onClick={() => toggle(option)}
              disabled={disabled || (!isSelected && selected.length >= 3)}
            >
              {rank && <span className="charter-option-rank">#{rank}</span>}
              <span>{option}</span>
            </button>
          )
        })}
      </div>

      <p className="charter-builder-hint">
        {selected.length}/3 selected
        {selected.length < 3 && ' — select three before running APO'}
      </p>
    </section>
  )
}
