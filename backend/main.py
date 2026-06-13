"""APO Backend — FastAPI application."""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from llm.client import has_api_key, XAI_TEXT_MODEL
from models.schemas import (
    AgentLogEntry,
    HealthResponse,
    Plan,
    RunRequest,
    RunResponse,
    VoiceConsentBody,
)
from orchestrator import run_orchestration
from telephony.consent import VoiceConsentGate
from telephony.twilio_voice import PUBLIC_BASE_URL, is_twilio_configured
from telephony.twiml import outbound_twiml

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()

logger = logging.getLogger("apo")
logging.basicConfig(level=logging.INFO)


@dataclass
class RunState:
    diagnosis: str
    charter: Any
    agent_log: list[AgentLogEntry] = field(default_factory=list)
    plan: Optional[Plan] = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    done: bool = False
    voice_consent: VoiceConsentGate = field(default_factory=VoiceConsentGate)


runs: dict[str, RunState] = {}

app = FastAPI(title="APO Backend", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    mode = "live" if has_api_key() else "stub"
    twilio = "yes" if is_twilio_configured() else "no"
    logger.info(
        "APO backend started — dir=%s mode=%s model=%s twilio=%s",
        BACKEND_DIR,
        mode,
        XAI_TEXT_MODEL,
        twilio,
    )


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        llm_enabled=has_api_key(),
        mode="live" if has_api_key() else "stub",
        backend_dir=str(BACKEND_DIR),
        twilio_enabled=is_twilio_configured(),
    )


@app.post("/api/run", response_model=RunResponse)
async def start_run(body: RunRequest) -> RunResponse:
    run_id = str(uuid.uuid4())
    state = RunState(diagnosis=body.diagnosis, charter=body.charter)
    runs[run_id] = state

    async def _background() -> None:
        try:
            plan = await run_orchestration(
                run_id,
                body.diagnosis,
                body.charter,
                state.queue,
                state.agent_log,
                body.records,
                voice_consent=state.voice_consent,
            )
            state.plan = plan
            await state.queue.put(("plan_ready", {"run_id": run_id}))
            await state.queue.put(("done", {}))
        except Exception as e:
            logger.exception("Run failed")
            await state.queue.put(
                (
                    "agent_log",
                    {
                        "agent": "executive",
                        "action": "error",
                        "output": f"Run failed: {e}",
                        "timestamp": __import__("datetime").datetime.now(
                            __import__("datetime").timezone.utc
                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    },
                )
            )
            await state.queue.put(("done", {}))
        finally:
            state.done = True

    asyncio.create_task(_background())
    return RunResponse(run_id=run_id)


@app.post("/api/run/{run_id}/voice-consent")
async def submit_voice_consent(run_id: str, body: VoiceConsentBody) -> dict:
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run not found")

    state = runs[run_id]
    if state.done:
        raise HTTPException(status_code=409, detail="Run already finished")

    state.voice_consent.resolve(body.granted, body.use_twilio)
    return {"ok": True, "granted": body.granted, "use_twilio": body.use_twilio}


@app.post("/api/twilio/outbound/{run_id}")
async def twilio_outbound_twiml(run_id: str) -> Response:
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run not found")
    if not PUBLIC_BASE_URL:
        raise HTTPException(status_code=500, detail="PUBLIC_BASE_URL not configured")

    twiml = outbound_twiml(run_id, PUBLIC_BASE_URL)
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/api/twilio/media/{run_id}")
async def twilio_media_stream(run_id: str, websocket: WebSocket) -> None:
    """Accept Twilio media stream; full Grok audio bridge is future work."""
    await websocket.accept()
    logger.info("Twilio media stream connected run_id=%s", run_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Twilio media stream closed run_id=%s", run_id)


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/api/stream/{run_id}")
async def stream_run(run_id: str) -> StreamingResponse:
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run not found")

    state = runs[run_id]

    async def event_generator():
        while True:
            try:
                event_type, payload = await asyncio.wait_for(
                    state.queue.get(), timeout=300.0
                )
                yield _format_sse(event_type, payload)
                if event_type == "done":
                    break
            except asyncio.TimeoutError:
                yield _format_sse("done", {})
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/plan/{run_id}", response_model=Plan)
async def get_plan(run_id: str) -> Plan:
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run not found")

    state = runs[run_id]
    if state.plan is None:
        raise HTTPException(status_code=404, detail="Plan not ready yet")

    return state.plan
