import type { Plan } from '../types'

interface PlanCardProps {
  plan: Plan | null
  status: string
}

export function PlanCard({ plan, status }: PlanCardProps) {
  if (!plan) {
    return (
      <section className="panel plan-panel">
        <header className="panel-header">
          <h2>Recommended Plan</h2>
        </header>
        <div className="plan-empty">
          {status === 'streaming' || status === 'connecting' ? (
            <p>Agents are investigating your options…</p>
          ) : (
            <p>Your charter-aligned action plan will appear here after the run completes.</p>
          )}
        </div>
      </section>
    )
  }

  return (
    <section className="panel plan-panel">
      <header className="panel-header">
        <div className="panel-header-row">
          <h2>Recommended Plan</h2>
          {plan.personalized ? (
            <span className="personalized-badge">Personalized from your records</span>
          ) : (
            <span className="personalized-badge personalized-badge--muted">
              General guidance — add records to personalize
            </span>
          )}
        </div>
        <p className="panel-subtitle">Draft plan for patient review — not a binding decision.</p>
      </header>

      <div className="plan-details">
        <div className="plan-provider">
          <h3>{plan.recommended_provider.name}</h3>
          <p>{plan.recommended_provider.address}</p>
          <p>{plan.recommended_provider.phone}</p>
        </div>

        <dl className="plan-stats">
          <div className="plan-stat">
            <dt>Wait time</dt>
            <dd>{plan.wait_time}</dd>
          </div>
          <div className="plan-stat">
            <dt>Est. cost</dt>
            <dd>{plan.est_cost}</dd>
          </div>
          <div className="plan-stat">
            <dt>Coverage</dt>
            <dd>{plan.coverage_status}</dd>
          </div>
        </dl>

        {plan.eligible_trials && plan.eligible_trials.length > 0 && (
          <div className="plan-trials">
            <h4>Eligible trials</h4>
            <ul>
              {plan.eligible_trials.map((trial) => (
                <li key={trial}>{trial}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="plan-next-action">
          <h4>Next action</h4>
          <p>{plan.next_action}</p>
        </div>
      </div>

      {plan.contradiction_found?.detected && (
        <div className="verification-trace">
          <h3>Live verification trace</h3>
          <p className="verification-trace-subtitle">
            Insurer and provider disagreed — APO re-routed to a verified option.
          </p>
          <ul className="verification-trace-list">
            {(plan.verification_trace ?? []).map((line) => (
              <li key={line} className="verification-trace-item">
                {line}
              </li>
            ))}
          </ul>
          {plan.rerouted_to && (
            <p className="verification-reroute">
              Re-routed to <strong>{plan.rerouted_to}</strong> after contradiction at Clinic B.
            </p>
          )}
        </div>
      )}

      <div className="charter-checks">
        <h3>Charter Check</h3>
        <p className="charter-checks-subtitle">
          Recommendations checked against your priorities. Alternatives considered but not
          recommended are shown for transparency.
        </p>
        <ul className="charter-check-list">
          {plan.charter_checks.map((check) => (
            <li
              key={check.item}
              className={`charter-check-item charter-check--${check.status}`}
              data-priority={check.priority_ref}
            >
              <div className="charter-check-header">
                <span className="charter-check-status">
                  {check.status === 'aligned'
                    ? 'Aligned'
                    : check.status === 'excluded'
                      ? 'Considered & excluded'
                      : 'Review required'}
                </span>
                <span className="charter-check-item-name">{check.item}</span>
              </div>
              <p className="charter-check-message">
                {check.status === 'aligned'
                  ? `Matches Priority ${check.priority_ref}`
                  : check.status === 'excluded'
                    ? `Excluded per Priority ${check.priority_ref} — not in recommended plan`
                    : `Conflicts with Priority ${check.priority_ref}`}
              </p>
              <p className="charter-check-detail">{check.message}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

export function getFlaggedPriority(plan: Plan | null): number | null {
  if (!plan) return null
  const excluded = plan.charter_checks.find((c) => c.status === 'excluded')
  if (excluded) return excluded.priority_ref
  const flagged = plan.charter_checks.find((c) => c.status === 'flagged')
  return flagged?.priority_ref ?? null
}
