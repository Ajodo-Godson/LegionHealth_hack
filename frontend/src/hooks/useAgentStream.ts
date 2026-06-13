import { useCallback, useEffect, useRef, useState } from 'react'
import {
  fetchHealth,
  fetchPlanWithRetry,
  startRun,
  streamUrl,
  submitVoiceConsent,
} from '../api/client'
import type {
  AgentLogEntry,
  Charter,
  PatientRecords,
  Plan,
  StreamStatus,
  VoiceConsentRequest,
} from '../types'
import { MOCK_PLAN, replayMockEvents } from '../mocks/demoEvents'

interface UseAgentStreamResult {
  events: AgentLogEntry[]
  plan: Plan | null
  status: StreamStatus
  error: string | null
  usingMock: boolean
  backendMode: 'live' | 'stub' | 'offline' | null
  backendDir: string | null
  twilioEnabled: boolean
  voiceConsentRequest: VoiceConsentRequest | null
  run: (diagnosis: string, charter: Charter, records?: PatientRecords | null) => Promise<void>
  respondToVoiceConsent: (granted: boolean, useTwilio: boolean) => Promise<void>
  reset: () => void
}

export function useAgentStream(): UseAgentStreamResult {
  const [events, setEvents] = useState<AgentLogEntry[]>([])
  const [plan, setPlan] = useState<Plan | null>(null)
  const [status, setStatus] = useState<StreamStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [usingMock, setUsingMock] = useState(false)
  const [backendMode, setBackendMode] = useState<'live' | 'stub' | 'offline' | null>(null)
  const [backendDir, setBackendDir] = useState<string | null>(null)
  const [twilioEnabled, setTwilioEnabled] = useState(false)
  const [voiceConsentRequest, setVoiceConsentRequest] = useState<VoiceConsentRequest | null>(
    null,
  )
  const abortRef = useRef<AbortController | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const runIdRef = useRef<string | null>(null)
  const consentResolverRef = useRef<
    ((result: { granted: boolean; useTwilio: boolean }) => void) | null
  >(null)

  useEffect(() => {
    void fetchHealth().then((health) => {
      if (!health) {
        setBackendMode('offline')
        return
      }
      setBackendMode(health.mode === 'live' ? 'live' : 'stub')
      setBackendDir(health.backend_dir ?? null)
      setTwilioEnabled(Boolean(health.twilio_enabled))
    })
  }, [])

  const refreshBackendHealth = useCallback(async () => {
    const health = await fetchHealth()
    if (!health) {
      setBackendMode('offline')
      setBackendDir(null)
      setTwilioEnabled(false)
      return false
    }
    setBackendMode(health.mode === 'live' ? 'live' : 'stub')
    setBackendDir(health.backend_dir ?? null)
    setTwilioEnabled(Boolean(health.twilio_enabled))
    return health.status === 'ok'
  }, [])

  const cleanup = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    eventSourceRef.current?.close()
    eventSourceRef.current = null
    runIdRef.current = null
    consentResolverRef.current = null
  }, [])

  const reset = useCallback(() => {
    cleanup()
    setEvents([])
    setPlan(null)
    setStatus('idle')
    setError(null)
    setUsingMock(false)
    setVoiceConsentRequest(null)
  }, [cleanup])

  const appendEvent = useCallback((entry: AgentLogEntry) => {
    setEvents((prev) => [...prev, entry])
  }, [])

  const waitForMockConsent = useCallback((): Promise<{ granted: boolean; useTwilio: boolean }> => {
    setVoiceConsentRequest({
      clinic_name: 'Metro Pulmonary & Sleep',
      clinic_phone: '(404) 555-0291',
      purpose:
        'Verify insurance coverage for sleep apnea treatment (informational only — not authorizing treatment)',
    })
    setStatus('awaiting_consent')
    return new Promise((resolve) => {
      consentResolverRef.current = resolve
    })
  }, [])

  const runMock = useCallback(
    async (signal: AbortSignal) => {
      setUsingMock(true)
      setStatus('streaming')

      try {
        await replayMockEvents(
          appendEvent,
          () => setPlan(MOCK_PLAN),
          () => setStatus('done'),
          signal,
          waitForMockConsent,
        )
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setError('Mock replay failed')
          setStatus('error')
        }
      }
    },
    [appendEvent, waitForMockConsent],
  )

  const loadPlan = useCallback(async (runId: string) => {
    try {
      const fetchedPlan = await fetchPlanWithRetry(runId)
      setPlan(fetchedPlan)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  const runLive = useCallback(
    async (runId: string, signal: AbortSignal) => {
      setUsingMock(false)
      runIdRef.current = runId
      setStatus('connecting')

      return new Promise<void>((resolve, reject) => {
        const es = new EventSource(streamUrl(runId))
        eventSourceRef.current = es
        let finished = false

        es.addEventListener('agent_log', (e) => {
          try {
            const entry = JSON.parse(e.data) as AgentLogEntry
            appendEvent(entry)
            setStatus('streaming')
          } catch {
            /* ignore malformed events */
          }
        })

        es.addEventListener('voice_consent_required', (e) => {
          try {
            const payload = JSON.parse(e.data) as VoiceConsentRequest
            setVoiceConsentRequest(payload)
            setStatus('awaiting_consent')
          } catch {
            /* ignore malformed events */
          }
        })

        es.addEventListener('plan_ready', () => {
          void loadPlan(runId)
        })

        es.addEventListener('done', () => {
          finished = true
          es.close()
          eventSourceRef.current = null
          setStatus('done')
          setVoiceConsentRequest(null)
          void loadPlan(runId)
          resolve()
        })

        es.onerror = () => {
          if (finished || signal.aborted) return
          es.close()
          eventSourceRef.current = null
          setError('SSE connection lost')
          setStatus('error')
          reject(new Error('SSE connection lost'))
        }

        signal.addEventListener('abort', () => {
          finished = true
          es.close()
          eventSourceRef.current = null
        })
      })
    },
    [appendEvent, loadPlan],
  )

  const respondToVoiceConsent = useCallback(
    async (granted: boolean, useTwilio: boolean) => {
      setVoiceConsentRequest(null)
      setStatus('streaming')

      if (consentResolverRef.current) {
        consentResolverRef.current({ granted, useTwilio })
        consentResolverRef.current = null
        return
      }

      const runId = runIdRef.current
      if (!runId) return

      try {
        await submitVoiceConsent(runId, granted, useTwilio)
      } catch (err) {
        setError((err as Error).message)
        setStatus('error')
      }
    },
    [],
  )

  const run = useCallback(
    async (diagnosis: string, charter: Charter, records?: PatientRecords | null) => {
      cleanup()
      setEvents([])
      setPlan(null)
      setError(null)
      setUsingMock(false)
      setVoiceConsentRequest(null)
      setStatus('connecting')

      const controller = new AbortController()
      abortRef.current = controller

      const backendUp = await refreshBackendHealth()

      if (!backendUp) {
        await runMock(controller.signal)
        return
      }

      try {
        const { run_id } = await startRun(diagnosis, charter, records)
        await runLive(run_id, controller.signal)
      } catch (err) {
        if ((err as Error).name === 'AbortError') return
        setUsingMock(true)
        setEvents([])
        setPlan(null)
        await runMock(controller.signal)
      }
    },
    [cleanup, runLive, runMock, refreshBackendHealth],
  )

  return {
    events,
    plan,
    status,
    error,
    usingMock,
    backendMode,
    backendDir,
    twilioEnabled,
    voiceConsentRequest,
    run,
    respondToVoiceConsent,
    reset,
  }
}
