from __future__ import annotations

from collections import Counter

from .models import (
    BenchmarkObservation,
    BenchmarkPack,
    BenchmarkReference,
    ClauseFact,
    PlaybookDecision,
    PlaybookRuleResult,
    PolicyPack,
    RiskFlag,
)

SPELLBOOK_OVERVIEW_URL = "https://www.spellbook.legal/blog/benchmarks"
SPELLBOOK_HELP_URL = "https://help.spellbook.legal/en/articles/9160166-how-to-review-documents-with-benchmarks"
TERMSCOUT_BLOG_URL = "https://blog.termscout.com/benchmarking-what-top-vendors-get-right"
TERMSCOUT_OVERVIEW_URL = "https://www.termscout.com/"
JURO_REVIEW_URL = "https://juro.com/ai-contract-review"
JURO_CONDITIONAL_LOGIC_URL = "https://juro.com/learn/automated-contract-playbook-dynamic-templates"


def benchmark_references() -> list[BenchmarkReference]:
    return [
        BenchmarkReference(
            reference_id="spellbook_overview",
            label="Spellbook Benchmarks overview",
            url=SPELLBOOK_OVERVIEW_URL,
            note="Public description of at-a-glance market or custom-standard checks.",
        ),
        BenchmarkReference(
            reference_id="spellbook_help",
            label="Spellbook Benchmarks FAQ",
            url=SPELLBOOK_HELP_URL,
            note="Public description of standards, pass/fail coverage rules, and coverage scoring.",
        ),
        BenchmarkReference(
            reference_id="termscout_benchmarking",
            label="TermScout benchmarking overview",
            url=TERMSCOUT_BLOG_URL,
            note="Public description of benchmark analysis using 800+ data points from thousands of contracts.",
        ),
        BenchmarkReference(
            reference_id="termscout_market",
            label="TermScout market benchmarking overview",
            url=TERMSCOUT_OVERVIEW_URL,
            note="Public positioning around real-world market standards, contract Signals, and certification.",
        ),
        BenchmarkReference(
            reference_id="juro_playbook",
            label="Juro AI contract review",
            url=JURO_REVIEW_URL,
            note="Public description of reviewing and redlining third-party paper against playbooks.",
        ),
        BenchmarkReference(
            reference_id="juro_conditional_logic",
            label="Juro conditional logic for contract playbooks",
            url=JURO_CONDITIONAL_LOGIC_URL,
            note="Public description of automating clauses, fallback positions, and workflow rules.",
        ),
        BenchmarkReference(
            reference_id="house_playbook",
            label="House inbound playbook v1 (illustrative)",
            url=None,
            note="Local benchmark and playbook pack used by this prototype. Replace with your negotiated standards in production.",
        ),
    ]


DEFAULT_TARGET_CLAUSES = [
    "term",
    "renewal",
    "pricing",
    "payment",
    "sla",
    "termination",
    "liability",
    "governing_law",
    "data_processing",
]


CONTRACT_TYPE_TARGETS = {
    "NDA": ["term", "termination", "liability", "governing_law"],
    "SOW": ["term", "pricing", "payment", "termination", "liability", "governing_law"],
}


def _clean_law(value: str | None) -> str:
    return " ".join((value or "").lower().replace("&", "and").split())


def _allowed_laws(policy_pack: PolicyPack) -> set[str]:
    return {_clean_law(value) for value in policy_pack.allowed_governing_laws}


def _target_clauses(contract_type: str) -> list[str]:
    return CONTRACT_TYPE_TARGETS.get(contract_type, DEFAULT_TARGET_CLAUSES)


def _missing_observation(
    clause_type: str,
    label: str,
    market_standard: str,
    reasoning: str,
    *,
    score: int = 45,
    fallback_position: str | None = None,
    benchmark_reference_id: str = "spellbook_help",
) -> BenchmarkObservation:
    return BenchmarkObservation(
        clause_type=clause_type,
        label=label,
        contract_value="Not extracted",
        market_standard=market_standard,
        coverage_status="missing",
        market_alignment="missing",
        playbook_outcome="watch" if score >= 50 else "fail",
        score=score,
        reasoning=reasoning,
        fallback_position=fallback_position,
        citations=[],
        benchmark_reference_id=benchmark_reference_id,
    )


