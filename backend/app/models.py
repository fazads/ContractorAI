from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high"]
BenchmarkAlignment = Literal["within_market", "near_market", "outside_market", "missing", "not_applicable"]
CoverageStatus = Literal["covered", "partial", "missing"]
PlaybookOutcome = Literal["pass", "watch", "fail"]
PlaybookRoute = Literal["auto_approve", "business_review", "legal_review"]
PlaybookLane = Literal["simple_inbound", "standard_inbound", "complex_review"]


class Citation(BaseModel):
    chunk_id: str
    section: str
    page_start: int | None = None
    page_end: int | None = None
    excerpt: str | None = None


class SectionChunk(BaseModel):
    id: str
    heading: str
    page_start: int | None = None
    page_end: int | None = None
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClauseFact(BaseModel):
    clause_type: str
    label: str
    display_value: str
    normalized: dict[str, Any] = Field(default_factory=dict)
    raw_text: str = ""
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = 0.0
    status: str = "unreviewed"


class SummaryPack(BaseModel):
    executive_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    clause_pack: list[dict[str, Any]] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class RiskFlag(BaseModel):
    id: str
    severity: Severity
    title: str
    explanation: str
    recommended_action: str
    rule_id: str
    citations: list[Citation] = Field(default_factory=list)
    status: str = "open"


class AnswerRecord(BaseModel):
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    abstained: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditEvent(BaseModel):
    agent: str
    action: str
    status: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class BenchmarkReference(BaseModel):
    reference_id: str
    label: str
    url: str | None = None
    note: str | None = None


class BenchmarkObservation(BaseModel):
    clause_type: str
    label: str
    contract_value: str
    market_standard: str
    coverage_status: CoverageStatus = "covered"
    market_alignment: BenchmarkAlignment = "within_market"
    playbook_outcome: PlaybookOutcome = "watch"
    score: int = 0
    reasoning: str = ""
    fallback_position: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    benchmark_reference_id: str | None = None


class BenchmarkPack(BaseModel):
    pack_name: str = ""
    contract_segment: str = ""
    coverage_score_pct: int = 0
    playbook_fit_score: int = 0
    counts: dict[str, int] = Field(default_factory=dict)
    items: list[BenchmarkObservation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    references: list[BenchmarkReference] = Field(default_factory=list)


class PlaybookRuleResult(BaseModel):
    rule_id: str
    title: str
    outcome: PlaybookOutcome
    owner: str = "legal"
    explanation: str = ""
    fallback_position: str | None = None
    suggested_redline: str | None = None
    citations: list[Citation] = Field(default_factory=list)


class PlaybookDecision(BaseModel):
    contract_lane: PlaybookLane = "standard_inbound"
    recommended_route: PlaybookRoute = "legal_review"
    decision_summary: str = ""
    auto_approval_eligible: bool = False
    approved_if_using_fallbacks: bool = False
    score: int = 0
    rule_results: list[PlaybookRuleResult] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class PolicyPack(BaseModel):
    min_renewal_notice_days: int = 90
    max_payment_days: int = 60
    min_sla_uptime_pct: float = 99.9
    require_service_credits: bool = True
    require_liability_cap: bool = True
    requires_data_processing_terms: bool = True
    expiring_within_days: int = 120
    preferred_payment_days: int = 45
    preferred_renewal_increase_cap_pct: float = 5.0
    allowed_governing_laws: list[str] = Field(default_factory=lambda: ["New York", "Delaware", "California", "England and Wales"])
    auto_approve_simple_inbound: bool = True
    max_auto_approve_medium_risks: int = 1
    max_auto_approve_watch_items: int = 2


class ContractState(BaseModel):
    contract_id: str
    doc_meta: dict[str, Any] = Field(default_factory=dict)
    policy_pack: PolicyPack = Field(default_factory=PolicyPack)
    sections: list[SectionChunk] = Field(default_factory=list)
    clauses: list[ClauseFact] = Field(default_factory=list)
    obligations: list[dict[str, Any]] = Field(default_factory=list)
    summary: SummaryPack = Field(default_factory=SummaryPack)
    risks: list[RiskFlag] = Field(default_factory=list)
    benchmark_pack: BenchmarkPack = Field(default_factory=BenchmarkPack)
    playbook_decision: PlaybookDecision = Field(default_factory=PlaybookDecision)
    answers: list[AnswerRecord] = Field(default_factory=list)
    audit_trail: list[AuditEvent] = Field(default_factory=list)


class QuestionRequest(BaseModel):
    question: str


class ReassessRequest(BaseModel):
    policy_pack: PolicyPack


class TextAnalyzeRequest(BaseModel):
    text: str
    file_name: str = "pasted_contract.txt"
    policy_pack: PolicyPack = Field(default_factory=PolicyPack)


class AnalyzeResponse(BaseModel):
    contract: ContractState


class SampleContractResponse(BaseModel):
    file_name: str
    text: str
    policy_pack: PolicyPack = Field(default_factory=PolicyPack)
