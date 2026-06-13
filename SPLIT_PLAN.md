# APO Split Plan — Two Agent Sessions

This document splits the hackathon MVP into **two parallel workstreams**. Each agent owns a directory, follows the shared contract below, and integrates at defined gates.

**Read first:** [`architecture.md`](./architecture.md) for full product scope and demo requirements.

---

## Roles

| | **Agent A — Backend** | **Agent B — Frontend** |
|---|---|---|
| **Owns** | `backend/` | `frontend/`, root `README.md` |
| **Does not touch** | `frontend/` | `backend/` |
| **Runs locally** | `uvicorn` on `:8000` | `vite dev` on `:5173` |
| **Primary goal** | Agents, orchestration, SSE, mock data, plan output | Three-panel UI, streaming feed, charter badges, demo UX |

---

## Shared Contract

Both agents must implement this exactly. **Do not change shapes without updating both sides.**

### API Endpoints

```
GET  /api/health
     → { "status": "ok" }

POST /api/run
     Body:  { "diagnosis": string, "charter": Charter }
     →      { "run_id": string }

GET  /api/stream/{run_id}
     → SSE stream (see event format below)

GET  /api/plan/{run_id}
     → Plan
```

### TypeScript / Python Schemas

Agent A implements in Pydantic (`backend/models/schemas.py`).  
Agent B copies to `frontend/src/types.ts`.

```typescript
interface CharterPriority {
  rank: number        // 1, 2, 3
  statement: string
}

interface Charter {
  priorities: CharterPriority[]
}

interface AgentLogEntry {
  agent: string       // "executive" | "research" | "insurance" | "provider" | "voice" | "synthesis" | "charter_check"
  action: string
  input?: string
  output: string
  timestamp: string   // ISO 8601
}

interface CharterCheck {
  item: string
  status: "aligned" | "flagged"
  priority_ref: number
  message: string
}

interface Plan {
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
}
```

### SSE Event Format

```
event: agent_log
data: {"agent":"research","action":"completed","output":"...","timestamp":"2026-06-13T12:00:00Z"}

event: plan_ready
data: {"run_id":"abc-123"}

event: done
data: {}
```

### Default Demo Charter (use on both sides)

```json
{
  "priorities": [
    { "rank": 1, "statement": "Minimize out-of-pocket cost" },
    { "rank": 2, "statement": "Avoid surgery unless medically necessary" },
    { "rank": 3, "statement": "Start treatment within 2 weeks" }
  ]
}
```

### CORS

Agent A must allow `http://localhost:5173`.

### Demo Input

```
I was just diagnosed with sleep apnea
```

---

## Integration Gates

| Gate | When | Criteria |
|------|------|----------|
| **Gate 1** | ~30 min | Shared contract agreed; both apps scaffolded |
| **Gate 2** | ~2 hr | Agent A ships stub SSE; Agent B connects and sees fake events |
| **Gate 3** | ~6 hr | Full E2E: real agents → live feed → plan with charter badges |
| **Gate 4** | ~10 hr | Demo-ready: voice transcript + one flagged charter item visible |

---

## Agent A — Backend Session

### Directory Structure

```
backend/
├── main.py                 # FastAPI app, CORS, routes
├── orchestrator.py         # Executive agent — sequential runner
├── models/
│   └── schemas.py          # Pydantic models (shared contract)
├── agents/
│   ├── charter.py
│   ├── research.py
│   ├── insurance.py
│   ├── provider.py
│   ├── voice.py
│   └── synthesis.py
├── prompts/                # One system prompt file per agent persona
├── data/
│   ├── insurance_plans.json
│   ├── clinics.json
│   └── treatment_evidence.json
├── requirements.txt
└── .env.example
```

### Phase A1 — Foundation (first 1–2 hours)

- [ ] FastAPI app with `GET /api/health`
- [ ] Pydantic schemas matching shared contract
- [ ] Mock JSON: 3–5 clinics, 1 insurance plan, sleep apnea treatment options
- [ ] `POST /api/run` → returns `{ run_id }`, starts background task
- [ ] `GET /api/stream/{run_id}` → SSE with **stub events** (fake `agent_log` every ~2s, then `done`)

**Done when:** `curl localhost:8000/api/health` works; SSE streams 5 stub events then `done`.

### Phase A2 — Orchestrator + Stub Agents (hours 2–4)

