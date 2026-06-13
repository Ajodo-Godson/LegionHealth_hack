"""Provider agent — ranks clinics by charter priorities."""

from __future__ import annotations

import json

from agents._helpers import format_charter, load_data
from agents.stubs import run_provider as stub_provider
from llm.client import chat, has_api_key, load_prompt
from models.schemas import Charter


async def run_provider(diagnosis: str, charter: Charter) -> str:
    if not has_api_key():
        return stub_provider(diagnosis, charter)

    clinics = load_data("clinics.json")
    system = load_prompt("provider")
    user = (
        f"Diagnosis: {diagnosis}\n\n"
        f"Patient charter:\n{format_charter(charter)}\n\n"
        f"Clinic directory (JSON):\n{json.dumps(clinics, indent=2)}\n\n"
        "Select the best in-network clinic balancing cost, timeline, and surgery preference. "
        "Name the clinic, wait time, and phone number."
    )

    try:
        return await chat(system, user, temperature=0.2, max_tokens=400)
    except Exception:
        return stub_provider(diagnosis, charter)
