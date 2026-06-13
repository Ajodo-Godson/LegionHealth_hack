"""Voice Executor — Clinic B call transcript (contradiction source)."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Optional

from agents.stubs import run_voice_clinic_b as stub_voice_clinic_b

OnLineCallback = Callable[[str], Awaitable[None]]


async def run_voice_clinic_b(
    diagnosis: str,
    on_line: Optional[OnLineCallback] = None,
) -> list[str]:
    """Deterministic Clinic B transcript — planted contradiction for demo reliability."""
    lines = stub_voice_clinic_b(diagnosis)
    for line in lines:
        if on_line:
            await on_line(line)
        await asyncio.sleep(0.55)
    return lines
