import type { Charter, HealthResponse, PatientRecords, Plan, RunResponse } from '../types'

const API_BASE = '/api'

export async function fetchHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/health`)
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function checkHealth(): Promise<boolean> {
  const data = await fetchHealth()
  return data?.status === 'ok'
}

export async function startRun(
  diagnosis: string,
  charter: Charter,
  records?: PatientRecords | null,
): Promise<RunResponse> {
  const res = await fetch(`${API_BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ diagnosis, charter, records: records ?? null }),
  })
  if (!res.ok) {
    throw new Error(`Failed to start run: ${res.statusText}`)
  }
  return res.json()
}

export function streamUrl(runId: string): string {
  return `${API_BASE}/stream/${runId}`
}

export async function submitVoiceConsent(
  runId: string,
  granted: boolean,
  useTwilio: boolean,
): Promise<void> {
  const res = await fetch(`${API_BASE}/run/${runId}/voice-consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ granted, use_twilio: useTwilio }),
  })
  if (!res.ok) {
    throw new Error(`Failed to submit voice consent: ${res.statusText}`)
  }
}

export async function fetchPlan(runId: string): Promise<Plan> {
  const res = await fetch(`${API_BASE}/plan/${runId}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch plan: ${res.statusText}`)
  }
  return res.json()
}

/** Backend emits plan_ready before state.plan is set — retry briefly. */
export async function fetchPlanWithRetry(
  runId: string,
  maxAttempts = 8,
  delayMs = 400,
): Promise<Plan> {
  let lastError: Error | null = null

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fetchPlan(runId)
    } catch (err) {
      lastError = err as Error
      if (attempt < maxAttempts - 1) {
        await new Promise((r) => setTimeout(r, delayMs))
      }
    }
  }

  throw lastError ?? new Error('Failed to fetch plan')
}