def evaluate_term(clause: ClauseFact | None) -> BenchmarkObservation:
    market_standard = "Routine inbound commercial paper commonly uses a 12–24 month initial term."
    fallback = "Set the initial term to 12 months, with renewal handled in a separate renewal clause."
    if clause is None:
        return _missing_observation(
            "term",
            "Term",
            market_standard,
            "The benchmark pack expects a clear initial term so renewal, pricing, and expiry logic can be reviewed consistently.",
            score=40,
            fallback_position=fallback,
        )
    months = clause.normalized.get("term_months")
    if months is None:
        return BenchmarkObservation(
            clause_type="term",
            label="Term",
            contract_value=clause.display_value,
            market_standard=market_standard,
            coverage_status="partial",
            market_alignment="near_market",
            playbook_outcome="watch",
            score=62,
            reasoning="A term clause was found, but the duration could not be normalized cleanly from the extracted text.",
            fallback_position=fallback,
            citations=clause.citations,
            benchmark_reference_id="spellbook_help",
        )
    if months <= 24:
        alignment, outcome, score = "within_market", "pass", 90
        reasoning = f"The extracted {months}-month initial term sits inside the illustrative 12–24 month market band."
    elif months <= 36:
        alignment, outcome, score = "near_market", "watch", 72
        reasoning = f"The extracted {months}-month term is longer than the preferred band but still common enough to stay in the watch lane."
    else:
        alignment, outcome, score = "outside_market", "fail", 48
        reasoning = f"The extracted {months}-month term is materially longer than the default benchmark pack expects for routine inbound contracts."
    return BenchmarkObservation(
        clause_type="term",
        label="Term",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="termscout_market",
    )


def evaluate_renewal(clause: ClauseFact | None, policy_pack: PolicyPack) -> BenchmarkObservation:
    market_standard = "If auto-renewal is used, 60–90 days of opt-out notice is a common baseline; shorter windows should be watched."
    fallback = (
        f"Either party may elect non-renewal by giving at least {policy_pack.min_renewal_notice_days} days' written notice before the end of the then-current term."
    )
    if clause is None:
        return _missing_observation(
            "renewal",
            "Renewal",
            market_standard,
            "No renewal mechanics were extracted. For one-time paper this may be acceptable, but recurring service agreements usually define renewal behavior explicitly.",
            score=62,
            fallback_position=fallback,
        )
    auto_renews = bool(clause.normalized.get("auto_renews"))
    notice_days = clause.normalized.get("notice_days")
    if not auto_renews:
        alignment, outcome, score = "within_market", "pass", 85
        reasoning = "The clause does not appear to impose evergreen renewal, which keeps it inside the default playbook guardrails."
    elif notice_days is not None and notice_days >= policy_pack.min_renewal_notice_days:
        alignment, outcome, score = "within_market", "pass", 89
        reasoning = f"The clause auto-renews but preserves a {notice_days}-day notice window, which matches the configured playbook threshold."
    elif notice_days is not None and notice_days >= 60:
        alignment, outcome, score = "near_market", "watch", 72
        reasoning = f"The clause auto-renews with only {notice_days} days' notice, which is workable but shorter than the configured benchmark."
    else:
        alignment, outcome, score = "outside_market", "fail", 46
        reasoning = "The clause uses auto-renewal without a robust opt-out window, which falls outside the simplified inbound playbook."
    return BenchmarkObservation(
        clause_type="renewal",
        label="Renewal",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="termscout_market",
    )


