"""Insurance agent — reasons over coverage data."""

from __future__ import annotations

import json

from agents._helpers import format_charter, load_data
from agents.stubs import run_insurance as stub_insurance
from llm.client import chat, has_api_key, load_prompt
from models.schemas import Charter


async def run_insurance(diagnosis: str, charter: Charter) -> str:
    if not has_api_key():
        return stub_insurance(diagnosis, charter)

    insurance = load_data("insurance_plans.json")
    system = load_prompt("insurance")
    user = (
        f"Diagnosis: {diagnosis}\n\n"
        f"Patient charter:\n{format_charter(charter)}\n\n"
        f"Insurance data (JSON):\n{json.dumps(insurance, indent=2)}\n\n"
        "Report coverage, deductible impact, prior auth, and estimated out-of-pocket for CPAP vs surgery."
    )

    try:
        return await chat(system, user, temperature=0.2, max_tokens=400)
    except Exception:
        return stub_insurance(diagnosis, charter)
