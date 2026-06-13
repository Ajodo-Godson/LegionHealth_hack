# Deploy APO (LegionHealth)

Vercel hosts the **React frontend**. The **FastAPI backend** must run on a persistent server (Render) because APO uses SSE streaming, in-memory run state, and multi-minute LLM calls — not compatible with Vercel serverless.

## 1. Backend → Render (free tier)

1. Push this repo to GitHub (`Ajodo-Godson/LegionHealth_hack`).
2. Go to [render.com](https://render.com) → **New** → **Blueprint** → connect the repo.
3. Render reads `render.yaml` and creates `legionhealth-apo-api`.
4. In Render → **Environment**, add secrets:
   - `XAI_API_KEY` (required)
   - `AGENTPHONE_*` vars if using real calls
5. Deploy. Note the URL, e.g. `https://legionhealth-apo-api.onrender.com`.

Health check: `https://YOUR-API.onrender.com/api/health`

> Free tier sleeps after ~15 min idle — first request may take ~30s to wake.

## 2. Frontend → Vercel

### Option A — Vercel dashboard (recommended)

1. [vercel.com](https://vercel.com) → **Add New Project** → import `LegionHealth_hack`.
2. Set **Root Directory** to `frontend`.
3. Framework: **Vite** (auto-detected).
4. **Environment Variables** (Production):
   ```
   VITE_API_URL=https://legionhealth-apo-api.onrender.com/api
   ```
   Replace with your Render URL + `/api`.
5. Deploy.

### Option B — CLI

```bash
cd frontend
npm install
vercel link          # first time only
vercel env add VITE_API_URL production
# paste: https://YOUR-API.onrender.com/api
vercel --prod
```

## 3. Verify

1. Open your `*.vercel.app` URL.
2. Stub banner should **not** appear if backend is reachable.
3. Run **Demo (sleep apnea)** → full contradiction flow.

## Architecture

```
Browser (Vercel)  --HTTPS-->  Render (FastAPI + SSE)
                    |
                    +------>  api.x.ai (Grok)
                    +------>  AgentPhone (optional)
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Stub mode" / mock data | `VITE_API_URL` wrong or backend asleep |
| CORS error | Backend `ALLOWED_ORIGIN_REGEX` includes `https://.*\.vercel\.app` (default) |
| Plan empty | Ensure latest `main.py` sends `plan` in `plan_ready` SSE |
| Custom mode | Needs full orchestrator + scenario_builder on deployed branch |
