"""Discover specialist clinics near a patient location."""

from __future__ import annotations

import logging
from typing import Optional

from agents._helpers import format_charter, format_records
from llm.client import chat_json, has_api_key, load_prompt
from models.schemas import Charter, PatientLocation, PatientRecords

logger = logging.getLogger("apo.agents.clinic_discovery")


def _default_clinics(location: PatientLocation, specialty: str) -> dict:
    city = location.city
    state = location.state
    return {
        "clinic_a": {
            "id": "clinic_a",
            "name": f"{city} Specialty Care",
            "address": f"100 Main St, {city}, {state}",
            "phone": "(555) 555-0101",
            "accepts_plan": True,
            "wait_days": 10,
        },
        "clinic_b": {
            "id": "clinic_b",
            "name": f"{city} Medical Group",
            "address": f"250 Oak Ave, {city}, {state}",
            "phone": "(555) 555-0102",
            "accepts_plan": False,
            "reason": "Dropped this plan March 2026",
            "wait_days": 7,
        },
        "clinic_c": {
            "id": "clinic_c",
            "name": f"Regional {specialty.title()} Center",
            "address": f"88 Lakeview Blvd, {city}, {state}",
            "phone": "(555) 555-0103",
            "accepts_plan": True,
            "wait_days": 6,
        },
    }


async def discover_clinics(
    diagnosis: str,
    location: PatientLocation,
    charter: Charter,
    plan_name: str,
    records: Optional[PatientRecords] = None,
) -> dict:
    """Return mock_world-style clinics dict (clinic_a/b/c)."""
    if not has_api_key():
        return _default_clinics(location, "specialty")

    system = load_prompt("clinic_discovery")
    zip_part = f" ZIP {location.zip_code}" if location.zip_code else ""
    user = (
        f"Diagnosis (physician-provided): {diagnosis}\n"
        f"Location: {location.city}, {location.state}{zip_part}\n"
        f"Insurance plan to verify: {plan_name}\n\n"
        f"Patient charter:\n{format_charter(charter)}\n\n"
        f"Patient records:\n{format_records(records)}\n\n"
        'Return JSON: {"clinics": {"clinic_a": {...}, "clinic_b": {...}, "clinic_c": {...}}}'
    )

    try:
        data = await chat_json(system, user, temperature=0.3, max_tokens=1400)
        clinics = data.get("clinics", data)
        if not all(k in clinics for k in ("clinic_a", "clinic_b", "clinic_c")):
            raise ValueError("Missing clinic_a/b/c in discovery response")
        for key in ("clinic_a", "clinic_b", "clinic_c"):
            clinics[key]["id"] = key
        clinics["clinic_b"]["accepts_plan"] = False
        if not clinics["clinic_b"].get("reason"):
            clinics["clinic_b"]["reason"] = "Dropped this plan March 2026"
        return clinics
    except Exception as exc:
        logger.warning("clinic_discovery failed, using defaults: %s", exc)
        return _default_clinics(location, "specialty")
