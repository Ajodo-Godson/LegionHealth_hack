"""AgentPhone outbound calls + live transcript streaming."""

from __future__ import annotations

import json
import logging
import os
from typing import Awaitable, Callable, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("apo.telephony")

AGENTPHONE_API_KEY = os.getenv("AGENTPHONE_API_KEY", "")
AGENTPHONE_AGENT_ID = os.getenv("AGENTPHONE_AGENT_ID", "")
AGENTPHONE_TO_NUMBER = os.getenv("AGENTPHONE_TO_NUMBER", "")
AGENTPHONE_FROM_NUMBER_ID = os.getenv("AGENTPHONE_FROM_NUMBER_ID", "")
AGENTPHONE_API_BASE = os.getenv("AGENTPHONE_API_BASE", "https://api.agentphone.ai/v1").rstrip("/")

OnLineCallback = Callable[[str], Awaitable[None]]


def _load_insurance_plan() -> str:
    try:
        from agents._helpers import load_mock_world

        return load_mock_world()["insurer"]["plan_name"]
    except Exception:
        return "BlueCross Silver PPO"


def is_agentphone_configured() -> bool:
    return bool(AGENTPHONE_API_KEY and AGENTPHONE_AGENT_ID and AGENTPHONE_TO_NUMBER)


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {AGENTPHONE_API_KEY}",
        "Content-Type": "application/json",
    }


def _clinic_b_system_prompt(clinic_name: str, clinic_phone: str, insurance_plan: str) -> str:
    return f"""You are APO — Autonomous Patient Organization. You are NOT an AgentPhone demo, sales rep, or general assistant.

You are on a live outbound call to {clinic_name} ({clinic_phone}) verifying insurance for a patient with physician-provided sleep apnea diagnosis.

Your ONLY task: confirm whether {clinic_name} accepts {insurance_plan} for sleep apnea treatment TODAY.

Hard rules:
- One sentence per turn. Two maximum. Never more.
- Say who you are ONCE at the start: "Hi, this is APO calling on behalf of a patient."
- Ask ONE clear question about {insurance_plan} acceptance. Wait for the answer.
- Repeat back what you heard in one sentence. Thank them. End the call.
- Do NOT pitch AgentPhone, ask what they are building, or discuss unrelated products.
- Do NOT diagnose, prescribe, or authorize treatment.
- Total call under 60 seconds. When verification is complete, say goodbye and stop."""


def _clinic_b_initial_greeting(clinic_name: str) -> str:
    return (
        f"Hi, this is APO calling on behalf of a patient. "
        f"I need to verify insurance coverage with {clinic_name}."
    )


async def _create_outbound_call(
    clinic_name: str,
    clinic_phone: str,
    insurance_plan: str = "BlueCross Silver PPO",
) -> str:
    payload: dict = {
        "agentId": AGENTPHONE_AGENT_ID,
        "toNumber": AGENTPHONE_TO_NUMBER,
        "initialGreeting": _clinic_b_initial_greeting(clinic_name),
        "systemPrompt": _clinic_b_system_prompt(clinic_name, clinic_phone, insurance_plan),
        "voice": "Polly.Joanna",
    }
    if AGENTPHONE_FROM_NUMBER_ID:
        payload["fromNumberId"] = AGENTPHONE_FROM_NUMBER_ID

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{AGENTPHONE_API_BASE}/calls",
            headers=_auth_headers(),
            json=payload,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"AgentPhone API error {resp.status_code}: {resp.text[:500]}"
            )
        data = resp.json()

    call_id = data.get("id") or data.get("callId")
    if not call_id and isinstance(data.get("data"), dict):
        nested = data["data"]
        call_id = nested.get("id") or nested.get("callId")
    if not call_id:
        raise RuntimeError(f"AgentPhone call created but no call id in response: {data}")

    logger.info("AgentPhone outbound call started call_id=%s", call_id)
    return str(call_id)


async def _stream_transcript(
    call_id: str,
    on_line: Optional[OnLineCallback],
    lines: list[str],
) -> None:
    url = f"{AGENTPHONE_API_BASE}/calls/{call_id}/transcript/stream"
    event_type: Optional[str] = None
    data_buf: list[str] = []

    async def emit(line: str) -> None:
        lines.append(line)
        if on_line:
            await on_line(line)

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", url, headers=_auth_headers()) as resp:
            resp.raise_for_status()
            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line:
                    if data_buf:
                        payload = json.loads("\n".join(data_buf))
                        if event_type == "turn":
                            speaker = "APO" if payload.get("role") == "agent" else "Receptionist"
                            content = payload.get("content", "").strip()
                            if content:
                                await emit(f"{speaker}: {content}")
                        elif event_type == "ended":
                            return
                        event_type = None
                        data_buf = []
                    continue

                if line.startswith(":"):
                    continue
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_buf.append(line[5:].strip())


async def run_agentphone_clinic_call(
    run_id: str,
    clinic_name: str,
    clinic_phone: str,
    on_line: Optional[OnLineCallback] = None,
) -> list[str]:
    """
    Place outbound call via AgentPhone; stream live transcript turns to SSE.
    Demo calls AGENTPHONE_TO_NUMBER (your phone) with APO verifying Clinic B coverage.
    """
    del run_id  # reserved for webhook correlation
    if not is_agentphone_configured():
        raise RuntimeError("AgentPhone is not configured")

    lines: list[str] = []

    async def emit(line: str) -> None:
        lines.append(line)
        if on_line:
            await on_line(line)

    await emit(
        f"APO Voice Executor: Placing real outbound call via AgentPhone to {AGENTPHONE_TO_NUMBER}..."
    )
    await emit(f"APO: Verifying coverage with {clinic_name} ({clinic_phone})")

    call_id = await _create_outbound_call(
        clinic_name,
        clinic_phone,
        insurance_plan=_load_insurance_plan(),
    )
    await emit(f"APO: Call connected (ID {call_id[:12]}…). Live transcript streaming.")

    await _stream_transcript(call_id, on_line, lines)
    await emit("APO: Call complete — verification recorded.")
    return lines


def agentphone_config_summary() -> dict:
    """Non-secret config snapshot for health / test UI."""
    return {
        "configured": is_agentphone_configured(),
        "agent_id": AGENTPHONE_AGENT_ID[:8] + "…" if AGENTPHONE_AGENT_ID else None,
        "to_number": AGENTPHONE_TO_NUMBER,
        "from_number_id": AGENTPHONE_FROM_NUMBER_ID[:8] + "…"
        if AGENTPHONE_FROM_NUMBER_ID
        else None,
    }
