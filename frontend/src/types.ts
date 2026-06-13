export interface CharterPriority {
  rank: number
  statement: string
}

export interface Charter {
  priorities: CharterPriority[]
}

export interface PatientRecords {
  severity?: string
  comorbidities?: string[]
  prior_treatments?: string[]
}

export interface AgentLogEntry {
  agent: string
  action: string
  input?: string
  output: string
  timestamp: string
}

export interface CharterCheck {
  item: string
  status: 'aligned' | 'flagged' | 'excluded'
  priority_ref: number
  message: string
}

export interface ContradictionFound {
  detected: boolean
  insurer_claim: string
  provider_claim: string
  clinic_id: string
  clinic_name: string
  message: string
}

export interface Plan {
  recommended_provider: {
    name: string
    address: string
    phone: string
  }
  wait_time: string
  est_cost: string
  coverage_status: string
  eligible_trials?: string[]
  next_action: string
  charter_checks: CharterCheck[]
  personalized?: boolean
  contradiction_found?: ContradictionFound | null
  rerouted_to?: string | null
  verification_trace?: string[]
}

export interface RunResponse {
  run_id: string
}

export type StreamStatus =
  | 'idle'
  | 'connecting'
  | 'streaming'
  | 'awaiting_consent'
  | 'done'
  | 'error'

export interface VoiceConsentRequest {
  clinic_name: string
  clinic_phone: string
  purpose: string
}

export interface HealthResponse {
  status: string
  llm_enabled?: boolean
  mode?: 'live' | 'stub'
  backend_dir?: string
  twilio_enabled?: boolean
}

export const CHARTER_PRIORITY_OPTIONS = [
  'Minimize out-of-pocket cost',
  'Avoid surgery unless medically necessary',
  'Start treatment within 2 weeks',
  'Stay close to home',
  'Prefer telehealth when possible',
  'Maximize evidence-based care',
] as const

export function charterFromStatements(statements: string[]): Charter {
  return {
    priorities: statements.map((statement, index) => ({
      rank: index + 1,
      statement,
    })),
  }
}

export function isCharterComplete(charter: Charter): boolean {
  return charter.priorities.length === 3
}

export const DEFAULT_CHARTER: Charter = {
  priorities: [
    { rank: 1, statement: 'Minimize out-of-pocket cost' },
    { rank: 2, statement: 'Avoid surgery unless medically necessary' },
    { rank: 3, statement: 'Start treatment within 2 weeks' },
  ],
}

export const DEMO_DIAGNOSIS = 'I was just diagnosed with sleep apnea'

export const EMPTY_RECORDS: PatientRecords = {}

export const DEMO_RECORDS: PatientRecords = {
  severity: 'Moderate (AHI 25–30)',
  comorbidities: ['Hypertension', 'Obesity'],
  prior_treatments: ['Lifestyle changes', 'Positional therapy'],
}

export const SEVERITY_OPTIONS = [
  'Mild (AHI 5–15)',
  'Moderate (AHI 15–30)',
  'Severe (AHI 30+)',
] as const

export const COMORBIDITY_OPTIONS = [
  'Hypertension',
  'Obesity',
  'Type 2 diabetes',
  'Heart disease',
] as const

export const PRIOR_TREATMENT_OPTIONS = [
  'Lifestyle changes',
  'Positional therapy',
  'CPAP trial',
  'Oral appliance',
] as const

export function recordsProvided(records: PatientRecords | null | undefined): boolean {
  if (!records) return false
  return Boolean(
    records.severity?.trim() ||
      (records.comorbidities && records.comorbidities.length > 0) ||
      (records.prior_treatments && records.prior_treatments.length > 0),
  )
}

export function recordsForApi(
  records: PatientRecords,
): PatientRecords | null {
  return recordsProvided(records) ? records : null
}