def evaluate_pricing(clause: ClauseFact | None, policy_pack: PolicyPack) -> BenchmarkObservation:
    market_standard = (
        f"Routine renewal pricing is often fixed during the initial term and then capped at CPI or about {policy_pack.preferred_renewal_increase_cap_pct:g}% annually."
    )
    fallback = (
        f"Renewal fee increases may not exceed the lesser of CPI and {policy_pack.preferred_renewal_increase_cap_pct:g}% in any 12-month period."
    )
    if clause is None:
        return _missing_observation(
            "pricing",
            "Pricing",
            market_standard,
            "The benchmark pack expects the commercial paper to state whether pricing is fixed initially and how renewal uplifts work.",
            score=55,
            fallback_position=fallback,
        )
    fixed_initial = bool(clause.normalized.get("fixed_initial_term"))
    cap_pct = clause.normalized.get("renewal_increase_cap_pct")
    cpi_linked = bool(clause.normalized.get("cpi_linked"))
    if fixed_initial and (cap_pct is None or cap_pct <= policy_pack.preferred_renewal_increase_cap_pct):
        alignment, outcome, score = "within_market", "pass", 88
        reasoning = "The extracted pricing language preserves initial-term stability and keeps renewal uplift inside the preferred benchmark band."
    elif cap_pct is not None and cap_pct <= policy_pack.preferred_renewal_increase_cap_pct + 2:
        alignment, outcome, score = "near_market", "watch", 72
        reasoning = f"The clause caps uplift at {cap_pct:g}%, which is usable but looser than the preferred pricing guardrail."
    elif cpi_linked and cap_pct is None:
        alignment, outcome, score = "near_market", "watch", 68
        reasoning = "The clause ties increases to CPI but does not state a numeric ceiling, so the benchmark pack keeps it in the watch lane."
    else:
        alignment, outcome, score = "outside_market", "fail", 48
        reasoning = "The pricing clause lacks a tight enough renewal cap or initial-term stability for the simplified inbound playbook."
    return BenchmarkObservation(
        clause_type="pricing",
        label="Pricing",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="termscout_benchmarking",
    )


def evaluate_payment(clause: ClauseFact | None, policy_pack: PolicyPack) -> BenchmarkObservation:
    market_standard = f"The house benchmark prefers {policy_pack.preferred_payment_days}-day payment cycles and watches anything longer than {policy_pack.max_payment_days} days."
    fallback = f"Customer will pay undisputed invoices within {policy_pack.preferred_payment_days} days of receipt."
    if clause is None:
        return _missing_observation(
            "payment",
            "Payment",
            market_standard,
            "A benchmark comparison works best when invoice timing is explicit in the contract.",
            score=50,
            fallback_position=fallback,
        )
    payment_days = clause.normalized.get("payment_days")
    if payment_days is None:
        return BenchmarkObservation(
            clause_type="payment",
            label="Payment",
            contract_value=clause.display_value,
            market_standard=market_standard,
            coverage_status="partial",
            market_alignment="near_market",
            playbook_outcome="watch",
            score=60,
            reasoning="Payment language was found, but the due-date window could not be normalized to a day count.",
            fallback_position=fallback,
            citations=clause.citations,
            benchmark_reference_id="termscout_benchmarking",
        )
    if payment_days <= policy_pack.preferred_payment_days:
        alignment, outcome, score = "within_market", "pass", 92
        reasoning = f"The extracted {payment_days}-day payment term sits at or inside the preferred benchmark threshold."
    elif payment_days <= policy_pack.max_payment_days:
        alignment, outcome, score = "near_market", "watch", 72
        reasoning = f"The extracted {payment_days}-day payment term is workable but longer than the preferred benchmark."
    else:
        alignment, outcome, score = "outside_market", "fail", 45
        reasoning = f"The extracted {payment_days}-day payment term sits outside the configured benchmark pack."
    return BenchmarkObservation(
        clause_type="payment",
        label="Payment",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="termscout_market",
    )


