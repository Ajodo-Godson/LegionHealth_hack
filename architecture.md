# Autonomous Patient Organization (APO) — Build Spec

## The pitch

"We built the first Autonomous Patient Organization — an AI institution that doesn't just advise, it acts. It places real-time calls to verify your actual coverage and provider options, adapts its plan live when it discovers contradictions between what your insurer and your provider say, and checks every recommendation against your own health priorities. You cannot get this from one prompt to ChatGPT, Claude, or Grok — it requires live execution, real-time adaptation to new information, and a persistent fiduciary charter. A chat model can tell you what *should* be true. The APO finds out what *is* true, right now, for you."

The demo is not "an AI that calls people." The demo has two proof points a single LLM completion structurally cannot replicate:

1. **Live contradiction + adaptive re-route** — the system discovers, through real-time verification, that two sources disagree (insurer vs. provider), and visibly changes its plan in response — something only possible with actual execution and feedback, not pattern-matching from training data.
2. **Charter check** — every recommendation is evaluated against the patient's own stated priorities, not generic "best practice," and flagged if it conflicts.

*While you watched for ~2 minutes, the APO did what would normally take a patient hours of phone calls — and caught a discrepancy the patient never would have known to look for.*

## Scoped MVP (build this, nothing more)

One end-to-end thread: **patient reports a new diagnosis (sleep apnea), optionally adds records → APO fires parallel live/simulated calls to insurer + providers → discovers a planted contradiction → adaptively re-routes to a new provider → produces a charter-checked, verified action plan**.

Important framing: the APO never diagnoses. The diagnosis is a given input from a doctor. Records, if provided, are used only to *personalize* the downstream research (severity, comorbidities, prior treatments tried) — never to suggest "what condition you might have."

Do not build all 7 brainstormed concepts. Cut everything except:

1. Patient Charter (fiduciary proof point)
2. Diagnosis input + optional records form (personalization only)
3. Executive Agent (orchestrator)
4. Research Agent
5. Insurance Agent + 2-3 Provider Agents, run in **parallel**
6. Contradiction Detector + Adaptive Re-Router (live-verification proof point — this is the centerpiece)
7. Voice Executor Agent (one call rendered as transcript, can be one of the parallel calls)
8. Plan synthesis + charter-check + verification trace UI

## Architecture

```
Patient input (diagnosis + concerns) [+ optional records form]
        ↓
Charter Builder → produces Patient Charter (3 ranked priorities)
        ↓
Research Agent → treatment options + evidence
                  (if records present: filters/weights options by
                   severity, comorbidities, prior treatments)
        ↓
Executive Agent fires PARALLEL live-verification calls:
   ├── Insurance Agent  → calls/queries insurer  → "Plan covers CPAP/sleep study
   │                                                  at Clinic A and Clinic B"
   ├── Provider Agent A → calls Clinic A         → confirms coverage + wait time
   └── Provider Agent B → calls Clinic B         → "We dropped this insurance
                                                      plan in March 2026" (CONTRADICTION)
        ↓
Contradiction Detector → flags: insurer says Clinic B is covered,
                          Clinic B itself says it's not — for THIS patient,
                          TODAY
        ↓
Executive Agent ADAPTS LIVE → dispatches Provider Agent C → calls Clinic C
                               → confirms coverage + wait time
        ↓
Synthesis Agent → builds action plan from VERIFIED, RECONCILED data only
        ↓
Charter Check → flags any recommendation that conflicts with charter priorities,
                shows the override/flag explicitly in the UI
        ↓
Voice Executor → renders ONE of the above calls (e.g., the Clinic B call that
                  revealed the contradiction) as a live transcript
        ↓
Output: Verified Plan (doctor, wait time, est. cost, next action)
        + contradiction/re-route trace + charter trace
```

Records form is optional — if absent, the Research Agent proceeds with generic (non-personalized) reasoning based on the diagnosis alone. UI shows: "Personalized using your records" vs. "General guidance for this diagnosis." This is independent of, and secondary to, the live-verification/re-route mechanism, which is the demo's core proof point.

## Critical "must show" moments (two — both are required)

**Moment 1 — Live contradiction + re-route (the centerpiece).** The agent feed must visibly show:
- Insurance Agent: "✅ Insurer confirms Clinic B is in-network for sleep studies"
- Provider Agent B: "⚠️ Clinic B says: 'We stopped accepting this plan in March 2026'"
- Contradiction Detector: "🔍 Conflict detected — insurer and provider disagree. Re-routing."
- Executive Agent: "→ Dispatching Provider Agent C to Clinic C"
- Provider Agent C: "✅ Clinic C confirms coverage, 6-day wait"

This is the "you cannot get this from one prompt" moment — say it out loud during the demo.

**Moment 2 — Charter check.** At least one recommendation must visibly get checked against the charter and either:
- pass with an explicit "✅ Aligned with Priority X", or
- get flagged: "⚠️ Recommends X, but Priority 3 (avoid surgery unless necessary) — flagged for patient review."

This is the "fiduciary, not chatbot" moment. Don't skip either moment — together they're the whole pitch.

## Tech stack recommendation

- Backend: Python (FastAPI) with `asyncio` — the parallel calls (Insurance Agent + Provider Agents A & B firing simultaneously) are the centerpiece, so the orchestrator must genuinely run them concurrently, not sequentially. A simple custom async executor is fine; don't pull in a heavy framework under time pressure
- LLM: Claude or Grok via API, one model is fine — give each agent a distinct system prompt/persona, not a separate model
- Voice: Grok Voice or Twilio + ElevenLabs if doing a real call; otherwise simulate with a second LLM agent playing "clinic receptionist" and render it as a live transcript
- Frontend: single-page React app (Vite) — four panels: Charter, optional records form, Agent Activity Feed (live-streaming, must show concurrent agents firing at the same timestamp), Final Plan
- Mock data: JSON files for insurance plans, clinic directory, wait times — **the contradiction must be planted deterministically in this data**, not left to chance/LLM hallucination (see below)

## Data flow / state

- `charter.json` — { priorities: [ {rank, statement} ] }
- `patient_input.json` — { diagnosis, concerns, records: optional { severity, comorbidities, prior_treatments } }
- `mock_world.json` — the planted scenario (see repo `backend/data/mock_world.json`)
- `agent_log` — append-only list streamed via SSE — timestamps must show Insurance Agent / Provider Agent A / Provider Agent B firing concurrently
- `plan.json` — { recommended_provider, wait_time, est_cost, coverage_status, contradiction_found, rerouted_to, charter_checks, personalized, verification_trace }

For "records," a small structured form (severity, checkboxes for comorbidities/prior treatments) is enough — no file upload/parsing needed.

## Explicit non-goals (say this if judges ask)

- Not making real binding decisions or submitting forms — output is a draft plan for the patient to approve
- Not diagnosing — diagnosis is a given input from a doctor; records only personalize downstream research
- Not storing/transmitting real PHI — demo uses synthetic patient data and a scripted mock world
- Voice calls are informational/investigative only (asking questions), not authorizing anything
- The contradiction in the demo is planted/scripted for reliability — frame this honestly as "a realistic scenario we've configured" if asked; the *mechanism* (parallel verification → contradiction detection → re-route) generalizes to real data
