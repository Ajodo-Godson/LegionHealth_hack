import type { AgentLogEntry, Plan } from '../types'

export const MOCK_PLAN: Plan = {
  recommended_provider: {
    name: 'Lakeside Sleep Medicine',
    address: '88 Lakeview Blvd, Decatur, GA 30030',
    phone: '(404) 555-0377',
  },
  wait_time: '6 days',
  est_cost: '$150-400 (estimated after insurance)',
  coverage_status: 'Verified in-network — CPAP covered, prior auth 3-5 business days',
  eligible_trials: ['Sleep Apnea CPAP Adherence Study (local IRB-approved)'],
  next_action:
    'Schedule intake at Lakeside Sleep Medicine — verified after re-route from Clinic B mismatch',
  personalized: true,
  rerouted_to: 'clinic_c',
  contradiction_found: {
    detected: true,
    insurer_claim: 'Insurer lists Metro Pulmonary & Sleep as in-network for BlueCross Silver PPO',
    provider_claim: 'Metro Pulmonary & Sleep reports: Dropped this plan March 2026',
    clinic_id: 'clinic_b',
    clinic_name: 'Metro Pulmonary & Sleep',
    message:
      '🔍 Conflict detected — insurer and provider disagree for this patient, today.',
  },
  verification_trace: [
    '✅ Insurer confirms BlueCross Silver PPO covers sleep apnea treatment at Northside Sleep Center and Metro Pulmonary & Sleep',
    '✅ Northside Sleep Center confirms coverage, wait time 14 days',
    '⚠️ Metro Pulmonary & Sleep says: We no longer accept BlueCross Silver PPO — Dropped this plan March 2026.',
    '🔍 Conflict detected — insurer and provider disagree.',
    '✅ Lakeside Sleep Medicine confirms coverage, wait time 6 days',
  ],
  charter_checks: [
    {
      item: 'CPAP therapy via verified in-network clinic (Clinic C)',
      status: 'aligned',
      priority_ref: 1,
      message: 'Aligned with Priority 1 (minimize out-of-pocket cost)',
    },
    {
      item: 'Surgery (UPPP)',
      status: 'excluded',
      priority_ref: 2,
      message:
        'Considered and excluded — conflicts with Priority 2 (avoid surgery unless medically necessary). Not recommended unless CPAP fails.',
    },
    {
      item: 'Verified appointment within 6 days',
      status: 'aligned',
      priority_ref: 3,
      message: 'Aligned with Priority 3 (start treatment within 2 weeks)',
    },
  ],
}

