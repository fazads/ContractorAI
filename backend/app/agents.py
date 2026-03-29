from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .benchmarking import build_benchmark_pack, build_playbook_decision
from .extractors import extract_contract_facts, make_citation
from .llm import OpenAIProvider
from .models import (
    AnswerRecord,
    AuditEvent,
    BenchmarkObservation,
    BenchmarkPack,
    ClauseFact,
    ContractState,
    PlaybookDecision,
    PlaybookRuleResult,
    PolicyPack,
    RiskFlag,
    SectionChunk,
    SummaryPack,
)
from .parsers import build_section_chunks, extract_text_pages_from_marked_text, infer_contract_type, parse_upload
from .retrieval import LocalRetriever


class BaseAgent:
    name = "base"

    def audit(self, action: str, details: dict | None = None, status: str = "completed") -> AuditEvent:
        now = datetime.now(timezone.utc)
        return AuditEvent(
            agent=self.name,
            action=action,
            status=status,
            started_at=now,
            completed_at=now,
            details=details or {},
        )


class IngestionAgent(BaseAgent):
    name = "ingestion"

    def run_from_upload(self, file_name: str, file_bytes: bytes) -> tuple[dict, list[SectionChunk], AuditEvent]:
        file_type, pages, notes = parse_upload(file_name, file_bytes)
        sections = build_section_chunks(pages)
        all_text = "\n\n".join(page.text for page in pages if page.text)
        doc_meta = {
            "file_name": file_name,
            "file_type": file_type,
            "page_count": len(pages),
            "section_count": len(sections),
            "contract_type": infer_contract_type(all_text, file_name),
            "notes": notes,
        }
        event = self.audit(
            "parse_document",
            {
                "file_type": file_type,
                "page_count": len(pages),
                "section_count": len(sections),
                "notes": notes,
            },
        )
        return doc_meta, sections, event

    def run_from_text(self, file_name: str, text: str) -> tuple[dict, list[SectionChunk], AuditEvent]:
        pages = extract_text_pages_from_marked_text(text)
        sections = build_section_chunks(pages)
        all_text = "\n\n".join(page.text for page in pages if page.text)
        doc_meta = {
            "file_name": file_name,
            "file_type": "text",
            "page_count": len(pages),
            "section_count": len(sections),
            "contract_type": infer_contract_type(all_text, file_name),
            "notes": {},
        }
        event = self.audit(
            "parse_document",
            {"file_type": "text", "page_count": len(pages), "section_count": len(sections)},
        )
        return doc_meta, sections, event


class ClauseExtractionAgent(BaseAgent):
    name = "clause_extraction"

    def run(self, sections: list[SectionChunk]) -> tuple[list[ClauseFact], list[dict], AuditEvent]:
        clauses, obligations = extract_contract_facts(sections)
        event = self.audit(
            "normalize_clauses",
            {"clause_count": len(clauses), "obligation_count": len(obligations)},
        )
        return clauses, obligations, event


class BenchmarkAgent(BaseAgent):
    name = "benchmarking"

    def run(self, contract_type: str, clauses: list[ClauseFact], policy_pack: PolicyPack) -> tuple[BenchmarkPack, AuditEvent]:
        benchmark_pack = build_benchmark_pack(contract_type, clauses, policy_pack)
        event = self.audit(
            "benchmark_contract",
            {
                "contract_type": contract_type,
                "coverage_score_pct": benchmark_pack.coverage_score_pct,
                "playbook_fit_score": benchmark_pack.playbook_fit_score,
                "fail_count": benchmark_pack.counts.get("fail", 0),
            },
        )
        return benchmark_pack, event


class PlaybookAutomationAgent(BaseAgent):
    name = "playbook_automation"

    def run(
        self,
        doc_meta: dict,
        benchmark_pack: BenchmarkPack,
        risks: list[RiskFlag],
        clauses: list[ClauseFact],
        policy_pack: PolicyPack,
    ) -> tuple[PlaybookDecision, AuditEvent]:
        decision = build_playbook_decision(doc_meta, benchmark_pack, risks, clauses, policy_pack)
        event = self.audit(
            "route_playbook",
            {
                "contract_lane": decision.contract_lane,
                "recommended_route": decision.recommended_route,
                "score": decision.score,
            },
        )
        return decision, event


