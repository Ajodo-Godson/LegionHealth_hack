"""Generate synthetic treatment evidence + insurance for a custom diagnosis."""

from __future__ import annotations

import logging
from typing import Optional

from agents._helpers import format_charter, format_records
from llm.client import chat_json, has_api_key, load_prompt
from models.schemas import Charter, PatientRecords

logger = logging.getLogger("apo.agents.scenario_generator")


def _default_evidence(diagnosis: str) -> dict:
    return {
        "diagnosis": diagnosis,
        "treatments": [
            {
                "name": "First-line therapy",
                "type": "first-line",
                "evidence_level": "moderate",
                "summary": f"Standard first-line approach for {diagnosis}.",
                "cost_tier": "medium",
                "surgery": False,
            }
        ],
        "clinical_guidelines": [
            "Follow physician diagnosis; escalate if first-line fails.",
        ],
    }


def _default_insurance(plan_name: str = "BlueCross Silver PPO") -> dict:
    return {
        "patient": {
            "plan_name": plan_name,
            "member_id": "SYN-88421",
            "deductible_remaining": 850,
            "out_of_pocket_max_remaining": 3200,
        },
        "coverage": {
            "specialist_visit": {
                "covered": True,
                "prior_auth_required": True,
                "in_network_coinsurance": 20,
            }
        },
        "in_network_providers": [],
    }


async def generate_evidence_and_insurance(
    diagnosis: str,
    charter: Charter,
    records: Optional[PatientRecords] = None,
) -> tuple[dict, dict, str]:
    """Returns (treatment_evidence, insurance_plans, plan_name)."""
    if not has_api_key():
        plan = "BlueCross Silver PPO"
        return _default_evidence(diagnosis), _default_insurance(plan), plan

    system = load_prompt("scenario_generator")
    user = (
        f"Diagnosis (physician-provided — do not re-diagnose): {diagnosis}\n\n"
        f"Patient charter:\n{format_charter(charter)}\n\n"
        f"Patient records:\n{format_records(records)}\n\n"
        "Return JSON with keys:\n"
        '- "treatment_evidence": {diagnosis, treatments[], clinical_guidelines[]}\n'
        '- "insurance_plans": {patient, coverage, in_network_providers[]}\n'
        '- "plan_name": string (insurance plan name)\n'
        '- "condition_label": short label for the condition\n'
    )

    try:
        data = await chat_json(system, user, temperature=0.25, max_tokens=1600)
        evidence = data.get("treatment_evidence") or _default_evidence(diagnosis)
        insurance = data.get("insurance_plans") or _default_insurance()
        plan_name = data.get("plan_name") or insurance.get("patient", {}).get(
            "plan_name", "BlueCross Silver PPO"
        )
        if "patient" in insurance and isinstance(insurance["patient"], dict):
            insurance["patient"]["plan_name"] = plan_name
        return evidence, insurance, plan_name
    except Exception as exc:
        logger.warning("scenario_generator failed, using defaults: %s", exc)
        plan = "BlueCross Silver PPO"
        return _default_evidence(diagnosis), _default_insurance(plan), plan