export const MOCK_AGENT_EVENTS: AgentLogEntry[] = [
  {
    agent: 'executive',
    action: 'started',
    output: 'Physician diagnosis received: sleep apnea.',
    timestamp: '2026-06-13T12:00:00Z',
  },
  {
    agent: 'research',
    action: 'completed',
    output:
      'Based on your records: lifestyle changes tried — escalating to CPAP. Surgery noted for charter review.',
    timestamp: '2026-06-13T12:00:04Z',
  },
  {
    agent: 'executive',
    action: 'parallel_dispatch',
    output: 'Firing parallel verification: Insurance Agent + Provider A + Provider B (concurrent)',
    timestamp: '2026-06-13T12:00:08Z',
  },
  {
    agent: 'insurance',
    action: 'running',
    output: 'Live verification call to insurer...',
    timestamp: '2026-06-13T12:00:08Z',
  },
  {
    agent: 'provider_a',
    action: 'running',
    output: 'Calling Northside Sleep Center (Clinic A)...',
    timestamp: '2026-06-13T12:00:08Z',
  },
  {
    agent: 'provider_b',
    action: 'running',
    output: 'Calling Metro Pulmonary & Sleep (Clinic B)...',
    timestamp: '2026-06-13T12:00:08Z',
  },
  {
    agent: 'insurance',
    action: 'completed',
    output: '✅ Insurer confirms BlueCross Silver PPO covers Clinic A and Clinic B.',
    timestamp: '2026-06-13T12:00:12Z',
  },
  {
    agent: 'provider_a',
    action: 'completed',
    output: '✅ Northside Sleep Center confirms coverage, 14-day wait.',
    timestamp: '2026-06-13T12:00:12Z',
  },
  {
    agent: 'provider_b',
    action: 'completed',
    output: '⚠️ Metro Pulmonary & Sleep: We dropped BlueCross Silver PPO in March 2026.',
    timestamp: '2026-06-13T12:00:12Z',
  },
  {
    agent: 'contradiction_detector',
    action: 'completed',
    output: '🔍 Conflict detected — insurer and provider disagree. Re-routing.',
    timestamp: '2026-06-13T12:00:14Z',
  },
  {
    agent: 'executive',
    action: 'reroute',
    output: '→ Dispatching Provider Agent C to Lakeside Sleep Medicine (Clinic C)',
    timestamp: '2026-06-13T12:00:15Z',
  },
  {
    agent: 'provider_c',
    action: 'completed',
    output: '✅ Lakeside Sleep Medicine confirms coverage, 6-day wait.',
    timestamp: '2026-06-13T12:00:18Z',
  },
  {
    agent: 'executive',
    action: 'reconciling',
    output:
      'Reconciling verified results — replaying Clinic B call that surfaced the contradiction...',
    timestamp: '2026-06-13T12:00:19Z',
  },
  {
    agent: 'voice',
    action: 'transcript',
    output:
      'APO: Hi, verifying coverage for a patient with BlueCross Silver PPO diagnosed with sleep apnea.',
    timestamp: '2026-06-13T12:00:22Z',
  },
  {
    agent: 'voice',
    action: 'transcript',
    output: 'Receptionist: We stopped accepting BlueCross Silver PPO in March 2026.',
    timestamp: '2026-06-13T12:00:24Z',
  },
  {
    agent: 'synthesis',
    action: 'completed',
    output: 'Plan built from verified data after re-route to Clinic C.',
    timestamp: '2026-06-13T12:00:30Z',
  },
  {
    agent: 'charter_check',
    action: 'completed',
    output: '3 items reviewed, 1 alternative excluded per charter.',
    timestamp: '2026-06-13T12:00:32Z',
  },
]

export async function replayMockEvents(
  onEvent: (entry: AgentLogEntry) => void,
  onPlanReady: () => void,
  onDone: () => void,
  signal?: AbortSignal,
  waitForConsent?: () => Promise<{ granted: boolean; useTwilio: boolean }>,
): Promise<void> {
  const voiceEvents = MOCK_AGENT_EVENTS.filter((e) => e.agent === 'voice')
  const afterVoiceEvents = MOCK_AGENT_EVENTS.filter(
    (e) => e.agent === 'synthesis' || e.agent === 'charter_check',
  )
  const beforeConsentEvents = MOCK_AGENT_EVENTS.filter(
    (e) =>
      e.agent !== 'voice' && e.agent !== 'synthesis' && e.agent !== 'charter_check',
  )

  for (const event of beforeConsentEvents) {
    if (signal?.aborted) return
    await delay(900, signal)
    onEvent(event)
  }

  let playVoice = true
  if (waitForConsent) {
    const consent = await waitForConsent()
    playVoice = consent.granted
    if (signal?.aborted) return
  }

  if (playVoice) {
    for (const event of voiceEvents) {
      if (signal?.aborted) return
      await delay(700, signal)
      onEvent(event)
    }
  } else {
    onEvent({
      agent: 'voice',
      action: 'skipped',
      output: 'Patient skipped outbound call — using verified data only.',
      timestamp: new Date().toISOString(),
    })
  }

  for (const event of afterVoiceEvents) {
    if (signal?.aborted) return
    await delay(900, signal)
    onEvent(event)
  }

  await delay(400, signal)
  onPlanReady()
  await delay(200, signal)
  onDone()
}

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms)
    signal?.addEventListener('abort', () => {
      clearTimeout(timer)
      reject(new DOMException('Aborted', 'AbortError'))
    })
  })
}
