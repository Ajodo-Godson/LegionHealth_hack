from typing import Literal, Optional

from pydantic import BaseModel, Field


class CharterPriority(BaseModel):
    rank: int = Field(..., ge=1, le=3)
    statement: str


class Charter(BaseModel):
    priorities: list[CharterPriority]


class PatientRecords(BaseModel):
    """Optional structured summary — personalizes research, does not diagnose."""

    severity: Optional[str] = None
    comorbidities: Optional[list[str]] = None
    prior_treatments: Optional[list[str]] = None


class RunRequest(BaseModel):
    diagnosis: str
    charter: Charter
    records: Optional[PatientRecords] = None


class RunResponse(BaseModel):
    run_id: str


class AgentLogEntry(BaseModel):
    agent: str
    action: str
    input: Optional[str] = None
    output: str
    timestamp: str


class CharterCheck(BaseModel):
    item: str
    status: Literal["aligned", "flagged", "excluded"]
    priority_ref: int
    message: str


class RecommendedProvider(BaseModel):
    name: str
    address: str
    phone: str


class ContradictionFound(BaseModel):
    detected: bool = False
    insurer_claim: str = ""
    provider_claim: str = ""
    clinic_id: str = ""
    clinic_name: str = ""
    message: str = ""


class Plan(BaseModel):
    recommended_provider: RecommendedProvider
    wait_time: str
    est_cost: str
    coverage_status: str
    eligible_trials: Optional[list[str]] = None
    next_action: str
    charter_checks: list[CharterCheck]
    personalized: bool = False
    contradiction_found: Optional[ContradictionFound] = None
    rerouted_to: Optional[str] = None
    verification_trace: list[str] = Field(default_factory=list)


class VoiceConsentBody(BaseModel):
    granted: bool
    use_twilio: bool = False


class HealthResponse(BaseModel):
    status: str = "ok"
    llm_enabled: bool = False
    mode: str = "stub"
    backend_dir: str = ""
    twilio_enabled: bool = False