def evaluate_sla(clause: ClauseFact | None, policy_pack: PolicyPack) -> BenchmarkObservation:
    market_standard = "Managed service agreements often pair 99.9% availability with a service credit remedy for misses."
    fallback = "If availability falls below the SLA in a month, Customer will receive service credits under the applicable service credit schedule."
    if clause is None:
        return _missing_observation(
            "sla",
            "SLA",
            market_standard,
            "No service-level clause was extracted. For hosted services this is usually a coverage gap; for non-service paper it may be less relevant.",
            score=55,
            fallback_position=fallback,
        )
    uptime_pct = clause.normalized.get("uptime_pct")
    credits = clause.normalized.get("service_credits")
    if uptime_pct is not None and uptime_pct >= policy_pack.min_sla_uptime_pct and credits is True:
        alignment, outcome, score = "within_market", "pass", 92
        reasoning = f"The clause commits to {uptime_pct:g}% uptime and includes service credits, which matches the default benchmark pack."
    elif uptime_pct is not None and uptime_pct >= policy_pack.min_sla_uptime_pct:
        alignment, outcome, score = "near_market", "watch", 70
        reasoning = f"The clause commits to {uptime_pct:g}% uptime, but the extracted text does not include the preferred credit remedy."
    elif uptime_pct is not None and uptime_pct >= policy_pack.min_sla_uptime_pct - 0.4:
        alignment, outcome, score = "near_market", "watch", 66
        reasoning = f"The clause is close to the preferred uptime threshold at {uptime_pct:g}%, but still below the configured benchmark or missing credits."
    else:
        alignment, outcome, score = "outside_market", "fail", 42
        reasoning = "The SLA sits outside the simplified inbound benchmark band because uptime is too low or remedies are missing."
    return BenchmarkObservation(
        clause_type="sla",
        label="SLA",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="termscout_market",
    )


def evaluate_termination(clause: ClauseFact | None) -> BenchmarkObservation:
    market_standard = "Routine commercial paper often uses a 30-day cure period for material breach termination."
    fallback = "Either party may terminate for material breach if the breach remains uncured for 30 days after written notice."
    if clause is None:
        return _missing_observation(
            "termination",
            "Termination",
            market_standard,
            "A breach-and-cure mechanism is commonly included in inbound services paper so the playbook can route operational escalations cleanly.",
            score=55,
            fallback_position=fallback,
        )
    cure_days = clause.normalized.get("cure_period_days")
    if cure_days is not None and cure_days <= 30:
        alignment, outcome, score = "within_market", "pass", 86
        reasoning = f"The extracted {cure_days}-day cure period matches the benchmark pack's preferred termination language."
    elif cure_days is not None and cure_days <= 45:
        alignment, outcome, score = "near_market", "watch", 72
        reasoning = f"The extracted {cure_days}-day cure period is usable but looser than the preferred playbook position."
    else:
        alignment, outcome, score = "outside_market", "watch", 58
        reasoning = "Termination language was detected, but the breach cure mechanics are looser than the simplified playbook prefers or were not fully normalized."
    return BenchmarkObservation(
        clause_type="termination",
        label="Termination",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="termscout_benchmarking",
    )


def evaluate_liability(clause: ClauseFact | None) -> BenchmarkObservation:
    market_standard = "A fees-paid cap with a 12-month lookback is a common baseline starting point in routine commercial agreements."
    fallback = (
        "Except for the standard carve-outs, each party's aggregate liability under this Agreement will not exceed the fees paid or payable in the 12 months preceding the claim."
    )
    if clause is None:
        return _missing_observation(
            "liability",
            "Liability",
            market_standard,
            "The benchmark pack expects a limitation-of-liability clause so simple inbound deals do not move forward with uncapped exposure by omission.",
            score=35,
            fallback_position=fallback,
        )
    capped = bool(clause.normalized.get("capped"))
    lookback = clause.normalized.get("lookback_months")
    if capped and (lookback is None or lookback <= 12):
        alignment, outcome, score = "within_market", "pass", 88
        reasoning = "The extracted liability cap tracks the common fees-paid baseline with a 12-month-or-shorter lookback."
    elif capped and lookback <= 24:
        alignment, outcome, score = "near_market", "watch", 74
        reasoning = f"The extracted liability cap uses a {lookback}-month lookback, which is workable but broader than the preferred playbook baseline."
    elif capped:
        alignment, outcome, score = "near_market", "watch", 68
        reasoning = "A liability cap exists, but its structure is looser or less clearly bounded than the preferred benchmark pack."
    else:
        alignment, outcome, score = "outside_market", "fail", 40
        reasoning = "The extracted clause appears uncapped or unlimited, which falls outside the simplified inbound playbook."
    return BenchmarkObservation(
        clause_type="liability",
        label="Liability",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="termscout_market",
    )


