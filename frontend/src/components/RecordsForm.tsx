import type { PatientRecords } from '../types'
import {
  COMORBIDITY_OPTIONS,
  DEMO_RECORDS,
  EMPTY_RECORDS,
  PRIOR_TREATMENT_OPTIONS,
  SEVERITY_OPTIONS,
  recordsProvided,
} from '../types'

interface RecordsFormProps {
  records: PatientRecords
  onChange: (records: PatientRecords) => void
  disabled: boolean
}

export function RecordsForm({ records, onChange, disabled }: RecordsFormProps) {
  const hasRecords = recordsProvided(records)

  const toggleListItem = (
    key: 'comorbidities' | 'prior_treatments',
    value: string,
  ) => {
    const current = records[key] ?? []
    const next = current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value]
    onChange({ ...records, [key]: next.length > 0 ? next : undefined })
  }

  const fillDemo = () => onChange({ ...DEMO_RECORDS })

  const clearRecords = () => onChange({ ...EMPTY_RECORDS })

  return (
    <section className="records-form" aria-labelledby="records-heading">
      <div className="records-form-header">
        <div>
          <h2 id="records-heading" className="records-form-title">
            Optional: your records summary
          </h2>
          <p className="records-form-subtitle">
            APO does not diagnose — your doctor already did. These details only personalize research and planning.
          </p>
        </div>
        <div className="records-form-actions">
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={fillDemo}
            disabled={disabled}
          >
            Fill demo records
          </button>
          {hasRecords && (
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={clearRecords}
              disabled={disabled}
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="records-fields">
        <fieldset className="records-fieldset" disabled={disabled}>
          <legend className="records-legend">Severity</legend>
          <div className="records-options">
            {SEVERITY_OPTIONS.map((option) => (
              <label key={option} className="records-option">
                <input
                  type="radio"
                  name="severity"
                  checked={records.severity === option}
                  onChange={() => onChange({ ...records, severity: option })}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset className="records-fieldset" disabled={disabled}>
          <legend className="records-legend">Comorbidities</legend>
          <div className="records-options records-options--grid">
            {COMORBIDITY_OPTIONS.map((option) => (
              <label key={option} className="records-option">
                <input
                  type="checkbox"
                  checked={records.comorbidities?.includes(option) ?? false}
                  onChange={() => toggleListItem('comorbidities', option)}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset className="records-fieldset" disabled={disabled}>
          <legend className="records-legend">Prior treatments tried</legend>
          <div className="records-options records-options--grid">
            {PRIOR_TREATMENT_OPTIONS.map((option) => (
              <label key={option} className="records-option">
                <input
                  type="checkbox"
                  checked={records.prior_treatments?.includes(option) ?? false}
                  onChange={() => toggleListItem('prior_treatments', option)}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        </fieldset>
      </div>
    </section>
  )
}
