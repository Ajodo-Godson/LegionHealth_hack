"""Find real local clinics via Grok web_search tool."""

from __future__ import annotations

import logging

from llm.client import has_api_key, web_search_query
from models.schemas import PatientLocation

logger = logging.getLogger("apo.research.clinics")


def _condition_label(diagnosis: str) -> str:
    cleaned = diagnosis.strip()
    for prefix in (
        "I have ",
        "I was just diagnosed with ",
        "I was diagnosed with ",
        "Diagnosed with ",
    ):
        if cleaned.lower().startswith(prefix.lower()):
            return cleaned[len(prefix) :].strip()
    return cleaned


def _treatment_search_terms(treatment_evidence: dict | None) -> list[str]:
    if not treatment_evidence:
        return []
    names: list[str] = []
    for item in treatment_evidence.get("treatments", []):
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return names[:6]


def _search_prompt(
    diagnosis: str,
    location: PatientLocation,
    treatment_evidence: dict | None = None,
) -> str:
    condition = _condition_label(diagnosis)
    zip_part = f" ZIP {location.zip_code}" if location.zip_code else ""
    treatments = _treatment_search_terms(treatment_evidence)
    treatment_line = (
        f"- Prioritize clinics that offer these evidence-based treatments: "
        f"{', '.join(treatments)}.\n"
        if treatments
        else ""
    )
    guidelines = treatment_evidence.get("clinical_guidelines", []) if treatment_evidence else []
    guideline_line = (
        f"- Clinical context: {'; '.join(str(g) for g in guidelines[:3])}.\n"
        if guidelines
        else ""
    )
    return (
        f"Search the web for REAL medical clinics, ophthalmology practices, or hospitals "
        f"treating: {condition}\n"
        f"Location: {location.city}, {location.state}{zip_part}\n\n"
        "Requirements:\n"
        "- List at least 4 ACTUAL named facilities patients would find on Google "
        "(not made-up names).\n"
        "- For each: full name, street address, phone if available, website URL, "
        "and key treatments offered.\n"
        f"{treatment_line}"
        f"{guideline_line}"
        "- Prefer board-certified specialists and top-rated local condition-specific centers.\n"
        "- Note which appear to accept major PPO insurance when that info is public.\n"
        "Format as a structured list with one clinic per bullet."
    )


async def search_local_clinics(
    diagnosis: str,
    location: PatientLocation,
    treatment_evidence: dict | None = None,
) -> tuple[str, list[str]]:
    """Returns (research_text, citation_urls). Empty if search unavailable."""
    if not has_api_key():
        return "", []

    try:
        text, citations = await web_search_query(
            _search_prompt(diagnosis, location, treatment_evidence)
        )
        if text.strip():
            logger.info(
                "clinic web search: %d chars, %d citations (%s, %s)",
                len(text),
                len(citations),
                location.city,
                location.state,
            )
            return text, citations
    except Exception as exc:
        logger.warning("clinic web search failed: %s", exc)

    return "", []