def evaluate_governing_law(clause: ClauseFact | None, policy_pack: PolicyPack) -> BenchmarkObservation:
    allowed = ", ".join(policy_pack.allowed_governing_laws)
    market_standard = f"The simplified playbook prefers a pre-approved governing law list: {allowed}."
    fallback = f"This Agreement is governed by the laws of {policy_pack.allowed_governing_laws[0]}, without regard to conflict-of-law rules."
    if clause is None:
        return _missing_observation(
            "governing_law",
            "Governing law",
            market_standard,
            "No governing-law clause was extracted, which leaves routing decisions incomplete for simple inbound automation.",
            score=55,
            fallback_position=fallback,
        )
    jurisdiction = clause.normalized.get("jurisdiction", clause.display_value)
    if _clean_law(jurisdiction) in _allowed_laws(policy_pack):
        alignment, outcome, score = "within_market", "pass", 86
        reasoning = f"The extracted governing law ({jurisdiction}) is on the pre-approved list for simplified inbound review."
    else:
        alignment, outcome, score = "outside_market", "fail", 52
        reasoning = f"The extracted governing law ({jurisdiction}) is outside the pre-approved list, so the contract should not auto-approve."
    return BenchmarkObservation(
        clause_type="governing_law",
        label="Governing law",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="house_playbook",
    )


def evaluate_data_processing(clause: ClauseFact | None) -> BenchmarkObservation:
    market_standard = "If the contract involves customer or personal data, the benchmark pack expects a DPA or data-processing addendum reference."
    fallback = "Before Provider processes any customer personal data, the parties will execute the attached Data Processing Addendum."
    if clause is None:
        return BenchmarkObservation(
            clause_type="data_processing",
            label="Data processing",
            contract_value="No data-processing clause extracted",
            market_standard=market_standard,
            coverage_status="partial",
            market_alignment="not_applicable",
            playbook_outcome="watch",
            score=62,
            reasoning="No data-processing clause was extracted. This is acceptable only if the contract truly does not involve customer or personal data.",
            fallback_position=fallback,
            citations=[],
            benchmark_reference_id="spellbook_help",
        )
    handles_data = bool(clause.normalized.get("handles_customer_data"))
    dpa_present = bool(clause.normalized.get("dpa_present"))
    if handles_data and dpa_present:
        alignment, outcome, score = "within_market", "pass", 90
        reasoning = "The extracted contract appears to handle customer data and also includes DPA or addendum language, keeping it inside the playbook."
    elif handles_data:
        alignment, outcome, score = "outside_market", "fail", 30
        reasoning = "The contract appears to handle customer data, but the extracted text does not include DPA or data-processing addendum language."
    else:
        alignment, outcome, score = "not_applicable", "pass", 82
        reasoning = "The extracted text does not clearly show customer-data handling, so the DPA benchmark is treated as not applicable."
    return BenchmarkObservation(
        clause_type="data_processing",
        label="Data processing",
        contract_value=clause.display_value,
        market_standard=market_standard,
        coverage_status="covered" if handles_data or dpa_present else "partial",
        market_alignment=alignment,
        playbook_outcome=outcome,
        score=score,
        reasoning=reasoning,
        fallback_position=fallback if outcome != "pass" else None,
        citations=clause.citations,
        benchmark_reference_id="house_playbook",
    )


EVALUATORS = {
    "term": evaluate_term,
    "renewal": evaluate_renewal,
    "pricing": evaluate_pricing,
    "payment": evaluate_payment,
    "sla": evaluate_sla,
    "termination": evaluate_termination,
    "liability": evaluate_liability,
    "governing_law": evaluate_governing_law,
    "data_processing": evaluate_data_processing,
}