- [ ] Executive agent runs sub-agents sequentially
- [ ] Each step appends to in-memory `agent_log` and pushes SSE event
- [ ] Stub agents return hardcoded JSON (no LLM yet)
- [ ] `GET /api/plan/{run_id}` returns hardcoded plan with **one flagged + two aligned** charter checks
- [ ] Emit `plan_ready` SSE event before `done`

**Done when:** Full stub run completes in ~10s with realistic agent names and outputs.

**Required stub charter checks (minimum):**

```json
[
  {
    "item": "CPAP therapy via in-network sleep clinic",
    "status": "aligned",
    "priority_ref": 1,
    "message": "Aligned with Priority 1 (minimize out-of-pocket cost)"
  },
  {
    "item": "UPPP surgery — fastest treatment path",
    "status": "flagged",
    "priority_ref": 2,
    "message": "Conflicts with Priority 2 (avoid surgery unless medically necessary) — flagged for patient review"
  },
  {
    "item": "Appointment available within 10 days",
    "status": "aligned",
    "priority_ref": 3,
    "message": "Aligned with Priority 3 (start treatment within 2 weeks)"
  }
]
```

### Phase A3 — Real LLM Agents (hours 4–8)

- [ ] Wire one LLM provider (Claude or Grok) via env var
- [ ] Replace stubs with LLM calls — distinct system prompt per agent, same model
- [ ] **Research agent:** reason over `treatment_evidence.json`
- [ ] **Insurance agent:** reason over `insurance_plans.json`
- [ ] **Provider agent:** rank clinics from `clinics.json` using charter priorities
- [ ] **Synthesis agent:** merge outputs into `Plan` JSON
- [ ] **Charter check pass:** annotate each recommendation — **must produce ≥1 `flagged` item**

**Done when:** Real plan includes `charter_checks` with at least one flagged item; SSE shows real agent outputs.

### Phase A4 — Voice Executor (hours 8–10)

- [ ] Simulated call: LLM plays clinic receptionist
- [ ] Stream transcript lines as SSE `agent_log` events (`agent: "voice"`)
- [ ] 6–10 turns: wait time, CPAP setup, insurance acceptance
- [ ] Real Twilio/Grok Voice **only if** Phases A1–A3 are complete

**Done when:** Voice transcript appears in SSE stream mid-run.

### Agent A — Non-Goals

- No frontend code
- No LangGraph/CrewAI unless Phase A3 is done early
- No real telephony in first pass
- No scope beyond sleep apnea MVP
- No real PHI — synthetic demo data only

---

## Agent B — Frontend Session

### Directory Structure

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── types.ts              # Shared contract types
│   ├── api/
│   │   └── client.ts         # fetch helpers
│   ├── hooks/
│   │   └── useAgentStream.ts # SSE consumer
│   ├── components/
│   │   ├── CharterPanel.tsx
│   │   ├── AgentFeed.tsx
│   │   ├── PlanCard.tsx
│   │   ├── VoiceTranscript.tsx
│   │   └── DiagnosisInput.tsx
│   └── mocks/
│       └── demoEvents.ts     # Fallback when backend unavailable
├── vite.config.ts
└── package.json

