"""Build run-scoped scenario — static demo or generated custom."""

from __future__ import annotations

from typing import Optional

from agents._helpers import load_data, load_mock_world
from agents.clinic_discovery import discover_clinics
from agents.scenario_generator import generate_evidence_and_insurance
from models.schemas import Charter, PatientLocation, PatientRecords, RunScenario


def load_demo_scenario() -> RunScenario:
    return RunScenario(
        run_mode="demo",
        treatment_evidence=load_data("treatment_evidence.json"),
        insurance_plans=load_data("insurance_plans.json"),
        mock_world=load_mock_world(),
        condition_label="sleep apnea",
    )


def _build_mock_world(clinics: dict, plan_name: str, insurance: dict) -> dict:
    est_cost = insurance.get("coverage", {}).get("typical_patient_cost", "$150-400 (estimated)")
    if isinstance(est_cost, dict):
        est_cost = "$150-400 (estimated after insurance)"
    return {
        "insurer": {
            "plan_name": plan_name,
            "covers_sleep_apnea_treatment_at": ["clinic_a", "clinic_b"],
            "covers_treatment_at": ["clinic_a", "clinic_b"],
            "member_id": insurance.get("patient", {}).get("member_id", "SYN-88421"),
        },
        "clinics": clinics,
        "coverage": {
            "est_cost": est_cost,
            "prior_auth_days": "3-5 business days",
        },
    }


async def build_custom_scenario(
    diagnosis: str,
    charter: Charter,
    location: PatientLocation,
    records: Optional[PatientRecords] = None,
) -> RunScenario:
    evidence, insurance, plan_name = await generate_evidence_and_insurance(
        diagnosis, charter, records
    )
    clinics = await discover_clinics(
        diagnosis, location, charter, plan_name, records
    )
    provider_names = [clinics[k]["name"] for k in ("clinic_a", "clinic_b", "clinic_c")]
    insurance["in_network_providers"] = provider_names

    mock_world = _build_mock_world(clinics, plan_name, insurance)
    condition_label = evidence.get("diagnosis", diagnosis)

    return RunScenario(
        run_mode="custom",
        treatment_evidence=evidence,
        insurance_plans=insurance,
        mock_world=mock_world,
        location=location,
        condition_label=str(condition_label),
    )
