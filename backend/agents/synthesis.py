"""Synthesis + charter check — produces structured Plan JSON from verified data."""

from __future__ import annotations

import json
from typing import Optional

from agents._helpers import format_charter, format_records, get_clinic, load_mock_world, records_provided
from agents.stubs import build_plan as stub_build_plan, run_synthesis as stub_synthesis
from llm.client import chat, chat_json, has_api_key, load_prompt
from models.schemas import Charter, CharterCheck, ContradictionFound, PatientRecords, Plan


async def run_synthesis(
    diagnosis: str,
    charter: Charter,
    *,
    research: str,
    insurance: str,
    provider: str,
    voice_transcript: str,
    records: Optional[PatientRecords] = None,
    verification_trace: Optional[list[str]] = None,
    rerouted_to: Optional[str] = None,
) -> str:
    if not has_api_key():
        return stub_synthesis(diagnosis, charter)

    trace = "\n".join(verification_trace or [])
    system = load_prompt("synthesis")
    user = (
        f"Diagnosis (from doctor): {diagnosis}\n\n"
        f"Charter:\n{format_charter(charter)}\n\n"
        f"Patient records:\n{format_records(records)}\n\n"
        f"Research:\n{research}\n\n"
        f"Verified insurance:\n{insurance}\n\n"
        f"Verified provider (after re-route to {rerouted_to}):\n{provider}\n\n"
        f"Verification trace:\n{trace}\n\n"
        f"Voice transcript:\n{voice_transcript}\n\n"
        "Write a 2-4 sentence synthesis using ONLY verified, reconciled data."
    )

    try:
        return await chat(system, user, temperature=0.2, max_tokens=400)
    except Exception:
        return stub_synthesis(diagnosis, charter)


async def build_plan(
    diagnosis: str,
    charter: Charter,
    *,
    research: str,
    insurance: str,
    provider: str,
    voice_transcript: str,
    synthesis: str,
    records: Optional[PatientRecords] = None,
    contradiction: Optional[ContradictionFound] = None,
    rerouted_to: Optional[str] = None,
    verification_trace: Optional[list[str]] = None,
) -> Plan:
    personalized = records_provided(records)
    clinic_id = rerouted_to or "clinic_c"

    if not has_api_key():
        return stub_build_plan(
            diagnosis,
            charter,
            records,
            contradiction=contradiction,
            rerouted_to=clinic_id,
            verification_trace=verification_trace,
        )

    world = load_mock_world()
    clinic = get_clinic(world, clinic_id)
    system = load_prompt("plan")
    user = (
        f"Diagnosis (from doctor): {diagnosis}\n\n"
        f"Charter:\n{format_charter(charter)}\n\n"
        f"Use verified clinic: {json.dumps(clinic, indent=2)}\n\n"
        f"Verification trace:\n{json.dumps(verification_trace or [], indent=2)}\n\n"
        f"Contradiction detected: {contradiction.detected if contradiction else False}\n"
        f"Rerouted to: {clinic_id}\n\n"
        f"Synthesis:\n{synthesis}\n\n"
        f"Set personalized to {str(personalized).lower()}. "
        f"Include contradiction_found, rerouted_to, verification_trace in JSON."
    )

    try:
        raw = await chat_json(system, user, temperature=0.1, max_tokens=1400)
        plan = Plan.model_validate(raw)
        plan = _normalize_charter_checks(plan)
        if not _has_surgery_transparency(plan):
            plan = _ensure_surgery_excluded(plan, charter)
        return _apply_verification_metadata(
            plan,
            personalized=personalized,
            contradiction=contradiction,
            rerouted_to=clinic_id,
            verification_trace=verification_trace,
            clinic=clinic,
            world=world,
        )
    except Exception:
        return stub_build_plan(
            diagnosis,
            charter,
            records,
            contradiction=contradiction,
            rerouted_to=clinic_id,
            verification_trace=verification_trace,
        )


def _has_surgery_transparency(plan: Plan) -> bool:
    return any("surg" in c.item.lower() or "uppp" in c.item.lower() for c in plan.charter_checks)


def _normalize_charter_checks(plan: Plan) -> Plan:
    """Reframe surgery alternatives as excluded transparency, not open review items."""
    normalized: list[CharterCheck] = []
    for check in plan.charter_checks:
        is_surgery = "surg" in check.item.lower() or "uppp" in check.item.lower()
        if is_surgery and check.status in ("flagged", "excluded"):
            normalized.append(
                check.model_copy(
                    update={
                        "status": "excluded",
                        "item": "Surgery (UPPP)",
                        "message": (
                            f"Considered and excluded — conflicts with Priority {check.priority_ref} "
                            f"(avoid surgery unless medically necessary). "
                            "Not recommended unless CPAP fails."
                        ),
                    }
                )
            )
        else:
            normalized.append(check)
    return plan.model_copy(update={"charter_checks": normalized})


def _ensure_surgery_excluded(plan: Plan, charter: Charter) -> Plan:
    surgery_priority = next(
        (p.rank for p in charter.priorities if "surgery" in p.statement.lower()),
        2,
    )
    checks = list(plan.charter_checks)
    checks.append(
        CharterCheck(
            item="Surgery (UPPP)",
            status="excluded",
            priority_ref=surgery_priority,
            message=(
                f"Considered and excluded — conflicts with Priority {surgery_priority} "
                f"(avoid surgery unless medically necessary). "
                "Not recommended unless CPAP fails."
            ),
        )
    )
    return plan.model_copy(update={"charter_checks": checks})


def _apply_verification_metadata(
    plan: Plan,
    *,
    personalized: bool,
    contradiction: Optional[ContradictionFound],
    rerouted_to: str,
    verification_trace: Optional[list[str]],
    clinic: dict,
    world: dict,
) -> Plan:
    return plan.model_copy(
        update={
            "personalized": personalized,
            "contradiction_found": contradiction,
            "rerouted_to": rerouted_to,
            "verification_trace": verification_trace or [],
            "recommended_provider": plan.recommended_provider.model_copy(
                update={
                    "name": clinic["name"],
                    "address": clinic["address"],
                    "phone": clinic["phone"],
                }
            ),
            "wait_time": f"{clinic['wait_days']} days",
            "coverage_status": (
                f"Verified in-network — CPAP covered, prior auth "
                f"{world['coverage']['prior_auth_days']}"
            ),
            "est_cost": world["coverage"]["cpap_est_cost"],
        }
    )
