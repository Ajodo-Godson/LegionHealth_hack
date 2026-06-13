import type { PatientLocation } from '../types'

interface LocationFieldsProps {
  location: PatientLocation
  onChange: (location: PatientLocation) => void
  disabled: boolean
}

export function LocationFields({ location, onChange, disabled }: LocationFieldsProps) {
  return (
    <div className="location-inline">
      <label className="location-inline-field">
        <span className="sr-only">City</span>
        <input
          type="text"
          value={location.city}
          onChange={(e) => onChange({ ...location, city: e.target.value })}
          placeholder="City"
          disabled={disabled}
          required
        />
      </label>
      <label className="location-inline-field location-inline-field--state">
        <span className="sr-only">State</span>
        <input
          type="text"
          value={location.state}
          onChange={(e) => onChange({ ...location, state: e.target.value.toUpperCase() })}
          placeholder="ST"
          maxLength={2}
          disabled={disabled}
          required
        />
      </label>
    </div>
  )
}
