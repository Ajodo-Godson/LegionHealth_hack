import { CharterBuilder } from './CharterBuilder'
import { LocationFields } from './LocationFields'
import { DEMO_DIAGNOSIS } from '../types'
import type { Charter, PatientLocation, RunMode } from '../types'

interface SetupPanelProps {
  charter: Charter
  onCharterChange: (charter: Charter) => void
  diagnosis: string
  onDiagnosisChange: (value: string) => void
  effectiveMode: RunMode
  location: PatientLocation
  onLocationChange: (location: PatientLocation) => void
  disabled: boolean
  onRun: () => void
  canRun: boolean
  isRunning: boolean
}

export function SetupPanel({
  charter,
  onCharterChange,
  diagnosis,
  onDiagnosisChange,
  effectiveMode,
  location,
  onLocationChange,
  disabled,
  onRun,
  canRun,
  isRunning,
}: SetupPanelProps) {
  const needsLocation = effectiveMode === 'custom'
  const isDemoDiagnosis =
    diagnosis.trim().toLowerCase() === DEMO_DIAGNOSIS.trim().toLowerCase()

  return (
    <section className="start-card">
      <div className="start-card-intro">
        <h1>Get a verified care plan</h1>
        <p>Enter your diagnosis. APO checks options against your priorities — it does not diagnose.</p>
      </div>

      <label className="start-field">
        <span className="start-label">Your diagnosis</span>
        <input
          id="diagnosis"
          type="text"
          className="start-input"
          value={diagnosis}
          onChange={(e) => onDiagnosisChange(e.target.value)}
          placeholder="e.g. sleep apnea, dry eyes"
          disabled={disabled}
        />
      </label>

      {needsLocation && (
        <div className="start-field">
          <span className="start-label">Your location</span>
          <LocationFields location={location} onChange={onLocationChange} disabled={disabled} />
        </div>
      )}

      {isDemoDiagnosis && !needsLocation && (
        <p className="start-hint">Demo scenario — Atlanta sleep apnea with a planted verification conflict.</p>
      )}

      <div className="start-field">
        <span className="start-label">What matters most</span>
        <CharterBuilder charter={charter} onChange={onCharterChange} disabled={disabled} />
      </div>

      <button
        type="button"
        className="btn btn-primary btn-start"
        onClick={onRun}
        disabled={isRunning || !canRun}
      >
        {isRunning ? 'Running…' : 'Run APO'}
      </button>
    </section>
  )
}
