"""Live verification agents — parallel insurer + provider calls over mock_world."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from agents._helpers import format_charter, get_clinic, load_mock_world
from llm.client import chat, has_api_key, load_prompt
from models.schemas import Charter, ContradictionFound


@dataclass
class VerificationResults:
    insurance: str
    provider_a: str
    provider_b: str
    provider_c: Optional[str] = None
    contradiction: Optional[ContradictionFound] = None
    verification_trace: list[str] = None

    def __post_init__(self) -> None:
        if self.verification_trace is None:
            self.verification_trace = []


def stub_insurance_verification() -> str:
    world = load_mock_world()
    plan = world["insurer"]["plan_name"]
    clinics = world["insurer"]["covers_sleep_apnea_treatment_at"]
    names = [get_clinic(world, cid)["name"] for cid in clinics]
    return (
        f"✅ Insurer confirms {plan} covers sleep apnea treatment at "
        f"{names[0]} and {names[1]} (per payer directory, verified today)."
    )


def stub_provider_verification(clinic_id: str) -> str:
    world = load_mock_world()
    clinic = get_clinic(world, clinic_id)
    plan = world["insurer"]["plan_name"]

    if clinic.get("accepts_plan"):
        return (
            f"✅ {clinic['name']} confirms coverage for {plan}, "
            f"wait time {clinic['wait_days']} days, CPAP setup available."
        )

    reason = clinic.get("reason", "Plan not accepted")
    return (
        f"⚠️ {clinic['name']} says: We no longer accept {plan} — {reason}."
    )


def detect_contradiction() -> ContradictionFound:
    """Deterministic — compares insurer list vs clinic_b accepts_plan."""
    world = load_mock_world()
    insurer_covers = world["insurer"]["covers_sleep_apnea_treatment_at"]
    clinic_b = get_clinic(world, "clinic_b")
    plan = world["insurer"]["plan_name"]

    insurer_claim = (
        f"Insurer lists {clinic_b['name']} as in-network for {plan}"
    )
    provider_claim = (
        f"{clinic_b['name']} reports: {clinic_b.get('reason', 'plan not accepted')}"
    )

    if "clinic_b" in insurer_covers and not clinic_b.get("accepts_plan", True):
        return ContradictionFound(
            detected=True,
            insurer_claim=insurer_claim,
            provider_claim=provider_claim,
            clinic_id="clinic_b",
            clinic_name=clinic_b["name"],
            message=(
                "🔍 Conflict detected — insurer and provider disagree for this patient, today. "
                f"Insurer says covered; {clinic_b['name']} says it dropped {plan}."
            ),
        )

    return ContradictionFound(
        detected=False,
        insurer_claim=insurer_claim,
        provider_claim=provider_claim,
        clinic_id="clinic_b",
        clinic_name=clinic_b["name"],
        message="No contradiction detected.",
    )


async def run_insurance_verification(diagnosis: str, charter: Charter) -> str:
    if not has_api_key():
        return stub_insurance_verification()

    world = load_mock_world()
    system = load_prompt("insurance")
    user = (
        f"Diagnosis: {diagnosis}\n\n"
        f"Charter:\n{format_charter(charter)}\n\n"
        f"You are verifying live coverage with the insurer. Mock world (JSON):\n"
        f"{json.dumps(world['insurer'], indent=2)}\n\n"
        "Respond in 1-2 sentences. Confirm which clinics the plan covers for sleep apnea. "
        "Start with ✅ if confirming coverage."
    )
    try:
        return await chat(system, user, temperature=0.1, max_tokens=200)
    except Exception:
        return stub_insurance_verification()


async def run_provider_verification(
    clinic_id: str, diagnosis: str, charter: Charter
) -> str:
    if not has_api_key():
        return stub_provider_verification(clinic_id)

    world = load_mock_world()
    clinic = get_clinic(world, clinic_id)
    system = load_prompt("provider")
    user = (
        f"Diagnosis: {diagnosis}\n\n"
        f"Charter:\n{format_charter(charter)}\n\n"
        f"You are calling {clinic['name']} to verify coverage and wait time.\n"
        f"Clinic record (JSON):\n{json.dumps(clinic, indent=2)}\n\n"
        f"Patient plan: {world['insurer']['plan_name']}\n\n"
        "Respond in 1-2 sentences as the verification result. "
        "Use ✅ if they accept the plan, ⚠️ if they do not (include reason)."
    )
    try:
        return await chat(system, user, temperature=0.1, max_tokens=200)
    except Exception:
        return stub_provider_verification(clinic_id)
