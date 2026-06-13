import type { StreamStatus } from '../types'

interface AppTopBarProps {
  status: StreamStatus
  onReset: () => void
  isRunning: boolean
  showReset: boolean
}

export function AppTopBar({ status, onReset, isRunning, showReset }: AppTopBarProps) {
  const statusNote =
    status === 'streaming' || status === 'connecting'
      ? 'Working…'
      : status === 'awaiting_consent'
        ? 'Needs your OK'
        : status === 'done'
          ? 'Done'
          : null

  return (
    <header className="top-bar top-bar--minimal">
      <div className="top-bar-brand">
        <span className="top-bar-logo">APO</span>
        <span className="top-bar-title">Autonomous Patient Organization</span>
      </div>

      {statusNote && <span className={`top-bar-note top-bar-note--${status}`}>{statusNote}</span>}

      {showReset && (
        <button
          type="button"
          className="btn btn-secondary btn-small"
          onClick={onReset}
          disabled={isRunning}
        >
          New run
        </button>
      )}
    </header>
  )
}
