from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Iterable

from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

from .models import Citation, ClauseFact, SectionChunk

ONES = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
WORD_NUMBER_PATTERN = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|"
    r"sixty|seventy|eighty|ninety|hundred|and|-)+\b",
    re.IGNORECASE,
)


def words_to_int(phrase: str) -> int | None:
    tokens = [token for token in re.split(r"[\s-]+", phrase.lower()) if token]
    if not tokens:
        return None
    current = 0
    seen = False
    for token in tokens:
        if token == "and":
            continue
        if token in ONES:
            current += ONES[token]
            seen = True
        elif token in TENS:
            current += TENS[token]
            seen = True
        elif token == "hundred":
            current = max(current, 1) * 100
            seen = True
        else:
            return None
    return current if seen else None


def extract_number(text: str) -> int | None:
    if not text:
        return None
    paren_digit = re.search(r"\((\d+)\)", text)
    if paren_digit:
        return int(paren_digit.group(1))
    plain_digit = re.search(r"\b(\d+)\b", text)
    if plain_digit:
        return int(plain_digit.group(1))
    for match in WORD_NUMBER_PATTERN.finditer(text):
        value = words_to_int(match.group(0))
        if value is not None:
            return value
    return None


def extract_percentage(text: str) -> float | None:
    match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", text)
    return float(match.group(1)) if match else None


