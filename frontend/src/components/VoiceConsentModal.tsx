import type { VoiceConsentRequest } from '../types'

interface VoiceConsentModalProps {
  request: VoiceConsentRequest | null
  twilioEnabled: boolean
  onAuthorize: (useTwilio: boolean) => void
  onSkip: () => void
}

export function VoiceConsentModal({
  request,
  twilioEnabled,
  onAuthorize,
  onSkip,
}: VoiceConsentModalProps) {
  if (!request) return null

  return (
    <div className="consent-overlay" role="dialog" aria-modal="true" aria-labelledby="consent-title">
      <div className="consent-modal">
        <h2 id="consent-title">Authorize outbound call?</h2>
        <p className="consent-lead">
          APO wants to call <strong>{request.clinic_name}</strong> on your behalf to verify
          coverage — informational only, not authorizing treatment.
        </p>
        <dl className="consent-details">
          <div>
            <dt>Purpose</dt>
            <dd>{request.purpose}</dd>
          </div>
          <div>
            <dt>Phone</dt>
            <dd>{request.clinic_phone}</dd>
          </div>
        </dl>

        <div className="consent-actions">
          <button type="button" className="btn btn-primary" onClick={() => onAuthorize(false)}>
            Authorize — simulated transcript
          </button>
          {twilioEnabled && (
            <button type="button" className="btn btn-primary" onClick={() => onAuthorize(true)}>
              Authorize — real phone call (Twilio + Grok)
            </button>
          )}
          <button type="button" className="btn btn-secondary" onClick={onSkip}>
            Skip — use verified data only
          </button>
        </div>
      </div>
    </div>
  )
}