class SummarizationAgent(BaseAgent):
    name = "summarization"

    def __init__(self, llm_provider: OpenAIProvider | None = None) -> None:
        self.llm_provider = llm_provider or OpenAIProvider()

    def run(
        self,
        contract_type: str,
        clauses: list[ClauseFact],
        risks: list[RiskFlag],
        benchmark_pack: BenchmarkPack | None = None,
        playbook_decision: PlaybookDecision | None = None,
    ) -> tuple[SummaryPack, AuditEvent]:
        clause_map = {clause.clause_type: clause for clause in clauses}
        clause_pack = []
        for key in ["term", "renewal", "pricing", "payment", "sla", "liability", "governing_law", "data_processing"]:
            clause = clause_map.get(key)
            if clause:
                clause_pack.append(
                    {
                        "label": clause.label,
                        "value": clause.display_value,
                        "citations": [citation.model_dump() for citation in clause.citations],
                        "confidence": clause.confidence,
                    }
                )
        high_risk = sum(1 for risk in risks if risk.severity == "high")
        medium_risk = sum(1 for risk in risks if risk.severity == "medium")
        executive_bits = [contract_type]
        if term := clause_map.get("term"):
            executive_bits.append(term.display_value)
        if renewal := clause_map.get("renewal"):
            executive_bits.append(renewal.display_value)
        if payment := clause_map.get("payment"):
            executive_bits.append(payment.display_value)
        executive_summary = "; ".join(executive_bits) + "."
        if risks:
            executive_summary += f" Current rule checks show {high_risk} high and {medium_risk} medium risk flags."
        if benchmark_pack and benchmark_pack.items:
            executive_summary += (
                f" Benchmark coverage is {benchmark_pack.coverage_score_pct}% with a playbook fit score of {benchmark_pack.playbook_fit_score}/100."
            )
        if playbook_decision and playbook_decision.decision_summary:
            executive_summary += f" Recommended route: {playbook_decision.recommended_route.replace('_', ' ')}."

        key_findings = []
        for clause_key in ["pricing", "sla", "liability", "data_processing", "governing_law"]:
            clause = clause_map.get(clause_key)
            if clause:
                key_findings.append(f"{clause.label}: {clause.display_value}.")
        for risk in risks[:3]:
            key_findings.append(f"{risk.severity.title()} risk: {risk.title}.")
        if benchmark_pack and benchmark_pack.counts:
            key_findings.append(
                f"Benchmark pack: {benchmark_pack.counts.get('pass', 0)} pass, {benchmark_pack.counts.get('watch', 0)} watch, {benchmark_pack.counts.get('fail', 0)} fail."
            )
        if playbook_decision:
            key_findings.append(
                f"Playbook route: {playbook_decision.recommended_route.replace('_', ' ')} from the {playbook_decision.contract_lane.replace('_', ' ')} lane."
            )

        open_questions = []
        for missing in ["liability", "governing_law", "data_processing"]:
            if missing not in clause_map:
                label = missing.replace("_", " ").title()
                open_questions.append(f"Confirm whether a {label} clause exists in attachments or schedules.")
        if benchmark_pack:
            for item in benchmark_pack.items:
                if item.playbook_outcome == "fail":
                    open_questions.append(f"Resolve benchmark gap: {item.label.lower()} — {item.reasoning}")

        if self.llm_provider.available:
            payload = {
                "contract_type": contract_type,
                "clauses": [{"type": c.clause_type, "value": c.display_value} for c in clauses],
                "risks": [{"severity": r.severity, "title": r.title} for r in risks],
                "benchmark_pack": {
                    "coverage_score_pct": benchmark_pack.coverage_score_pct if benchmark_pack else None,
                    "playbook_fit_score": benchmark_pack.playbook_fit_score if benchmark_pack else None,
                    "counts": benchmark_pack.counts if benchmark_pack else {},
                },
                "playbook_decision": {
                    "recommended_route": playbook_decision.recommended_route if playbook_decision else None,
                    "contract_lane": playbook_decision.contract_lane if playbook_decision else None,
                },
            }
            enriched = self.llm_provider.generate_json(
                instructions=(
                    "You are the summarization agent for a contract assistant. "
                    "Return strict JSON with keys executive_summary, key_findings, open_questions. "
                    "Use only the supplied facts. Keep it concise and executive-friendly."
                ),
                payload=payload,
            )
            if enriched:
                executive_summary = enriched.get("executive_summary", executive_summary)
                key_findings = enriched.get("key_findings", key_findings)
                open_questions = enriched.get("open_questions", open_questions)

        summary = SummaryPack(
            executive_summary=executive_summary,
            key_findings=key_findings,
            clause_pack=clause_pack,
            open_questions=open_questions,
        )
        event = self.audit("summarize_contract", {"key_findings": len(key_findings)})
        return summary, event


