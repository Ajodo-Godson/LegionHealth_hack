import { useMemo, useState } from 'react'
import { AgentFeed } from './components/AgentFeed'
import { CharterBuilder } from './components/CharterBuilder'
import { CharterPanel } from './components/CharterPanel'
import { DiagnosisInput } from './components/DiagnosisInput'
import { PlanCard, getFlaggedPriority } from './components/PlanCard'
import { RecordsForm } from './components/RecordsForm'
import { VoiceConsentModal } from './components/VoiceConsentModal'
import { VoiceTranscript } from './components/VoiceTranscript'
import { useAgentStream } from './hooks/useAgentStream'
import {
  DEFAULT_CHARTER,
  DEMO_DIAGNOSIS,
  EMPTY_RECORDS,
  isCharterComplete,
  recordsForApi,
} from './types'
import type { Charter, PatientRecords } from './types'
import './App.css'

function App() {
  const [diagnosis, setDiagnosis] = useState(DEMO_DIAGNOSIS)
  const [charter, setCharter] = useState<Charter>({ ...DEFAULT_CHARTER })
  const [records, setRecords] = useState<PatientRecords>({ ...EMPTY_RECORDS })
  const {
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
  } = useAgentStream()

  const isRunning =
    status === 'connecting' || status === 'streaming' || status === 'awaiting_consent'
  const charterReady = isCharterComplete(charter)
  const highlightedPriority = useMemo(() => getFlaggedPriority(plan), [plan])

  const handleRun = () => {
    if (!charterReady) return
    run(diagnosis, charter, recordsForApi(records))
  }

  const handleReset = () => {
    reset()
    setDiagnosis(DEMO_DIAGNOSIS)
    setCharter({ ...DEFAULT_CHARTER })
    setRecords({ ...EMPTY_RECORDS })
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-brand">
          <h1>APO</h1>
          <span className="app-tagline">Autonomous Patient Organization</span>
        </div>
        <p className="app-pitch">
          Live parallel verification, contradiction detection, and adaptive re-routing — checked
          against your charter. APO never diagnoses; it finds out what is true for you, today.
        </p>
      </header>

      {backendMode === 'stub' && (
        <div className="warn-banner" role="status">
          Backend is in <strong>stub mode</strong> (no LLM). Stop the old server and run from{' '}
          <code>LegionHealth/backend</code> with <code>XAI_API_KEY</code> in <code>.env</code>.
          {backendDir && (
            <>
              {' '}
              Connected to: <code>{backendDir}</code>
            </>
          )}
        </div>
      )}

      {error && (
        <div className="error-banner" role="alert">
          {error}
          {usingMock && ' — showing mock data instead.'}
        </div>
      )}

      <CharterBuilder charter={charter} onChange={setCharter} disabled={isRunning} />

      <DiagnosisInput
        value={diagnosis}
        onChange={setDiagnosis}
        onRun={handleRun}
        onReset={handleReset}
        disabled={isRunning}
        isRunning={isRunning}
        runDisabled={!charterReady}
      />

      <RecordsForm records={records} onChange={setRecords} disabled={isRunning} />

      <main className="three-panel-layout">
        <CharterPanel charter={charter} highlightedPriority={highlightedPriority} />

        <div className="center-column">
          <AgentFeed
            events={events}
            status={status}
            usingMock={usingMock}
            backendMode={backendMode}
          />
          <VoiceTranscript events={events} status={status} />
        </div>

        <PlanCard plan={plan} status={status} />
      </main>

      <VoiceConsentModal
        request={voiceConsentRequest}
        twilioEnabled={twilioEnabled}
        onAuthorize={(useTwilio) => void respondToVoiceConsent(true, useTwilio)}
        onSkip={() => void respondToVoiceConsent(false, false)}
      />

      <footer className="app-footer">
        Demo uses synthetic patient data only — no real PHI. APO does not diagnose.
      </footer>
    </div>
  )
}

export default App
