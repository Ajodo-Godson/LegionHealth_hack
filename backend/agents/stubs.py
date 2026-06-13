"""Stub agent implementations — fallback when XAI_API_KEY is missing."""

from pathlib import Path
import json

from typing import Optional

from models.schemas import (
    Charter,
    Plan,
    CharterCheck,
    RecommendedProvider,
    PatientRecords,
    ContradictionFound,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(name: str) -> dict:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def run_research(
    diagnosis: str, charter: Charter, records: Optional[PatientRecords] = None
) -> str:
    evidence = _load_json("treatment_evidence.json")
    first_line = [t for t in evidence["treatments"] if t["type"] == "first-line"]
    cpap = first_line[0] if first_line else evidence["treatments"][0]
    surgical = [t for t in evidence["treatments"] if t.get("surgery")]

    has_records = bool(
        records
        and (
            records.severity
            or records.comorbidities
            or records.prior_treatments
        )
    )

    if has_records and records and records.prior_treatments:
        tried = ", ".join(records.prior_treatments)
        return (
            f"Based on your records: patient already tried {tried} without adequate improvement. "
            f"Escalating to {cpap['name']} as next step ({cpap['effectiveness']}). "
            f"Surgical option ({surgical[0]['name']}) noted for charter review if CPAP fails."
        )

    return (
        f"General guidance for '{diagnosis}' (no records on file): "
        f"First-line recommendation is {cpap['name']} ({cpap['effectiveness']}). "
        f"Surgical option identified: {surgical[0]['name']} — reserved if conservative therapy fails."
    )


def run_insurance(diagnosis: str, charter: Charter) -> str:
    plan = _load_json("insurance_plans.json")
    cpap = plan["coverage"]["cpap"]
    return (
        f"Insurance analysis for {plan['patient']['plan_name']}. "
        f"CPAP covered (prior auth required). "
        f"Estimated patient cost after insurance: ${cpap['typical_patient_cost_after_insurance']}. "
        f"Deductible remaining: ${plan['patient']['deductible_remaining']}."
    )


def run_provider(diagnosis: str, charter: Charter) -> str:
    clinics = _load_json("clinics.json")["clinics"]
    northside = next(c for c in clinics if c["name"] == "Northside Sleep Center")
    return (
        f"Provider search complete. Top match: {northside['name']} "
        f"(wait {northside['wait_time_days']} days, rating {northside['rating']}). "
        f"In-network, CPAP setup available — aligns with charter priorities "
        f"(cost + treatment within 2 weeks). Phone: {northside['phone']}."
    )


def run_voice_clinic_b(diagnosis: str) -> list[str]:
    world = _load_json("mock_world.json")
    clinic = world["clinics"]["clinic_b"]
    plan = world["insurer"]["plan_name"]
    return [
        f"APO Voice Executor: Calling {clinic['name']}...",
        f"Receptionist: {clinic['name']}, how can I help you?",
        f"APO: Hi, I'm verifying coverage for a patient with {plan} recently diagnosed with sleep apnea.",
        f"Receptionist: I'm sorry — we stopped accepting {plan} in March 2026.",
        "APO: Can you confirm you are no longer in-network for this plan?",
        f"Receptionist: Correct. {clinic.get('reason', 'We dropped this plan')}. "
        "We can still see self-pay patients, but not under that insurance.",
        "APO: Understood. We'll note this discrepancy and verify another provider.",
    ]


def run_voice(diagnosis: str, charter: Charter) -> list[str]:
    return run_voice_clinic_b(diagnosis)


def run_synthesis(diagnosis: str, charter: Charter) -> str:
    return (
        "Synthesis complete. After live verification caught an insurer/provider mismatch at Clinic B, "
        "APO re-routed to Lakeside Sleep Medicine (Clinic C) — verified in-network, 6-day wait. "
        "CPAP path recommended; surgery considered and excluded per charter."
    )


def build_plan(
    diagnosis: str,
    charter: Charter,
    records: Optional[PatientRecords] = None,
    *,
    contradiction: Optional[ContradictionFound] = None,
    rerouted_to: str = "clinic_c",
    verification_trace: Optional[list[str]] = None,
) -> Plan:
    world = _load_json("mock_world.json")
    clinic = world["clinics"][rerouted_to]

    charter_checks = [
        CharterCheck(
            item="CPAP therapy via verified in-network clinic (Clinic C)",
            status="aligned",
            priority_ref=1,
            message="Aligned with Priority 1 (minimize out-of-pocket cost)",
        ),
        CharterCheck(
            item="Surgery (UPPP)",
            status="excluded",
            priority_ref=2,
            message=(
                "Considered and excluded — conflicts with Priority 2 (avoid surgery unless "
                "medically necessary). Not recommended unless CPAP fails."
            ),
        ),
        CharterCheck(
            item=f"Verified appointment within {clinic['wait_days']} days",
            status="aligned",
            priority_ref=3,
            message="Aligned with Priority 3 (start treatment within 2 weeks)",
        ),
    ]

    personalized = bool(
        records
        and (
            records.severity
            or records.comorbidities
            or records.prior_treatments
        )
    )

    if contradiction is None:
        from agents.verification import detect_contradiction

        contradiction = detect_contradiction()

    return Plan(
        recommended_provider=RecommendedProvider(
            name=clinic["name"],
            address=clinic["address"],
            phone=clinic["phone"],
        ),
        wait_time=f"{clinic['wait_days']} days",
        est_cost=world["coverage"]["cpap_est_cost"],
        coverage_status=(
            f"Verified in-network — CPAP covered, prior auth "
            f"{world['coverage']['prior_auth_days']}"
        ),
        eligible_trials=["Sleep Apnea CPAP Adherence Study (local IRB-approved)"],
        next_action=(
            f"Schedule intake at {clinic['name']} — verified after re-route from Clinic B mismatch"
        ),
        charter_checks=charter_checks,
        personalized=personalized,
        contradiction_found=contradiction,
        rerouted_to=rerouted_to,
        verification_trace=verification_trace or [],
    )