def parse_date(text: str) -> date | None:
    if not text:
        return None
    patterns = [
        r"\b[A-Z][a-z]+ \d{1,2}, \d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return date_parser.parse(match.group(0), fuzzy=True).date()
            except Exception:
                continue
    return None


def excerpt_around(text: str, start: int | None = None, end: int | None = None, width: int = 180) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return ""
    if start is None or end is None:
        return normalized[: width * 2] + ("…" if len(normalized) > width * 2 else "")
    s = max(0, start - width)
    e = min(len(normalized), end + width)
    prefix = "…" if s > 0 else ""
    suffix = "…" if e < len(normalized) else ""
    return prefix + normalized[s:e] + suffix


def make_citation(chunk: SectionChunk, excerpt: str | None = None) -> Citation:
    return Citation(
        chunk_id=chunk.id,
        section=chunk.heading,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        excerpt=excerpt or excerpt_around(chunk.text),
    )


def chunk_score(chunk: SectionChunk, keywords: Iterable[str]) -> int:
    haystack = f"{chunk.heading} {chunk.text}".lower()
    return sum(haystack.count(keyword.lower()) for keyword in keywords)


def ranked_chunks(chunks: list[SectionChunk], keywords: Iterable[str]) -> list[SectionChunk]:
    return sorted(chunks, key=lambda c: (chunk_score(c, keywords), -(c.page_start or 0)), reverse=True)


def find_match(chunks: list[SectionChunk], *, keywords: Iterable[str], patterns: Iterable[re.Pattern[str]]):
    for chunk in ranked_chunks(chunks, keywords):
        for pattern in patterns:
            match = pattern.search(chunk.text)
            if match:
                return chunk, match
    return None


def lookup_clause(clauses: list[ClauseFact], clause_type: str) -> ClauseFact | None:
    for clause in clauses:
        if clause.clause_type == clause_type:
            return clause
    return None


def extract_parties_and_effective_date(chunks: list[SectionChunk]) -> ClauseFact | None:
    intro_chunks = chunks[:2] if len(chunks) >= 2 else chunks
    combined_text = "\n".join(chunk.text for chunk in intro_chunks)
    party_match = re.search(
        r"between\s+(?P<party1>[^\n(]+?)\s*\([^\n)]*\)\s+and\s+(?P<party2>[^\n(]+?)\s*\([^\n)]*\)",
        combined_text,
        re.IGNORECASE,
    )
    effective = parse_date(combined_text)
    if not party_match and not effective:
        return None
    citations = [make_citation(intro_chunks[0])] if intro_chunks else []
    party1 = party_match.group("party1").strip(" ,") if party_match else None
    party2 = party_match.group("party2").strip(" ,") if party_match else None
    display_parts = [part for part in [party1, party2] if part]
    display = " – ".join(display_parts) if display_parts else "Parties detected"
    if effective:
        display += f" (effective {effective.isoformat()})"
    return ClauseFact(
        clause_type="parties",
        label="Parties",
        display_value=display,
        normalized={
            "party_1": party1,
            "party_2": party2,
            "effective_date": effective.isoformat() if effective else None,
        },
        raw_text=combined_text[:1500],
        citations=citations,
        confidence=0.88 if party_match and effective else 0.72,
    )


def extract_term_clause(chunks: list[SectionChunk], parties_clause: ClauseFact | None) -> ClauseFact | None:
    patterns = [
        re.compile(
            r"initial term[^.]{0,140}?(?P<phrase>(?:[A-Za-z-]+\s*)?\(\d+\)|\d+|[A-Za-z-]+)\s*(?P<unit>month|year)s?",
            re.IGNORECASE,
        ),
        re.compile(
            r"continue for[^.]{0,60}?(?P<phrase>(?:[A-Za-z-]+\s*)?\(\d+\)|\d+|[A-Za-z-]+)\s*(?P<unit>month|year)s?",
            re.IGNORECASE,
        ),
    ]
    result = find_match(chunks, keywords=["term", "effective date", "renew"], patterns=patterns)
    if not result:
        return None
    chunk, match = result
    number = extract_number(match.group("phrase"))
    unit = match.group("unit").lower()
    if not number:
        return None
    term_months = number * 12 if unit == "year" else number
    effective_date = None
    if parties_clause and parties_clause.normalized.get("effective_date"):
        effective_date = date.fromisoformat(parties_clause.normalized["effective_date"])
    expiration = effective_date + relativedelta(months=term_months) - timedelta(days=1) if effective_date else None
    display = f"{term_months} months"
    if effective_date:
        display += f" from {effective_date.isoformat()}"
    if expiration:
        display += f" (estimated end {expiration.isoformat()})"
    return ClauseFact(
        clause_type="term",
        label="Term",
        display_value=display,
        normalized={
            "term_months": term_months,
            "effective_date": effective_date.isoformat() if effective_date else None,
            "estimated_expiration_date": expiration.isoformat() if expiration else None,
        },
        raw_text=chunk.text,
        citations=[make_citation(chunk, excerpt_around(chunk.text, match.start(), match.end()))],
        confidence=0.9,
    )


def extract_renewal_clause(chunks: list[SectionChunk]) -> ClauseFact | None:
    for chunk in ranked_chunks(chunks, ["renew", "notice", "term"]):
        text = chunk.text
        if "renew" not in text.lower():
            continue
        auto_renews = bool(re.search(r"automatic(?:ally)? renew|auto[- ]renew", text, re.IGNORECASE))
        notice_match = re.search(
            r"(?P<phrase>(?:[A-Za-z-]+\s*)?\(\d+\)|\d+|[A-Za-z-]+)\s*days?[^.]{0,60}?(?:notice|written notice)",
            text,
            re.IGNORECASE,
        )
        notice_days = extract_number(notice_match.group("phrase")) if notice_match else None
        renewal_match = re.search(
            r"successive\s+(?P<phrase>(?:[A-Za-z-]+\s*)?\(\d+\)|\d+|[A-Za-z-]+)[- ](?P<unit>month|year)",
            text,
            re.IGNORECASE,
        )
        renewal_term_months = None
        if renewal_match:
            rv = extract_number(renewal_match.group("phrase"))
            if rv:
                renewal_term_months = rv * 12 if renewal_match.group("unit").lower() == "year" else rv
        if not auto_renews and notice_days is None:
            continue
        pieces = []
        if auto_renews:
            pieces.append("Auto-renews")
        if renewal_term_months:
            pieces.append(f"{renewal_term_months}-month renewals")
        if notice_days is not None:
            pieces.append(f"{notice_days}-day notice")
        return ClauseFact(
            clause_type="renewal",
            label="Renewal",
            display_value=" • ".join(pieces) if pieces else "Renewal language detected",
            normalized={
                "auto_renews": auto_renews,
                "notice_days": notice_days,
                "renewal_term_months": renewal_term_months,
            },
            raw_text=text,
            citations=[make_citation(chunk, excerpt_around(text, notice_match.start(), notice_match.end())) if notice_match else make_citation(chunk)],
            confidence=0.9 if notice_days is not None else 0.76,
        )
    return None


def extract_pricing_clause(chunks: list[SectionChunk]) -> ClauseFact | None:
    for chunk in ranked_chunks(chunks, ["fee", "pricing", "price", "cpi", "renewal"]):
        text = chunk.text
        lower = text.lower()
        if not any(token in lower for token in ["fee", "pricing", "price", "cpi"]):
            continue
        initial_fixed = "fixed" in lower and "initial term" in lower
        cpi_linked = "consumer price index" in lower or "cpi" in lower
        cap_pct = extract_percentage(text)
        if not initial_fixed and not cpi_linked and cap_pct is None:
            continue
        display_parts = []
        if initial_fixed:
            display_parts.append("Fixed during initial term")
        if cpi_linked:
            display_parts.append(f"CPI-linked renewal uplift up to {cap_pct:g}%" if cap_pct is not None else "CPI-linked renewal uplift")
        elif cap_pct is not None:
            display_parts.append(f"Increase cap {cap_pct:g}%")
        return ClauseFact(
            clause_type="pricing",
            label="Pricing",
            display_value=" • ".join(display_parts),
            normalized={
                "fixed_initial_term": initial_fixed,
                "cpi_linked": cpi_linked,
                "renewal_increase_cap_pct": cap_pct,
            },
            raw_text=text,
            citations=[make_citation(chunk)],
            confidence=0.86,
        )
    return None


def extract_payment_clause(chunks: list[SectionChunk]) -> ClauseFact | None:
    for chunk in ranked_chunks(chunks, ["payment", "invoice", "receipt", "days"]):
        text = chunk.text
        lower = text.lower()
        if "invoice" not in lower and "pay" not in lower:
            continue
        payment_match = re.search(
            r"within\s+(?P<phrase>(?:[A-Za-z-]+\s*)?\(\d+\)|\d+|[A-Za-z-]+)\s*days?",
            text,
            re.IGNORECASE,
        )
        payment_days = extract_number(payment_match.group("phrase")) if payment_match else None
        if payment_days is None:
            continue
        return ClauseFact(
            clause_type="payment",
            label="Payment",
            display_value=f"Undisputed invoices due in {payment_days} days",
            normalized={"payment_days": payment_days},
            raw_text=text,
            citations=[make_citation(chunk, excerpt_around(text, payment_match.start(), payment_match.end()))],
            confidence=0.9,
        )
    return None


def extract_sla_clause(chunks: list[SectionChunk]) -> ClauseFact | None:
    for chunk in ranked_chunks(chunks, ["service level", "uptime", "availability", "incident", "service credit"]):
        text = chunk.text
        lower = text.lower()
        if not any(token in lower for token in ["uptime", "availability", "service level", "incident"]):
            continue
        uptime_pct = extract_percentage(text)
        response_match = re.search(
            r"response[^.]{0,40}?(?P<phrase>(?:[A-Za-z-]+\s*)?\(\d+\)|\d+|[A-Za-z-]+)\s*(?P<unit>hour|minute)",
            text,
            re.IGNORECASE,
        )
        response_value = extract_number(response_match.group("phrase")) if response_match else None
        response_unit = response_match.group("unit").lower() if response_match else None
        response_minutes = None
        if response_value and response_unit:
            response_minutes = response_value * 60 if response_unit == "hour" else response_value
        service_credits = None
        if re.search(r"does not include service credits|no service credits", lower):
            service_credits = False
        elif "service credit" in lower:
            service_credits = True
        if uptime_pct is None and response_minutes is None and service_credits is None:
            continue
        display_parts = []
        if uptime_pct is not None:
            display_parts.append(f"{uptime_pct:g}% monthly uptime")
        if response_minutes is not None:
            display_parts.append(f"P1 response in {response_minutes} minutes")
        if service_credits is False:
            display_parts.append("no service credits")
        elif service_credits is True:
            display_parts.append("service credits included")
        return ClauseFact(
            clause_type="sla",
            label="SLA",
            display_value=" • ".join(display_parts),
            normalized={
                "uptime_pct": uptime_pct,
                "priority_1_response_minutes": response_minutes,
                "service_credits": service_credits,
            },
            raw_text=text,
            citations=[make_citation(chunk)],
            confidence=0.9,
        )
    return None


def extract_termination_clause(chunks: list[SectionChunk]) -> ClauseFact | None:
    for chunk in ranked_chunks(chunks, ["terminate", "termination", "breach", "cure"]):
        text = chunk.text
        lower = text.lower()
        if "terminate" not in lower and "termination" not in lower:
            continue
        cure_match = re.search(
            r"uncured for\s+(?P<phrase>(?:[A-Za-z-]+\s*)?\(\d+\)|\d+|[A-Za-z-]+)\s*days?",
            text,
            re.IGNORECASE,
        )
        cure_days = extract_number(cure_match.group("phrase")) if cure_match else None
        for_convenience = bool(re.search(r"terminate for convenience", lower))
        display_parts = []
        if cure_days is not None:
            display_parts.append(f"Material breach cure period {cure_days} days")
        if for_convenience:
            display_parts.append("termination for convenience allowed")
        if not display_parts:
            display_parts.append("Termination language detected")
        return ClauseFact(
            clause_type="termination",
            label="Termination",
            display_value=" • ".join(display_parts),
            normalized={"cure_period_days": cure_days, "for_convenience": for_convenience},
            raw_text=text,
            citations=[make_citation(chunk)],
            confidence=0.84,
        )
    return None


def extract_liability_clause(chunks: list[SectionChunk]) -> ClauseFact | None:
    for chunk in ranked_chunks(chunks, ["liability", "damages", "fees paid", "aggregate"]):
        text = chunk.text
        lower = text.lower()
        if "liability" not in lower:
            continue
        if "unlimited liability" in lower or "no limitation of liability" in lower:
            return ClauseFact(
                clause_type="liability",
                label="Liability",
                display_value="Unlimited or uncapped liability language detected",
                normalized={"capped": False, "cap_type": "unlimited"},
                raw_text=text,
                citations=[make_citation(chunk)],
                confidence=0.88,
            )
        cap_match = re.search(r"(?:will|shall) not exceed", text, re.IGNORECASE)
        period_match = re.search(
            r"(?P<phrase>(?:[A-Za-z-]+\s*)?\(\d+\)|\d+|[A-Za-z-]+)\s*months?\s+preceding",
            text,
            re.IGNORECASE,
        )
        lookback_months = extract_number(period_match.group("phrase")) if period_match else None
        if cap_match:
            display = "Capped at fees paid or payable"
            if lookback_months:
                display += f" in prior {lookback_months} months"
            return ClauseFact(
                clause_type="liability",
                label="Liability",
                display_value=display,
                normalized={
                    "capped": True,
                    "cap_type": "fees_paid_prior_period",
                    "lookback_months": lookback_months,
                },
                raw_text=text,
                citations=[make_citation(chunk)],
                confidence=0.9,
            )
    return None


def extract_governing_law_clause(chunks: list[SectionChunk]) -> ClauseFact | None:
    pattern = re.compile(
        r"governed by the laws of(?: the)?(?: state of)?\s+(?P<jurisdiction>[A-Z][A-Za-z ]+?)(?:,|\.| without)",
        re.IGNORECASE,
    )
    result = find_match(chunks, keywords=["governing law", "governed by", "laws of"], patterns=[pattern])
    if not result:
        return None
    chunk, match = result
    jurisdiction = re.sub(r"\s+", " ", match.group("jurisdiction").strip())
    return ClauseFact(
        clause_type="governing_law",
        label="Governing law",
        display_value=jurisdiction,
        normalized={"jurisdiction": jurisdiction},
        raw_text=chunk.text,
        citations=[make_citation(chunk, excerpt_around(chunk.text, match.start(), match.end()))],
        confidence=0.9,
    )


def extract_data_processing_clause(chunks: list[SectionChunk]) -> ClauseFact | None:
    combined = "\n".join(chunk.text for chunk in chunks)
    handles_data = bool(re.search(r"process\w* [^.]{0,80}data|personal data|user account information|customer order data", combined, re.IGNORECASE))
    dpa_chunk = None
    for chunk in ranked_chunks(chunks, ["data processing", "dpa", "privacy", "personal data"]):
        lower = chunk.text.lower()
        if any(token in lower for token in ["data processing addendum", "dpa", "processing addendum"]):
            dpa_chunk = chunk
            break
    if not handles_data and not dpa_chunk:
        return None
    data_chunk = None
    for chunk in ranked_chunks(chunks, ["customer order data", "personal data", "user account information", "process"]):
        if re.search(r"process\w* [^.]{0,80}data|personal data|user account information|customer order data", chunk.text, re.IGNORECASE):
            data_chunk = chunk
            break
    citations = []
    if data_chunk:
        citations.append(make_citation(data_chunk))
    if dpa_chunk and (not citations or dpa_chunk.id != citations[0].chunk_id):
        citations.append(make_citation(dpa_chunk))
    display = "Customer data handling detected"
    if dpa_chunk:
        display += " • DPA/addendum language found"
    else:
        display += " • no DPA/addendum language found"
    return ClauseFact(
        clause_type="data_processing",
        label="Data processing",
        display_value=display,
        normalized={"handles_customer_data": handles_data, "dpa_present": bool(dpa_chunk)},
        raw_text=(data_chunk.text if data_chunk else combined[:1200]),
        citations=citations,
        confidence=0.85 if handles_data else 0.7,
    )


def build_obligations(clauses: list[ClauseFact]) -> list[dict]:
    obligations: list[dict] = []
    payment = lookup_clause(clauses, "payment")
    if payment:
        obligations.append(
            {
                "type": "payment",
                "party": "Customer",
                "description": payment.display_value,
                "citations": [citation.model_dump() for citation in payment.citations],
            }
        )
    sla = lookup_clause(clauses, "sla")
    if sla:
        obligations.append(
            {
                "type": "service_level",
                "party": "Provider",
                "description": sla.display_value,
                "citations": [citation.model_dump() for citation in sla.citations],
            }
        )
    renewal = lookup_clause(clauses, "renewal")
    if renewal and renewal.normalized.get("notice_days"):
        obligations.append(
            {
                "type": "renewal_notice",
                "party": "Either party",
                "description": f"Give {renewal.normalized['notice_days']} days' notice to stop auto-renewal.",
                "citations": [citation.model_dump() for citation in renewal.citations],
            }
        )
    return obligations


def extract_contract_facts(chunks: list[SectionChunk]) -> tuple[list[ClauseFact], list[dict]]:
    clauses: list[ClauseFact] = []
    parties_clause = extract_parties_and_effective_date(chunks)
    if parties_clause:
        clauses.append(parties_clause)

    extractors = [
        lambda c: extract_term_clause(c, parties_clause),
        extract_renewal_clause,
        extract_pricing_clause,
        extract_payment_clause,
        extract_sla_clause,
        extract_termination_clause,
        extract_liability_clause,
        extract_governing_law_clause,
        extract_data_processing_clause,
    ]

    for extractor in extractors:
        clause = extractor(chunks)
        if clause:
            clauses.append(clause)

    obligations = build_obligations(clauses)
    return clauses, obligations