class RiskComplianceAgent(BaseAgent):
    name = "risk_compliance"

    def run(self, clauses: list[ClauseFact], policy_pack: PolicyPack) -> tuple[list[RiskFlag], AuditEvent]:
        clause_map = {clause.clause_type: clause for clause in clauses}
        risks: list[RiskFlag] = []

        renewal = clause_map.get("renewal")
        if renewal and renewal.normalized.get("auto_renews"):
            notice_days = renewal.normalized.get("notice_days")
            if notice_days is not None and notice_days < policy_pack.min_renewal_notice_days:
                risks.append(
                    RiskFlag(
                        id=f"risk-{len(risks)+1:03d}",
                        severity="medium",
                        title="Short renewal notice window",
                        explanation=(
                            f"The contract auto-renews and only allows {notice_days} days of notice, below the configured threshold of {policy_pack.min_renewal_notice_days} days."
                        ),
                        recommended_action="Negotiate a longer notice window or create an operational reminder before the deadline.",
                        rule_id="renewal_notice_days",
                        citations=renewal.citations,
                    )
                )

        term = clause_map.get("term")
        if term and term.normalized.get("estimated_expiration_date"):
            expiration = datetime.fromisoformat(term.normalized["estimated_expiration_date"]).date()
            days_remaining = (expiration - datetime.now().date()).days
            if days_remaining <= policy_pack.expiring_within_days:
                severity = "high" if days_remaining <= 30 else "medium"
                risks.append(
                    RiskFlag(
                        id=f"risk-{len(risks)+1:03d}",
                        severity=severity,
                        title="Contract expiry approaching",
                        explanation=(
                            f"The estimated term end date is {expiration.isoformat()}, which is in {days_remaining} days and within the configured {policy_pack.expiring_within_days}-day watch window."
                        ),
                        recommended_action="Review renewal strategy and trigger internal renewal workflow.",
                        rule_id="expiring_within_window",
                        citations=term.citations,
                    )
                )

        payment = clause_map.get("payment")
        if payment and payment.normalized.get("payment_days") is not None:
            payment_days = payment.normalized["payment_days"]
            if payment_days > policy_pack.max_payment_days:
                severity = "medium" if payment_days > policy_pack.max_payment_days + 15 else "low"
                risks.append(
                    RiskFlag(
                        id=f"risk-{len(risks)+1:03d}",
                        severity=severity,
                        title="Long payment cycle",
                        explanation=(
                            f"The contract allows {payment_days} days to pay invoices, above the configured threshold of {policy_pack.max_payment_days} days."
                        ),
                        recommended_action="Assess cash-flow impact and consider shortening the invoice cycle.",
                        rule_id="payment_days_threshold",
                        citations=payment.citations,
                    )
                )

        sla = clause_map.get("sla")
        if sla:
            uptime_pct = sla.normalized.get("uptime_pct")
            if uptime_pct is not None and uptime_pct < policy_pack.min_sla_uptime_pct:
                risks.append(
                    RiskFlag(
                        id=f"risk-{len(risks)+1:03d}",
                        severity="medium",
                        title="SLA below policy threshold",
                        explanation=(
                            f"The SLA commits to {uptime_pct}% uptime, below the configured minimum of {policy_pack.min_sla_uptime_pct}%."
                        ),
                        recommended_action="Negotiate stronger uptime commitments or carve out credits for missed availability.",
                        rule_id="sla_uptime_threshold",
                        citations=sla.citations,
                    )
                )
            if policy_pack.require_service_credits and sla.normalized.get("service_credits") is False:
                risks.append(
                    RiskFlag(
                        id=f"risk-{len(risks)+1:03d}",
                        severity="medium",
                        title="Missing service credits",
                        explanation="The SLA includes uptime language but explicitly states that no service credits are provided for misses.",
                        recommended_action="Add a service credit schedule or escalation remedy for SLA failures.",
                        rule_id="missing_service_credits",
                        citations=sla.citations,
                    )
                )

        liability = clause_map.get("liability")
        if policy_pack.require_liability_cap:
            if liability is None:
                risks.append(
                    RiskFlag(
                        id=f"risk-{len(risks)+1:03d}",
                        severity="high",
                        title="Liability cap not detected",
                        explanation="No limitation-of-liability clause was extracted from the contract body.",
                        recommended_action="Confirm whether a liability cap exists in the core agreement, schedules, or order form.",
                        rule_id="liability_cap_missing",
                        citations=[],
                    )
                )
            elif not liability.normalized.get("capped", False):
                risks.append(
                    RiskFlag(
                        id=f"risk-{len(risks)+1:03d}",
                        severity="high",
                        title="Potential uncapped liability",
                        explanation="The liability language appears unlimited or uncapped under the configured policy.",
                        recommended_action="Introduce a balanced cap tied to fees, claim type, or carve-outs.",
                        rule_id="liability_uncapped",
                        citations=liability.citations,
                    )
                )

        data_processing = clause_map.get("data_processing")
        if policy_pack.requires_data_processing_terms and data_processing:
            if data_processing.normalized.get("handles_customer_data") and not data_processing.normalized.get("dpa_present"):
                risks.append(
                    RiskFlag(
                        id=f"risk-{len(risks)+1:03d}",
                        severity="high",
                        title="Data processing terms missing",
                        explanation=(
                            "The contract appears to involve customer data handling, but no DPA or data-processing addendum language was detected in the extracted sections."
                        ),
                        recommended_action="Attach or incorporate DPA language before signing for any customer-data-processing use case.",
                        rule_id="dpa_missing",
                        citations=data_processing.citations,
                    )
                )

        event = self.audit("evaluate_risks", {"risk_count": len(risks)})
        return risks, event


