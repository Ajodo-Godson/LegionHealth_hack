import { useCallback, useState } from 'react'

interface AgentPhoneTestPanelProps {
  enabled: boolean
  toNumber: string | null
  disabled: boolean
}

export function AgentPhoneTestPanel({ enabled, toNumber, disabled }: AgentPhoneTestPanelProps) {
  const [status, setStatus] = useState<'idle' | 'calling' | 'done' | 'error'>('idle')
  const [log, setLog] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleTest = useCallback(async () => {
    if (!enabled || disabled) return

    setStatus('calling')
    setLog([])
    setError(null)

    try {
      const res = await fetch('/api/agentphone/test-call', { method: 'POST' })
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || res.statusText)
      }
      if (!res.body) throw new Error('No response body')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finished = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() ?? ''

        for (const chunk of chunks) {
          const lines = chunk.split('\n')
          let eventType = 'message'
          let data = ''
          for (const line of lines) {
            if (line.startsWith('event:')) eventType = line.slice(6).trim()
            if (line.startsWith('data:')) data = line.slice(5).trim()
          }
          if (!data) continue

          const payload = JSON.parse(data) as Record<string, unknown>

          if (eventType === 'status' && typeof payload.message === 'string') {
            setLog((prev) => [...prev, payload.message as string])
          }
          if (eventType === 'transcript' && typeof payload.line === 'string') {
            setLog((prev) => [...prev, payload.line as string])
          }
          if (eventType === 'done') {
            if (typeof payload.message === 'string') {
              setLog((prev) => [...prev, payload.message as string])
            }
            finished = true
            setStatus('done')
          }
          if (eventType === 'error') {
            throw new Error(String(payload.message ?? 'Test call failed'))
          }
        }
      }

      if (!finished) setStatus('done')
    } catch (err) {
      setError((err as Error).message)
      setStatus('error')
    }
  }, [enabled, disabled])

  if (!enabled) return null

  return (
    <section className="agentphone-test">
      <div className="agentphone-test-header">
        <div>
          <h2>Test AgentPhone outbound call</h2>
          <p className="agentphone-test-subtitle">
            Places a real call to <strong>{toNumber ?? 'your configured number'}</strong> from{' '}
            <strong>+19897155384</strong> — no full APO run required. Answer and play clinic
            receptionist: &ldquo;We dropped BlueCross Silver PPO in March 2026.&rdquo;
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary btn-small"
          onClick={() => void handleTest()}
          disabled={disabled || status === 'calling'}
        >
          {status === 'calling' ? 'Calling…' : 'Test outbound call'}
        </button>
      </div>

      {error && (
        <p className="agentphone-test-error" role="alert">
          {error}
        </p>
      )}

      {log.length > 0 && (
        <ul className="agentphone-test-log">
          {log.map((line, i) => (
            <li key={`${i}-${line.slice(0, 24)}`}>{line}</li>
          ))}
        </ul>
      )}
    </section>
  )
}
