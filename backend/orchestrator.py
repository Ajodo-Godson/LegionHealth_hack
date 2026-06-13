"""Executive agent — parallel verification, contradiction detection, adaptive re-route."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from agents.research import run_research
from agents.synthesis import build_plan, run_synthesis
from agents.verification import (
    detect_contradiction,
    run_insurance_verification,
    run_provider_verification,
    stub_provider_verification,
)
from agents.voice_agent import run_voice_clinic_b
from agents._helpers import get_clinic, load_mock_world, records_provided
from models.schemas import AgentLogEntry, Charter, PatientRecords, Plan
from telephony.consent import VoiceConsentGate
from telephony.twilio_voice import run_twilio_clinic_call


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def _emit_log(
    queue: asyncio.Queue,
    agent: str,
    action: str,
    output: str,
    input_text: Optional[str] = None,
) -> AgentLogEntry:
    entry = AgentLogEntry(
        agent=agent,
        action=action,
        input=input_text,
        output=output,
        timestamp=_now_iso(),
    )
    await queue.put(("agent_log", entry.model_dump()))
    return entry


async def run_orchestration(
    run_id: str,
    diagnosis: str,
    charter: Charter,
    queue: asyncio.Queue,
    log_store: list[AgentLogEntry],
    records: Optional[PatientRecords] = None,
    voice_consent: Optional[VoiceConsentGate] = None,
) -> Plan:
    records_note = (
        " Records included — research will personalize."
        if records_provided(records)
        else " No records — general guidance."
    )
    await _emit_log(
        queue,
        "executive",
        "started",
        f"Physician diagnosis received: {diagnosis}.{records_note}",
    )

    # Research
    await _emit_log(
        queue, "research", "running", "Analyzing treatment evidence for sleep apnea..."
    )
    research_out = await run_research(diagnosis, charter, records)
    entry = await _emit_log(queue, "research", "completed", research_out, diagnosis)
    log_store.append(entry)

    # Parallel live verification
    await _emit_log(
        queue,
        "executive",
        "parallel_dispatch",
        "Firing parallel verification: Insurance Agent + Provider A + Provider B (concurrent)",
    )
    await asyncio.gather(
        _emit_log(
            queue,
            "insurance",
            "running",
            "Live verification call to insurer — checking in-network clinics...",
        ),
        _emit_log(
            queue,
            "provider_a",
            "running",
            "Calling Northside Sleep Center (Clinic A) to verify coverage + wait time...",
        ),
        _emit_log(
            queue,
            "provider_b",
            "running",
            "Calling Metro Pulmonary & Sleep (Clinic B) to verify coverage + wait time...",
        ),
    )

    insurance_out, provider_a_out, provider_b_out = await asyncio.gather(
        run_insurance_verification(diagnosis, charter),
        run_provider_verification("clinic_a", diagnosis, charter),
        run_provider_verification("clinic_b", diagnosis, charter),
    )

    for agent, output in (
        ("insurance", insurance_out),
        ("provider_a", provider_a_out),
        ("provider_b", provider_b_out),
    ):
        entry = await _emit_log(queue, agent, "completed", output)
        log_store.append(entry)

    verification_trace = [insurance_out, provider_a_out, provider_b_out]

    # Contradiction detection (deterministic)
    await _emit_log(
        queue,
        "contradiction_detector",
        "running",
        "Comparing insurer claims against provider responses...",
    )
    contradiction = detect_contradiction()
    entry = await _emit_log(
        queue, "contradiction_detector", "completed", contradiction.message
    )
    log_store.append(entry)
    verification_trace.append(contradiction.message)

    provider_c_out: Optional[str] = None
    rerouted_to: Optional[str] = None

    if contradiction.detected:
        await _emit_log(
            queue,
            "executive",
            "reroute",
            "→ Dispatching Provider Agent C to Lakeside Sleep Medicine (Clinic C)",
        )
        await _emit_log(
            queue,
            "provider_c",
            "running",
            "Calling Lakeside Sleep Medicine (Clinic C) after contradiction...",
        )
        provider_c_out = await run_provider_verification(
            "clinic_c", diagnosis, charter
        )
        entry = await _emit_log(queue, "provider_c", "completed", provider_c_out)
        log_store.append(entry)
        verification_trace.append(provider_c_out)
        rerouted_to = "clinic_c"
    else:
        provider_c_out = stub_provider_verification("clinic_c")
        rerouted_to = "clinic_a"

    await _emit_log(
        queue,
        "executive",
        "reconciling",
        "Reconciling verified results — replaying Clinic B call that surfaced the contradiction...",
    )

    world = load_mock_world()
    clinic_b = get_clinic(world, "clinic_b")
    gate = voice_consent or VoiceConsentGate()
    granted, use_twilio = await gate.wait(
        queue,
        clinic_name=clinic_b["name"],
        clinic_phone=clinic_b["phone"],
        purpose="Verify insurance coverage for sleep apnea treatment (informational only — not authorizing treatment)",
    )

    voice_transcript = ""

    async def on_voice_line(line: str) -> None:
        entry = await _emit_log(queue, "voice", "transcript", line)
        log_store.append(entry)

    if granted:
        mode_label = "Twilio outbound" if use_twilio else "simulated transcript"
        await _emit_log(
            queue,
            "voice",
            "started",
            f"Clinic B verification call authorized ({mode_label})...",
        )

        transcript_lines: list[str] = []
        if use_twilio:
            try:
                transcript_lines = await run_twilio_clinic_call(
                    run_id,
                    clinic_b["name"],
                    clinic_b["phone"],
                    on_line=on_voice_line,
                )
            except Exception as exc:
                await _emit_log(
                    queue,
                    "voice",
                    "fallback",
                    f"Twilio unavailable ({exc}) — using simulated Clinic B transcript.",
                )
                transcript_lines = await run_voice_clinic_b(
                    diagnosis, on_line=on_voice_line
                )
        else:
            transcript_lines = await run_voice_clinic_b(
                diagnosis, on_line=on_voice_line
            )

        voice_transcript = "\n".join(transcript_lines)
        await _emit_log(
            queue, "voice", "completed", "Clinic B call transcript complete"
        )
    else:
        await _emit_log(
            queue,
            "voice",
            "skipped",
            "Patient skipped outbound call — building plan from verified data only.",
        )

    # Synthesis from verified data
    verified_provider_summary = provider_c_out or provider_a_out
    await _emit_log(
        queue, "synthesis", "running", "Building plan from verified, reconciled data only..."
    )
    synthesis_out = await run_synthesis(
        diagnosis,
        charter,
        research=research_out,
        insurance=insurance_out,
        provider=verified_provider_summary,
        voice_transcript=voice_transcript,
        records=records,
        verification_trace=verification_trace,
        rerouted_to=rerouted_to,
    )
    entry = await _emit_log(queue, "synthesis", "completed", synthesis_out)
    log_store.append(entry)

    await _emit_log(
        queue,
        "charter_check",
        "running",
        "Checking recommendations against patient charter...",
    )
    plan = await build_plan(
        diagnosis,
        charter,
        research=research_out,
        insurance=insurance_out,
        provider=verified_provider_summary,
        voice_transcript=voice_transcript,
        synthesis=synthesis_out,
        records=records,
        contradiction=contradiction,
        rerouted_to=rerouted_to,
        verification_trace=verification_trace,
    )
    excluded = [c for c in plan.charter_checks if c.status == "excluded"]
    flagged = [c for c in plan.charter_checks if c.status == "flagged"]
    check_summary = (
        f"Charter check complete: {len(plan.charter_checks)} items reviewed, "
        f"{len(excluded)} alternative(s) excluded per charter"
        + (f", {len(flagged)} flagged for review" if flagged else "")
        + "."
    )
    entry = await _emit_log(queue, "charter_check", "completed", check_summary)
    log_store.append(entry)

    return plan
