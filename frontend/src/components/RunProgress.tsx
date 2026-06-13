import type { AgentLogEntry } from '../types'

interface RunProgressProps {
  status: string
  events: AgentLogEntry[]
}

export function RunProgress({ status, events }: RunProgressProps) {
  if (status !== 'connecting' && status !== 'streaming' && status !== 'awaiting_consent') {
    return null
  }

  const latest = [...events].reverse().find((e) => e.agent !== 'voice' && e.output?.trim())
  const message =
    status === 'awaiting_consent'
      ? 'Waiting for you to authorize the clinic verification call.'
      : latest?.output ?? 'Starting agents…'

  return (
    <div className="run-progress" role="status">
      <span className="run-progress-dot" aria-hidden />
      <p>{message}</p>
    </div>
  )
}
