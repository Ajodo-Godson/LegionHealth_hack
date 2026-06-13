"""Grok Voice Agent API client — text-driven turns for demo transcript."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Awaitable, Callable, Optional

import websockets
from dotenv import load_dotenv

from llm.client import load_prompt

load_dotenv()

XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_VOICE_MODEL = os.getenv("XAI_VOICE_MODEL", "grok-voice-latest")
XAI_VOICE_URL = os.getenv(
    "XAI_VOICE_URL",
    f"wss://api.x.ai/v1/realtime?model={XAI_VOICE_MODEL}",
)
VOICE_TURN_TIMEOUT = float(os.getenv("XAI_VOICE_TURN_TIMEOUT", "45"))
MAX_CALL_TURNS = int(os.getenv("APO_VOICE_MAX_TURNS", "5"))


def _voice_url() -> str:
    if "model=" in XAI_VOICE_URL:
        return XAI_VOICE_URL
    sep = "&" if "?" in XAI_VOICE_URL else "?"
    return f"{XAI_VOICE_URL}{sep}model={XAI_VOICE_MODEL}"


async def _collect_response_text(ws) -> str:
    """Wait for a single assistant response transcript from Grok Voice."""
    parts: list[str] = []

    while True:
        raw = await ws.recv()
        event = json.loads(raw)
        event_type = event.get("type", "")

        if event_type in (
            "response.output_audio_transcript.delta",
            "response.output_text.delta",
            "response.text.delta",
        ):
            delta = event.get("delta", "")
            if isinstance(delta, str):
                parts.append(delta)

        elif event_type in (
            "response.output_audio_transcript.done",
            "response.output_text.done",
            "response.text.done",
        ):
            transcript = event.get("transcript") or event.get("text") or ""
            if transcript:
                return str(transcript).strip()
            if parts:
                return "".join(parts).strip()

        elif event_type == "response.done":
            if parts:
                return "".join(parts).strip()
            output = event.get("response", {}).get("output", [])
            for item in output:
                for block in item.get("content", []):
                    if block.get("type") in ("output_text", "text", "audio"):
                        text = block.get("text") or block.get("transcript")
                        if text:
                            return str(text).strip()
            return "".join(parts).strip() or "Understood."

        elif event_type == "error":
            raise RuntimeError(event.get("error", {}).get("message", "Grok Voice error"))


async def voice_turn(
    instructions: str,
    user_text: Optional[str] = None,
    *,
    voice: str = "rex",
) -> str:
    """Run one Grok Voice turn; returns assistant transcript text."""
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY is not set")

    headers = {"Authorization": f"Bearer {XAI_API_KEY}"}

    async with websockets.connect(
        _voice_url(),
        additional_headers=headers,
        open_timeout=VOICE_TURN_TIMEOUT,
        close_timeout=5,
    ) as ws:
        await ws.send(
            json.dumps(
                {
                    "type": "session.update",
                    "session": {
                        "instructions": instructions,
                        "voice": voice,
                        "turn_detection": None,
                        "modalities": ["text", "audio"],
                    },
                }
            )
        )

        if user_text:
            await ws.send(
                json.dumps(
                    {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": user_text}],
                        },
                    }
                )
            )

        await ws.send(json.dumps({"type": "response.create"}))
        return await asyncio.wait_for(_collect_response_text(ws), timeout=VOICE_TURN_TIMEOUT)


OnLineCallback = Callable[[str], Awaitable[None]]


async def run_simulated_clinic_call(
    diagnosis: str,
    clinic_name: str,
    insurance_plan: str,
    clinic_wait_days: int,
    clinic_phone: str,
    on_line: Optional[OnLineCallback] = None,
) -> list[str]:
    """
    Simulate an outbound clinic call using Grok Voice (APO) + text LLM (receptionist).
    Streams lines as 'APO: ...' or 'Receptionist: ...'.
    """
    from llm.client import chat

    executor_prompt = load_prompt("voice_executor")
    receptionist_prompt = load_prompt("voice_receptionist")

    context = (
        f"Patient diagnosis: {diagnosis}. "
        f"Calling: {clinic_name} ({clinic_phone}). "
        f"Insurance: {insurance_plan}. "
        f"Typical new patient wait: {clinic_wait_days} days. "
        "Ask one question per turn about availability, CPAP setup, prior auth, and device delivery."
    )
    instructions = f"{executor_prompt}\n\n{context}"

    lines: list[str] = []
    last_apo = ""

    async def emit(line: str) -> None:
        lines.append(line)
        if on_line:
            await on_line(line)

    opening = await voice_turn(
        instructions,
        user_text="You are now connected to the clinic receptionist. Introduce yourself and ask your first question.",
    )
    last_apo = _normalize_speaker_line(opening, "APO")
    await emit(f"APO: {last_apo}")

    for _ in range(MAX_CALL_TURNS):
        receptionist_reply = await chat(
            receptionist_prompt,
            (
                f"Clinic: {clinic_name} ({clinic_phone}).\n"
                f"In-network with {insurance_plan}.\n"
                f"New patient consult wait: {clinic_wait_days} days.\n"
                f"CPAP setup available. Prior auth typically 3-5 business days.\n"
                f"The APO caller just said: \"{last_apo}\"\n"
                "Respond naturally in 1-2 sentences as the receptionist."
            ),
            temperature=0.5,
            max_tokens=200,
        )
        receptionist_line = _normalize_speaker_line(receptionist_reply, "Receptionist")
        await emit(f"Receptionist: {receptionist_line}")

        if _should_end_call(receptionist_line, last_apo):
            break

        apo_reply = await voice_turn(
            instructions,
            user_text=f"The receptionist said: \"{receptionist_line}\". Continue the call with your next question or closing.",
        )
        last_apo = _normalize_speaker_line(apo_reply, "APO")
        await emit(f"APO: {last_apo}")

        if _should_end_call(receptionist_line, last_apo):
            break

    return lines


def _normalize_speaker_line(text: str, default_speaker: str) -> str:
    cleaned = text.strip()
    for prefix in ("APO:", "APO Voice Executor:", "Receptionist:", "Clinic:"):
        if cleaned.startswith(prefix):
            return cleaned.split(":", 1)[1].strip()
    return cleaned


def _should_end_call(receptionist: str, apo: str) -> bool:
    combined = f"{receptionist} {apo}".lower()
    closing_phrases = (
        "thank you",
        "have a great day",
        "goodbye",
        "you're welcome",
        "we'll include this",
    )
    return any(phrase in combined for phrase in closing_phrases) and "?" not in apo[-40:]
