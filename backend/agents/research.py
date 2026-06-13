"""Research agent — reasons over treatment evidence."""

from __future__ import annotations

import json
import logging
from typing import Optional

from agents._helpers import format_charter, format_records, load_data, records_provided
from agents.stubs import run_research as stub_research
from llm.client import chat, has_api_key, load_prompt
from models.schemas import Charter, PatientRecords

logger = logging.getLogger("apo.agents.research")


async def run_research(
    diagnosis: str,
    charter: Charter,
    records: Optional[PatientRecords] = None,
) -> str:
    if not has_api_key():
        logger.warning("research: no API key — using stub")
        return stub_research(diagnosis, charter, records)

    evidence = load_data("treatment_evidence.json")
    system = load_prompt("research")
    records_block = format_records(records)

    if records_provided(records):
        records_instruction = (
            "Patient records ARE provided. Personalize your response — reference prior "
            "treatments tried and escalate appropriately (e.g. lifestyle failed → CPAP)."
        )
    else:
        records_instruction = (
            "No patient records provided. Give general first-line guidance for this diagnosis."
        )

    user = (
        f"Diagnosis (from patient's doctor — do not re-diagnose): {diagnosis}\n\n"
        f"Patient charter:\n{format_charter(charter)}\n\n"
        f"Patient records summary:\n{records_block}\n\n"
        f"{records_instruction}\n\n"
        f"Treatment evidence (JSON):\n{json.dumps(evidence, indent=2)}"
    )

    try:
        result = await chat(system, user, temperature=0.2, max_tokens=450)
        logger.info("research: LLM response received (%d chars)", len(result))
        return result
    except Exception as exc:
        logger.error("research: LLM failed, using stub — %s", exc)
        return stub_research(diagnosis, charter, records)
