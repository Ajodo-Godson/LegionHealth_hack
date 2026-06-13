import type { AgentLogEntry } from '../types'

const AGENT_LABELS: Record<string, string> = {
  executive: 'Executive',
  research: 'Research',
  insurance: 'Insurance',
  provider: 'Provider',
  provider_a: 'Provider A',
  provider_b: 'Provider B',
  provider_c: 'Provider C',
  contradiction_detector: 'Contradiction Detector',
  voice: 'Voice Executor',
  synthesis: 'Synthesis',
  charter_check: 'Charter Check',
}

const PARALLEL_AGENTS = new Set(['insurance', 'provider_a', 'provider_b'])

interface AgentFeedProps {
  events: AgentLogEntry[]
  status: string
  usingMock: boolean
  backendMode?: 'live' | 'stub' | 'offline' | null
}

export function AgentFeed({ events, status, usingMock, backendMode }: AgentFeedProps) {
  const nonVoiceEvents = events.filter((e) => e.agent !== 'voice')

  return (
    <section className="panel agent-feed-panel">
      <header className="panel-header">
        <div className="panel-header-row">
          <h2>Agent Activity</h2>
          <div className="feed-badges">
            {backendMode === 'stub' && <span className="mock-badge">Stub backend</span>}
            {backendMode === 'live' && <span className="live-badge">Grok live</span>}
            {usingMock && <span className="mock-badge">Frontend mock</span>}
          </div>
        </div>
        <StatusIndicator status={status} />
      </header>

      <div className="agent-feed">
        {nonVoiceEvents.length === 0 && status === 'idle' && (
          <p className="feed-empty">Press Run APO to start live verification.</p>
        )}
        {nonVoiceEvents.length === 0 && status !== 'idle' && (
          <p className="feed-empty feed-loading">Agents initializing…</p>
        )}
        {nonVoiceEvents.map((entry, i) => (
          <FeedEntry key={`${entry.timestamp}-${i}`} entry={entry} />
        ))}
      </div>
    </section>
  )
}

function FeedEntry({ entry }: { entry: AgentLogEntry }) {
  const label = AGENT_LABELS[entry.agent] ?? entry.agent
  const time = formatTime(entry.timestamp)
  const isParallel =
    PARALLEL_AGENTS.has(entry.agent) &&
    (entry.action === 'running' || entry.action === 'completed')
  const isReroute = entry.agent === 'executive' && entry.action === 'reroute'
  const isReconciling = entry.agent === 'executive' && entry.action === 'reconciling'
  const isConflict =
    entry.agent === 'contradiction_detector' && entry.action === 'completed'

  return (
    <article
      className={`feed-entry ${isParallel ? 'feed-entry--parallel' : ''} ${isReroute ? 'feed-entry--reroute' : ''} ${isReconciling ? 'feed-entry--reconciling' : ''} ${isConflict ? 'feed-entry--conflict' : ''}`}
    >
      <div className="feed-entry-header">
        <span className="feed-agent">{label}</span>
        <span className="feed-action">{entry.action.replace(/_/g, ' ')}</span>
        <time className="feed-time">{time}</time>
      </div>
      <p className="feed-output">{entry.output}</p>
    </article>
  )
}

function StatusIndicator({ status }: { status: string }) {
  const labels: Record<string, string> = {
    idle: 'Ready',
    connecting: 'Connecting…',
    streaming: 'Live verification…',
    awaiting_consent: 'Awaiting your authorization',
    done: 'Complete',
    error: 'Error',
  }

  return (
    <span className={`status-pill status-${status}`}>
      {labels[status] ?? status}
    </span>
  )
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return iso
  }
}