class QAAgent(BaseAgent):
    name = "qa"

    def __init__(self, llm_provider: OpenAIProvider | None = None) -> None:
        self.llm_provider = llm_provider or OpenAIProvider()

    def classify_question(self, question: str) -> str | None:
        lower = question.lower()
        mapping = {
            "renewal": ["renew", "notice", "auto-renew"],
            "term": ["term", "expire", "expiration", "effective date"],
            "pricing": ["price", "pricing", "cpi", "increase", "fee"],
            "payment": ["invoice", "payment", "net", "paid", "days"],
            "sla": ["sla", "service level", "uptime", "availability", "incident", "response time"],
            "liability": ["liability", "damages", "cap", "indemn"],
            "termination": ["terminate", "termination", "breach", "cure"],
            "governing_law": ["governing law", "jurisdiction", "venue", "law applies"],
            "data_processing": ["data", "privacy", "dpa", "processing", "personal data"],
        }
        for clause_type, hints in mapping.items():
            if any(hint in lower for hint in hints):
                return clause_type
        return None

    def is_benchmark_question(self, question: str) -> bool:
        lower = question.lower()
        return any(token in lower for token in ["benchmark", "market", "standard", "fit score", "favorable", "favorability"])

    def is_playbook_question(self, question: str) -> bool:
        lower = question.lower()
        return any(token in lower for token in ["playbook", "auto approve", "auto-approve", "route", "fallback", "redline", "escalate"])

    def answer_from_clause(self, clause: ClauseFact, question: str) -> AnswerRecord:
        clause_type = clause.clause_type
        normalized = clause.normalized
        answer = clause.display_value
        if clause_type == "renewal":
            answer = "This contract auto-renews" if normalized.get("auto_renews") else "I did not detect auto-renewal language."
            if normalized.get("renewal_term_months"):
                answer += f" for {normalized['renewal_term_months']}-month renewal terms"
            if normalized.get("notice_days"):
                answer += f", unless notice is given at least {normalized['notice_days']} days before term end."
            else:
                answer += "."
        elif clause_type == "term":
            answer = f"The extracted initial term is {normalized.get('term_months')} months"
            if normalized.get("effective_date"):
                answer += f" from {normalized['effective_date']}"
            if normalized.get("estimated_expiration_date"):
                answer += f", with an estimated term end date of {normalized['estimated_expiration_date']}"
            answer += "."
        elif clause_type == "pricing":
            answer = f"Pricing summary: {clause.display_value}."
        elif clause_type == "payment":
            answer = f"Payment terms: {clause.display_value}."
        elif clause_type == "sla":
            answer = f"Service level summary: {clause.display_value}."
        elif clause_type == "liability":
            answer = f"Liability summary: {clause.display_value}."
        elif clause_type == "termination":
            answer = f"Termination summary: {clause.display_value}."
        elif clause_type == "governing_law":
            answer = f"The governing law clause points to {normalized.get('jurisdiction', clause.display_value)}."
        elif clause_type == "data_processing":
            answer = f"Data processing summary: {clause.display_value}."
        return AnswerRecord(
            question=question,
            answer=answer,
            citations=clause.citations,
            evidence=[citation.excerpt or "" for citation in clause.citations if citation.excerpt],
            confidence=max(0.8, clause.confidence),
            abstained=False,
        )

    def _citations_from_rule_results(self, results: list[PlaybookRuleResult], limit: int = 5):
        citations = []
        for result in results:
            for citation in result.citations:
                citations.append(citation)
                if len(citations) >= limit:
                    return citations
        return citations

    def answer_from_benchmark_item(self, item: BenchmarkObservation, question: str) -> AnswerRecord:
        answer = (
            f"{item.label}: {item.contract_value}. Benchmark view: {item.market_alignment.replace('_', ' ')} with a {item.playbook_outcome} playbook outcome and score {item.score}/100. "
            f"Reference band: {item.market_standard} {item.reasoning}"
        )
        if item.fallback_position:
            answer += f" Fallback position: {item.fallback_position}"
        return AnswerRecord(
            question=question,
            answer=answer,
            citations=item.citations,
            evidence=[citation.excerpt or "" for citation in item.citations if citation.excerpt],
            confidence=0.87,
            abstained=False,
        )

    def answer_from_benchmark_pack(self, state: ContractState, question: str) -> AnswerRecord:
        benchmark_pack = state.benchmark_pack
        answer = (
            f"The contract's benchmark coverage is {benchmark_pack.coverage_score_pct}% and its playbook fit score is {benchmark_pack.playbook_fit_score}/100. "
            f"Current counts are {benchmark_pack.counts.get('pass', 0)} pass, {benchmark_pack.counts.get('watch', 0)} watch, and {benchmark_pack.counts.get('fail', 0)} fail."
        )
        if benchmark_pack.notes:
            answer += f" {benchmark_pack.notes[0]}"
        citations = self._citations_from_rule_results(state.playbook_decision.rule_results)
        return AnswerRecord(
            question=question,
            answer=answer,
            citations=citations,
            evidence=[citation.excerpt or "" for citation in citations if citation.excerpt],
            confidence=0.82,
            abstained=False,
        )

    def answer_from_playbook(self, state: ContractState, question: str, clause_type: str | None = None) -> AnswerRecord:
        decision = state.playbook_decision
        if clause_type:
            relevant = [result for result in decision.rule_results if result.rule_id == f"playbook.{clause_type}"]
            if relevant:
                result = relevant[0]
                answer = f"Playbook check for {result.title.lower()}: {result.explanation} Outcome: {result.outcome}."
                if result.suggested_redline:
                    answer += f" Suggested fallback: {result.suggested_redline}"
                citations = result.citations
                return AnswerRecord(
                    question=question,
                    answer=answer,
                    citations=citations,
                    evidence=[citation.excerpt or "" for citation in citations if citation.excerpt],
                    confidence=0.84,
                    abstained=False,
                )

        answer = (
            f"The recommended playbook route is {decision.recommended_route.replace('_', ' ')} from the {decision.contract_lane.replace('_', ' ')} lane. "
            f"{decision.decision_summary} Playbook score: {decision.score}/100."
        )
        if decision.approved_if_using_fallbacks and not decision.auto_approval_eligible:
            answer += " The contract can stay in the simplified workflow if the listed fallback positions are accepted."
        citations = self._citations_from_rule_results(decision.rule_results)
        return AnswerRecord(
            question=question,
            answer=answer,
            citations=citations,
            evidence=[citation.excerpt or "" for citation in citations if citation.excerpt],
            confidence=0.84,
            abstained=False,
        )

    def answer(self, question: str, state: ContractState, retriever: LocalRetriever) -> tuple[AnswerRecord, AuditEvent]:
        clause_map = {clause.clause_type: clause for clause in state.clauses}
        clause_type = self.classify_question(question)

        if self.is_playbook_question(question) and state.playbook_decision.rule_results:
            record = self.answer_from_playbook(state, question, clause_type=clause_type)
            event = self.audit("answer_question", {"mode": "playbook", "question": question})
            return record, event

        if self.is_benchmark_question(question) and state.benchmark_pack.items:
            if clause_type:
                item = next((item for item in state.benchmark_pack.items if item.clause_type == clause_type), None)
                if item:
                    record = self.answer_from_benchmark_item(item, question)
                    event = self.audit("answer_question", {"mode": "benchmark_clause", "question": question})
                    return record, event
            record = self.answer_from_benchmark_pack(state, question)
            event = self.audit("answer_question", {"mode": "benchmark_overview", "question": question})
            return record, event

        if clause_type and clause_type in clause_map:
            record = self.answer_from_clause(clause_map[clause_type], question)
            event = self.audit("answer_question", {"mode": "normalized_clause", "question": question})
            return record, event

        results = retriever.search(question, top_k=3)
        if self.llm_provider.available and results:
            payload = {
                "question": question,
                "evidence": [
                    {
                        "section": result.chunk.heading,
                        "pages": [result.chunk.page_start, result.chunk.page_end],
                        "text": result.chunk.text,
                    }
                    for result in results
                ],
            }
            structured = self.llm_provider.generate_json(
                instructions=(
                    "You are the Q&A agent for a contract assistant. "
                    "Answer only from the supplied evidence. If the evidence is insufficient, return JSON with answer saying you cannot confirm from the evidence and abstained true. "
                    "Return strict JSON with keys answer, confidence, abstained."
                ),
                payload=payload,
            )
            if structured:
                citations = [make_citation(result.chunk) for result in results]
                record = AnswerRecord(
                    question=question,
                    answer=structured.get("answer", "I could not answer from the supplied evidence."),
                    citations=citations,
                    evidence=[citation.excerpt or "" for citation in citations],
                    confidence=float(structured.get("confidence", 0.6)),
                    abstained=bool(structured.get("abstained", False)),
                )
                event = self.audit("answer_question", {"mode": "llm_retrieval", "question": question})
                return record, event

        if results:
            top = results[0]
            answer = (
                "I could not map that question to a normalized clause yet. "
                f"The most relevant section is '{top.chunk.heading}' on page {top.chunk.page_start or '?'} and it says: {top.chunk.text[:260]}"
            )
            citations = [make_citation(result.chunk) for result in results]
            record = AnswerRecord(
                question=question,
                answer=answer,
                citations=citations,
                evidence=[citation.excerpt or "" for citation in citations],
                confidence=0.55,
                abstained=False,
            )
            event = self.audit("answer_question", {"mode": "retrieval_fallback", "question": question})
            return record, event

        record = AnswerRecord(
            question=question,
            answer="I could not find evidence for that question in the current contract text.",
            citations=[],
            evidence=[],
            confidence=0.1,
            abstained=True,
        )
        event = self.audit("answer_question", {"mode": "abstain", "question": question})
        return record, event


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    def __init__(self) -> None:
        self.llm_provider = OpenAIProvider()
        self.ingestion = IngestionAgent()
        self.extractor = ClauseExtractionAgent()
        self.risk = RiskComplianceAgent()
        self.benchmark = BenchmarkAgent()
        self.playbook = PlaybookAutomationAgent()
        self.summary = SummarizationAgent(self.llm_provider)
        self.qa = QAAgent(self.llm_provider)

    def _new_contract_id(self) -> str:
        return f"ctr-{uuid.uuid4().hex[:8]}"

    def analyze_upload(self, file_name: str, file_bytes: bytes, policy_pack: PolicyPack) -> tuple[ContractState, LocalRetriever]:
        doc_meta, sections, ingest_event = self.ingestion.run_from_upload(file_name, file_bytes)
        return self._finalize_analysis(doc_meta, sections, policy_pack, ingest_event)

    def analyze_text(self, file_name: str, text: str, policy_pack: PolicyPack) -> tuple[ContractState, LocalRetriever]:
        doc_meta, sections, ingest_event = self.ingestion.run_from_text(file_name, text)
        return self._finalize_analysis(doc_meta, sections, policy_pack, ingest_event)

    def _finalize_analysis(
        self,
        doc_meta: dict,
        sections: list[SectionChunk],
        policy_pack: PolicyPack,
        ingest_event: AuditEvent,
    ) -> tuple[ContractState, LocalRetriever]:
        clauses, obligations, extract_event = self.extractor.run(sections)
        risks, risk_event = self.risk.run(clauses, policy_pack)
        benchmark_pack, benchmark_event = self.benchmark.run(doc_meta.get("contract_type", "Contract"), clauses, policy_pack)
        playbook_decision, playbook_event = self.playbook.run(doc_meta, benchmark_pack, risks, clauses, policy_pack)
        summary, summary_event = self.summary.run(
            doc_meta.get("contract_type", "Contract"),
            clauses,
            risks,
            benchmark_pack,
            playbook_decision,
        )
        state = ContractState(
            contract_id=self._new_contract_id(),
            doc_meta=doc_meta,
            policy_pack=policy_pack,
            sections=sections,
            clauses=clauses,
            obligations=obligations,
            summary=summary,
            risks=risks,
            benchmark_pack=benchmark_pack,
            playbook_decision=playbook_decision,
            audit_trail=[
                self.audit("route_analysis", {"file_name": doc_meta.get("file_name")}),
                ingest_event,
                extract_event,
                risk_event,
                benchmark_event,
                playbook_event,
                summary_event,
            ],
        )
        retriever = LocalRetriever()
        retriever.fit(sections)
        return state, retriever

    def reassess(self, state: ContractState, policy_pack: PolicyPack) -> ContractState:
        risks, risk_event = self.risk.run(state.clauses, policy_pack)
        benchmark_pack, benchmark_event = self.benchmark.run(state.doc_meta.get("contract_type", "Contract"), state.clauses, policy_pack)
        playbook_decision, playbook_event = self.playbook.run(state.doc_meta, benchmark_pack, risks, state.clauses, policy_pack)
        summary, summary_event = self.summary.run(
            state.doc_meta.get("contract_type", "Contract"),
            state.clauses,
            risks,
            benchmark_pack,
            playbook_decision,
        )
        state.policy_pack = policy_pack
        state.risks = risks
        state.benchmark_pack = benchmark_pack
        state.playbook_decision = playbook_decision
        state.summary = summary
        state.audit_trail.extend([risk_event, benchmark_event, playbook_event, summary_event])
        return state

    def answer_question(self, state: ContractState, retriever: LocalRetriever, question: str) -> ContractState:
        answer, qa_event = self.qa.answer(question, state, retriever)
        state.answers.append(answer)
        state.audit_trail.append(qa_event)
        return state
