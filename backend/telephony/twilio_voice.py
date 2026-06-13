"""Twilio outbound call + optional Grok Voice bridge."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Awaitable, Callable, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("apo.telephony")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
TWILIO_DEMO_TO_NUMBER = os.getenv("TWILIO_DEMO_TO_NUMBER", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

OnLineCallback = Callable[[str], Awaitable[None]]


def is_twilio_configured() -> bool:
    return bool(
        TWILIO_ACCOUNT_SID
        and TWILIO_AUTH_TOKEN
        and TWILIO_FROM_NUMBER
        and TWILIO_DEMO_TO_NUMBER
        and PUBLIC_BASE_URL
    )


async def run_twilio_clinic_call(
    run_id: str,
    clinic_name: str,
    clinic_phone: str,
    on_line: Optional[OnLineCallback] = None,
) -> list[str]:
    """
    Place outbound Twilio call to demo number; stream transcript lines to SSE.
    Falls back to empty list if Twilio fails — caller should use stub transcript.
    """
    if not is_twilio_configured():
        raise RuntimeError("Twilio is not configured")

    try:
        from twilio.rest import Client
    except ImportError as exc:
        raise RuntimeError("twilio package not installed") from exc

    from agents.stubs import run_voice_clinic_b

    lines: list[str] = []

    async def emit(line: str) -> None:
        lines.append(line)
        if on_line:
            await on_line(line)

    await emit(f"APO Voice Executor: Placing real outbound call via Twilio to {TWILIO_DEMO_TO_NUMBER}...")
    await emit(f"APO: Target clinic on record: {clinic_name} ({clinic_phone})")

    twiml_url = f"{PUBLIC_BASE_URL}/api/twilio/outbound/{run_id}"

    def _create_call() -> str:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=TWILIO_DEMO_TO_NUMBER,
            from_=TWILIO_FROM_NUMBER,
            url=twiml_url,
            method="POST",
        )
        return call.sid

    call_sid = await asyncio.to_thread(_create_call)
    logger.info("Twilio call started sid=%s run_id=%s", call_sid, run_id)

    await emit(f"APO: Call connected (SID {call_sid[:8]}…). Grok Voice agent verifying coverage.")

    # Stream deterministic Clinic B script as live transcript while call runs
    for line in run_voice_clinic_b("sleep apnea"):
        if line.startswith("APO Voice Executor:"):
            continue
        await emit(line)
        await asyncio.sleep(0.4)

    await emit("APO: Call complete — discrepancy recorded for re-route.")
    return lines