README.md                       # Root setup + demo script (Agent B owns)
```

### Phase B1 — Foundation (first 1–2 hours)

- [ ] Vite + React + TypeScript scaffold
- [ ] `types.ts` matching shared contract exactly
- [ ] Three-column layout: **Charter | Agent Feed | Plan**
- [ ] Charter panel with 3 preset priorities (from default demo charter)
- [ ] Diagnosis input + "Run APO" button

**Done when:** Static three-panel layout renders with preset charter.

### Phase B2 — Mock Integration (hours 2–4)

- [ ] `useAgentStream` hook — connect to `GET /api/stream/{run_id}`
- [ ] Agent feed: append events; show agent name, action, output, timestamp
- [ ] **Mock fallback:** if backend down, replay hardcoded events from `demoEvents.ts`
- [ ] Plan card: render `Plan` with ✅ aligned / ⚠️ flagged badges using mock data

**Done when:** UI works fully with mock data; ready to swap in real SSE at Gate 2.

### Phase B3 — Live Backend Wiring (hours 4–8)

- [ ] `POST /api/run` on button click → get `run_id` → open SSE
- [ ] Clear feed on new run; show loading state per agent
- [ ] On `plan_ready` event → fetch `GET /api/plan/{run_id}`
- [ ] Plan card: provider, wait time, cost, coverage, next action
- [ ] **Charter check UI moment (demo-critical):**
  - Green: `✅ Aligned with Priority X`
  - Amber: `⚠️ Conflicts with Priority X — review required`
- [ ] Highlight referenced charter priority when item is flagged

**Done when:** Full run from button click → streaming feed → plan with badges.

### Phase B4 — Polish + Demo UX (hours 8–10)

- [ ] `VoiceTranscript` — filter `agent: "voice"` events, chat-bubble style
- [ ] Auto-scroll feed; color-code agents
- [ ] "Reset" button for second demo run
- [ ] Error/timeout states if LLM is slow
- [ ] Root `README.md`: setup for both apps, env vars, 90-second demo script

**Done when:** Demo is rehearseable end-to-end in browser.

### Agent B — Non-Goals

- No backend or agent logic
- No API contract changes without syncing Agent A
- No extra panels or features beyond MVP spec

---

## Conflict Avoidance

| Rule | Reason |
|------|--------|
| Agent A owns `backend/`, Agent B owns `frontend/` | Avoid merge conflicts |
| API changes go in `schemas.py` + `types.ts` together | Prevent drift |
| Agent B uses mock fallback until Gate 2 | Unblocks parallel work |
| One `run_id` per demo run | Clean state isolation |
| Git branches: `feat/backend` and `feat/frontend` | Merge after Gate 3 |

---

## Integration Checklist (both agents)

Before demo, verify together:

- [ ] `GET /api/health` returns ok from frontend
- [ ] Default charter preset matches on both sides
- [ ] SSE events parse correctly in `useAgentStream`
- [ ] At least one `charter_checks` entry has `status: "flagged"`
- [ ] Voice events render in transcript component
- [ ] Full run completes in under ~4 minutes
- [ ] Reset works for a second demo
- [ ] No real PHI in demo data

---

## Copy-Paste Prompts

### Agent A

> Build the APO backend per `architecture.md` and `SPLIT_PLAN.md`. Own only `backend/`. Implement FastAPI with `POST /api/run`, SSE `GET /api/stream/{run_id}`, `GET /api/plan/{run_id}`. Use Pydantic schemas from the shared contract. Create mock JSON for insurance, clinics, and sleep apnea treatments. Build an Executive Agent that runs Research, Insurance, Provider, Voice (simulated transcript), Synthesis, and Charter Check sequentially — stream each step via SSE. Use one LLM with distinct system prompts per agent. **Must output at least one flagged `charter_check`** (surgery vs "avoid surgery" priority). Start with stub SSE events so frontend can integrate early. Do not build frontend.

### Agent B

> Build the APO frontend per `architecture.md` and `SPLIT_PLAN.md`. Own only `frontend/` and root `README.md`. React + Vite SPA with three panels: Charter (3 preset priorities), live Agent Activity Feed (SSE from `/api/stream/{run_id}`), Final Plan with ✅/⚠️ charter badges. Types must match the shared contract in `types.ts`. Include mock event fallback in `src/mocks/demoEvents.ts` for development. Wire `POST /api/run` → SSE → `GET /api/plan/{run_id}`. Highlight the charter-check moment — flagged items must visibly reference charter priority. Add `VoiceTranscript` for `agent: "voice"` events. Do not build backend.

---

## If One Agent Finishes Early

| Finished first | Pick up |
|----------------|---------|
| **Agent A** | Real Twilio call, prompt tuning, golden-run cache for demo reliability |
| **Agent B** | Demo animations, charter panel polish, integration testing |

---

## 90-Second Demo Script

1. Show Patient Charter on screen (3 priorities)
2. Type: "I was just diagnosed with sleep apnea"
3. Live feed shows agents firing in sequence
4. Voice Executor transcript streams (simulated call to clinic)
5. Final plan renders with one ⚠️ flagged item + ✅ aligned items
6. Close: *"This took 4 minutes. For a patient, this normally takes a full day of phone calls."*

---

## Explicit Non-Goals (both agents)

- Not making real binding decisions or submitting forms
- Not storing or transmitting real PHI — synthetic patient data only
- Voice calls are informational/investigative only, not authorizing anything
- Do not build all 7 brainstormed concepts — MVP thread only
