# APO — Autonomous Patient Organization

Hackathon MVP: parallel live verification → planted contradiction → adaptive re-route → charter-checked plan.

**Core proof:** Insurer says Clinic B is covered; Clinic B says it dropped the plan — APO detects the mismatch and re-routes to Clinic C. This cannot be replicated with one LLM prompt.

See [`architecture.md`](./architecture.md) for full spec.

## Core principle

**APO never diagnoses.** The diagnosis comes from the patient's doctor as a given input. Optional structured records (severity, comorbidities, prior treatments) only **personalize** downstream research — they do not determine what condition the patient has.

## Quick start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # add your XAI_API_KEY
python3 -m uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/api` → `localhost:8000`.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `XAI_API_KEY` | Yes (for LLM) | xAI API key from [console.x.ai](https://console.x.ai) |
| `XAI_TEXT_MODEL` | No | Default `grok-3` — Research, Insurance, Provider, Synthesis |
| `XAI_VOICE_MODEL` | No | Default `grok-voice-latest` — Voice Executor via Grok Voice API |

Without `XAI_API_KEY`, agents fall back to stub responses (still demoable).

## Architecture

- **Parallel verification**: Insurance + Provider A + Provider B via `asyncio.gather`
- **Deterministic contradiction**: `backend/data/mock_world.json` — Clinic B planted mismatch
- **Adaptive re-route**: Provider C after Contradiction Detector fires
- **Optional records form**: personalizes Research only
- **Plan fields**: `contradiction_found`, `rerouted_to`, `verification_trace`, `personalized`, `charter_checks`

## Demo script (~2 minutes)

1. Show Patient Charter (3 priorities)
2. Diagnosis pre-filled — optionally **Fill demo records**
3. **Run APO** — three agents fire in parallel (same timestamps in feed)
4. Clinic B contradiction → re-route to Clinic C — narrate the mismatch out loud
5. Clinic B voice transcript streams
6. Plan: verification trace + charter flag + personalized badge
7. Close: *"Insurer said covered. Clinic said no. APO caught it and re-routed — live, for this patient, today."*

## API contract

```
POST /api/run
{
  "diagnosis": string,
  "charter": { "priorities": [{ "rank": number, "statement": string }] },
  "records": {
    "severity": string,
    "comorbidities": string[],
    "prior_treatments": string[]
  } | null
}

GET /api/plan/{run_id}
→ Plan includes personalized, contradiction_found, rerouted_to, verification_trace
```

See `SPLIT_PLAN.md` — do not break endpoint shapes without updating `frontend/src/types.ts`.

## Non-goals

- APO **does not diagnose** — diagnosis is physician-provided input
- Records **only personalize** research/planning — they do not determine the condition
- Not making real binding decisions or submitting forms
- Not storing/transmitting real PHI — demo uses synthetic patient data
- Voice calls are informational/investigative only, not authorizing anything
