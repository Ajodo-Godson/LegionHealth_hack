import { DEMO_DIAGNOSIS } from '../types'

interface DiagnosisInputProps {
  value: string
  onChange: (value: string) => void
  onRun: () => void
  onReset: () => void
  disabled: boolean
  isRunning: boolean
  runDisabled?: boolean
}

export function DiagnosisInput({
  value,
  onChange,
  onRun,
  onReset,
  disabled,
  isRunning,
  runDisabled = false,
}: DiagnosisInputProps) {
  return (
    <section className="diagnosis-input">
      <label htmlFor="diagnosis" className="diagnosis-label">
        Physician diagnosis (given — APO does not diagnose)
      </label>
      <textarea
        id="diagnosis"
        className="diagnosis-textarea"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={DEMO_DIAGNOSIS}
        rows={2}
        disabled={disabled}
      />
      <div className="diagnosis-actions">
        <button
          type="button"
          className="btn btn-primary"
          onClick={onRun}
          disabled={disabled || !value.trim() || runDisabled}
        >
          {isRunning ? 'Running…' : 'Run APO'}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onReset}
          disabled={isRunning}
        >
          Reset
        </button>
      </div>
    </section>
  )
}