def build_benchmark_pack(contract_type: str, clauses: list[ClauseFact], policy_pack: PolicyPack) -> BenchmarkPack:
    clause_map = {clause.clause_type: clause for clause in clauses}
    items: list[BenchmarkObservation] = []
    for clause_type in _target_clauses(contract_type):
        clause = clause_map.get(clause_type)
        evaluator = EVALUATORS[clause_type]
        if clause_type in {"renewal", "pricing", "payment", "sla", "governing_law"}:
            item = evaluator(clause, policy_pack)  # type: ignore[arg-type]
        else:
            item = evaluator(clause)  # type: ignore[misc]
        items.append(item)

    if items:
        covered_points = 0.0
        for item in items:
            if item.coverage_status == "covered":
                covered_points += 1.0
            elif item.coverage_status == "partial":
                covered_points += 0.5
        coverage_score_pct = round(100 * covered_points / len(items))
        playbook_fit_score = round(sum(item.score for item in items) / len(items))
    else:
        coverage_score_pct = 0
        playbook_fit_score = 0

    counts_counter = Counter(item.playbook_outcome for item in items)
    counts = {
        "pass": counts_counter.get("pass", 0),
        "watch": counts_counter.get("watch", 0),
        "fail": counts_counter.get("fail", 0),
    }

    notes = [
        "This prototype uses an illustrative local benchmark pack inspired by public product descriptions, not proprietary vendor datasets.",
        "Coverage score mirrors Spellbook-style term coverage; playbook fit score mirrors a simplified TermScout-style favorability or fit summary.",
    ]
    if counts["fail"]:
        notes.append("At least one clause falls outside the default market/playbook range and should not be auto-approved without revision.")
    elif counts["watch"]:
        notes.append("The contract is broadly usable, but some clauses sit in a watch band and may need fallback language.")
    else:
        notes.append("All benchmarked clauses sit inside the default illustrative benchmark band.")

    return BenchmarkPack(
        pack_name="Inbound commercial benchmark pack (illustrative)",
        contract_segment=contract_type or "Contract",
        coverage_score_pct=coverage_score_pct,
        playbook_fit_score=playbook_fit_score,
        counts=counts,
        items=items,
        notes=notes,
        references=benchmark_references(),
    )


OWNER_BY_CLAUSE = {
    "renewal": "business",
    "pricing": "procurement",
    "payment": "finance",
    "sla": "operations",
    "data_processing": "privacy",
}


RULE_TITLE_BY_CLAUSE = {
    "renewal": "Renewal guardrail",
    "pricing": "Pricing guardrail",
    "payment": "Payment guardrail",
    "sla": "SLA guardrail",
    "termination": "Termination guardrail",
    "liability": "Liability guardrail",
    "governing_law": "Governing law guardrail",
    "data_processing": "Data handling guardrail",
    "term": "Term guardrail",
}


