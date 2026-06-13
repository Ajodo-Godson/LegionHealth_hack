"""Voice consent gate — pause orchestration until patient authorizes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VoiceConsentGate:
    event: asyncio.Event = field(default_factory=asyncio.Event)
    granted: bool = False
    use_twilio: bool = False

    def resolve(self, granted: bool, use_twilio: bool = False) -> None:
        self.granted = granted
        self.use_twilio = use_twilio and granted
        self.event.set()

    async def wait(
        self,
        queue: asyncio.Queue,
        *,
        clinic_name: str,
        clinic_phone: str,
        purpose: str,
        timeout: float = 300.0,
    ) -> tuple[bool, bool]:
        await queue.put(
            (
                "voice_consent_required",
                {
                    "clinic_name": clinic_name,
                    "clinic_phone": clinic_phone,
                    "purpose": purpose,
                },
            )
        )
        try:
            await asyncio.wait_for(self.event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return False, False
        return self.granted, self.use_twilio
