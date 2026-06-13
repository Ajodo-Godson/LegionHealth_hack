"""Unified real-phone providers — AgentPhone preferred, Twilio fallback."""

from __future__ import annotations

from typing import Awaitable, Callable, Literal, Optional

from telephony.agentphone_voice import is_agentphone_configured, run_agentphone_clinic_call
from telephony.twilio_voice import is_twilio_configured, run_twilio_clinic_call

OnLineCallback = Callable[[str], Awaitable[None]]
PhoneProvider = Literal["agentphone", "twilio", "none"]


def is_real_phone_configured() -> bool:
    return is_agentphone_configured() or is_twilio_configured()


def preferred_phone_provider() -> PhoneProvider:
    if is_agentphone_configured():
        return "agentphone"
    if is_twilio_configured():
        return "twilio"
    return "none"


async def run_real_clinic_call(
    run_id: str,
    clinic_name: str,
    clinic_phone: str,
    on_line: Optional[OnLineCallback] = None,
) -> list[str]:
    provider = preferred_phone_provider()
    if provider == "agentphone":
        return await run_agentphone_clinic_call(
            run_id, clinic_name, clinic_phone, on_line=on_line
        )
    if provider == "twilio":
        return await run_twilio_clinic_call(
            run_id, clinic_name, clinic_phone, on_line=on_line
        )
    raise RuntimeError("No real phone provider configured")