def build_playbook_decision(
    doc_meta: dict,
    benchmark_pack: BenchmarkPack,
    risks: list[RiskFlag],
    clauses: list[ClauseFact],
    policy_pack: PolicyPack,
) -> PlaybookDecision:
    high_risks = sum(1 for risk in risks if risk.severity == "high")
    medium_risks = sum(1 for risk in risks if risk.severity == "medium")
    fail_count = benchmark_pack.counts.get("fail", 0)
    watch_count = benchmark_pack.counts.get("watch", 0)
    contract_type = doc_meta.get("contract_type", "Contract")
    page_count = int(doc_meta.get("page_count") or 0)
    section_count = int(doc_meta.get("section_count") or 0)

    complexity = 0
    if contract_type == "MSA":
        complexity += 1
    if page_count > 8:
        complexity += 2
    if page_count > 15:
        complexity += 1
    if section_count > 12:
        complexity += 1
    if fail_count > 0:
        complexity += 1
    if high_risks > 0:
        complexity += 1
    if medium_risks > 2:
        complexity += 1

    if complexity <= 1:
        lane = "simple_inbound"
    elif complexity <= 3:
        lane = "standard_inbound"
    else:
        lane = "complex_review"

    rule_results: list[PlaybookRuleResult] = [
        PlaybookRuleResult(
            rule_id="lane.classification",
            title="Inbound lane classification",
            outcome="pass" if lane == "simple_inbound" else "watch" if lane == "standard_inbound" else "fail",
            owner="legal",
            explanation=(
                f"This contract was placed in the {lane.replace('_', ' ')} lane based on type ({contract_type}), length ({page_count} pages, {section_count} sections), and current risk/deviation levels."
            ),
        ),
        PlaybookRuleResult(
            rule_id="guardrail.risk_counts",
            title="Risk guardrail",
            outcome="pass" if high_risks == 0 and medium_risks <= policy_pack.max_auto_approve_medium_risks else "watch" if high_risks == 0 else "fail",
            owner="legal",
            explanation=(
                f"The current review shows {high_risks} high and {medium_risks} medium risks against an auto-approval limit of {policy_pack.max_auto_approve_medium_risks} medium risks."
            ),
        ),
    ]

    for item in benchmark_pack.items:
        rule_results.append(
            PlaybookRuleResult(
                rule_id=f"playbook.{item.clause_type}",
                title=RULE_TITLE_BY_CLAUSE.get(item.clause_type, item.label),
                outcome=item.playbook_outcome,
                owner=OWNER_BY_CLAUSE.get(item.clause_type, "legal"),
                explanation=item.reasoning,
                fallback_position=item.fallback_position,
                suggested_redline=item.fallback_position if item.playbook_outcome != "pass" else None,
                citations=item.citations,
            )
        )

    auto_approval_eligible = (
        policy_pack.auto_approve_simple_inbound
        and lane == "simple_inbound"
        and high_risks == 0
        and medium_risks <= policy_pack.max_auto_approve_medium_risks
        and fail_count == 0
        and watch_count <= policy_pack.max_auto_approve_watch_items
    )
    fallback_ready = all(
        result.fallback_position
        for result in rule_results
        if result.outcome in {"watch", "fail"} and result.rule_id.startswith("playbook.")
    )
    approved_if_using_fallbacks = (
        lane != "complex_review"
        and high_risks == 0
        and fail_count <= 2
        and fallback_ready
        and benchmark_pack.playbook_fit_score >= 60
    )

    score = max(0, min(100, benchmark_pack.playbook_fit_score - (high_risks * 12) - max(0, medium_risks - policy_pack.max_auto_approve_medium_risks) * 4))

    if auto_approval_eligible:
        recommended_route = "auto_approve"
        decision_summary = (
            "The contract sits in the simple inbound lane and clears the configured benchmark and risk guardrails, so it can move without legal touch."
        )
        next_steps = [
            "Route through the business self-serve workflow and capture metadata in the repository.",
            "Keep the extracted benchmark pack attached for auditability.",
        ]
    elif approved_if_using_fallbacks:
        recommended_route = "business_review"
        decision_summary = (
            "The contract does not qualify for straight auto-approval, but it can stay in the simplified inbound workflow if the listed fallback positions are sent first."
        )
        next_steps = [
            "Send the suggested fallback redlines to the counterparty.",
            "If the counterparty accepts the fallback language, the contract can be approved without full legal review.",
        ]
    else:
        recommended_route = "legal_review"
        decision_summary = (
            "The contract falls outside the simplified inbound playbook because the current mix of risks, benchmark deviations, or complexity needs legal review."
        )
        next_steps = [
            "Escalate to legal with the benchmark table and failed playbook checks attached.",
            "Focus review on the failed items first; they are the main blockers to automated routing.",
        ]

    return PlaybookDecision(
        contract_lane=lane,
        recommended_route=recommended_route,
        decision_summary=decision_summary,
        auto_approval_eligible=auto_approval_eligible,
        approved_if_using_fallbacks=approved_if_using_fallbacks,
        score=score,
        rule_results=rule_results,
        next_steps=next_steps,
    )
