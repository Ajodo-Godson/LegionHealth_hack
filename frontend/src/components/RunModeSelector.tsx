import type { PatientLocation, RunMode } from '../types'

interface RunModeSelectorProps {
  runMode: RunMode
  location: PatientLocation
  onRunModeChange: (mode: RunMode) => void
  onLocationChange: (location: PatientLocation) => void
  disabled: boolean
}

export function RunModeSelector({
  runMode,
  location,
  onRunModeChange,
  onLocationChange,
  disabled,
}: RunModeSelectorProps) {
  return (
    <section className="run-mode-selector">
      <fieldset className="run-mode-fieldset" disabled={disabled}>
        <legend className="run-mode-legend">Scenario mode</legend>
        <div className="run-mode-options">
          <label className="run-mode-option">
            <input
              type="radio"
              name="run-mode"
              value="demo"
              checked={runMode === 'demo'}
              onChange={() => onRunModeChange('demo')}
            />
            <span>
              <strong>Demo (sleep apnea)</strong>
              <span className="run-mode-option-desc">
                Planted Atlanta sleep clinics — reliable contradiction + re-route.
              </span>
            </span>
          </label>
          <label className="run-mode-option">
            <input
              type="radio"
              name="run-mode"
              value="custom"
              checked={runMode === 'custom'}
              onChange={() => onRunModeChange('custom')}
            />
            <span>
              <strong>Custom (generated)</strong>
              <span className="run-mode-option-desc">
                Any diagnosis — Grok generates evidence, insurance, and local clinics.
              </span>
            </span>
          </label>
        </div>
      </fieldset>

      {runMode === 'custom' && (
        <div className="location-fields">
          <label className="location-field">
            <span>City</span>
            <input
              type="text"
              value={location.city}
              onChange={(e) => onLocationChange({ ...location, city: e.target.value })}
              placeholder="Atlanta"
              disabled={disabled}
              required
            />
          </label>
          <label className="location-field">
            <span>State</span>
            <input
              type="text"
              value={location.state}
              onChange={(e) => onLocationChange({ ...location, state: e.target.value })}
              placeholder="GA"
              maxLength={2}
              disabled={disabled}
              required
            />
          </label>
          <label className="location-field">
            <span>ZIP (optional)</span>
            <input
              type="text"
              value={location.zip_code ?? ''}
              onChange={(e) =>
                onLocationChange({
                  ...location,
                  zip_code: e.target.value.trim() || undefined,
                })
              }
              placeholder="30303"
              disabled={disabled}
            />
          </label>
        </div>
      )}
    </section>
  )
}

export function isCustomRunReady(location: PatientLocation): boolean {
  return Boolean(location.city.trim() && location.state.trim())
}
