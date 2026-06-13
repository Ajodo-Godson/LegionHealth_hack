"""Shared helpers for LLM agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from models.schemas import Charter, PatientRecords

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data(name: str) -> dict:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def load_mock_world() -> dict:
    return load_data("mock_world.json")


def get_clinic(world: dict, clinic_id: str) -> dict:
    return world["clinics"][clinic_id]


def format_charter(charter: Charter) -> str:
    priorities = sorted(charter.priorities, key=lambda p: p.rank)
    return "\n".join(f"Priority {p.rank}: {p.statement}" for p in priorities)


def records_provided(records: Optional[PatientRecords]) -> bool:
    if records is None:
        return False
    if records.severity and records.severity.strip():
        return True
    if records.comorbidities:
        return True
    if records.prior_treatments:
        return True
    return False


DEMO_DIAGNOSIS_KEYWORDS = (
    "sleep apnea",
    "obstructive sleep apnea",
    "osa",
    "cpap",
    "ahi",
)


def is_demo_diagnosis(diagnosis: str) -> bool:
    text = diagnosis.lower()
    return any(keyword in text for keyword in DEMO_DIAGNOSIS_KEYWORDS)


def format_records(records: Optional[PatientRecords]) -> str:
    if not records_provided(records):
        return "No patient records summary provided."

    assert records is not None
    lines: list[str] = []
    if records.severity:
        lines.append(f"Severity: {records.severity}")
    if records.comorbidities:
        lines.append(f"Comorbidities: {', '.join(records.comorbidities)}")
    if records.prior_treatments:
        lines.append(f"Prior treatments tried: {', '.join(records.prior_treatments)}")
    return "\n".join(lines)
