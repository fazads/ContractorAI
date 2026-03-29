from __future__ import annotations

from .models import PolicyPack

SAMPLE_CONTRACT_FILE_NAME = "acme_nimbus_msa_sample.txt"
SAMPLE_SIMPLE_INBOUND_FILE_NAME = "bluebird_vendor_agreement_sample.txt"

SAMPLE_POLICY = PolicyPack(
    min_renewal_notice_days=90,
    max_payment_days=60,
    min_sla_uptime_pct=99.9,
    require_service_credits=True,
    require_liability_cap=True,
    requires_data_processing_terms=True,
    expiring_within_days=120,
    preferred_payment_days=45,
    preferred_renewal_increase_cap_pct=5.0,
    allowed_governing_laws=["New York", "Delaware", "California", "England and Wales"],
    auto_approve_simple_inbound=True,
    max_auto_approve_medium_risks=1,
    max_auto_approve_watch_items=2,
)

SAMPLE_CONTRACT_TEXT = """[[PAGE 1]]
MASTER SERVICES AGREEMENT

This Master Services Agreement (\"Agreement\") is entered into as of January 1, 2026 (the \"Effective Date\") by and between Acme Manufacturing, Inc. (\"Customer\") and Nimbus Analytics LLC (\"Provider\").

1. Services
Provider will deliver hosted analytics and reporting services described in applicable statements of work. In providing the services, Provider will process Customer order data, usage records, and user account information solely to operate the platform and deliver reporting.

2. Term and Renewal
The initial term of this Agreement is twelve (12) months from the Effective Date. Thereafter, this Agreement will automatically renew for successive one-year terms unless either party gives at least sixty (60) days' written notice before the end of the then-current term.

[[PAGE 2]]
3. Fees and Payment
Fees during the initial term are fixed as set out in Schedule A. Renewal pricing may increase once per renewal term by the Consumer Price Index (CPI), capped at four percent (4%). Provider may invoice monthly in arrears. Customer will pay undisputed invoices within forty-five (45) days of receipt.

4. Service Levels
Provider will make the hosted service available 99.9% of the time in each calendar month, excluding planned maintenance. Priority 1 incidents will receive an initial response within one (1) hour. This Agreement does not include service credits.

5. Termination
Either party may terminate this Agreement for material breach if the breach remains uncured for thirty (30) days after written notice.

[[PAGE 3]]
6. Limitation of Liability
Except for fraud or willful misconduct, each party's aggregate liability under this Agreement will not exceed the fees paid or payable under this Agreement during the twelve (12) months preceding the event giving rise to the claim.

7. Governing Law
This Agreement is governed by the laws of the State of New York, without regard to conflict of law rules.

8. Confidentiality
Each party will protect the other party's confidential information using reasonable safeguards.
"""

SAMPLE_SIMPLE_INBOUND_TEXT = """[[PAGE 1]]
VENDOR AGREEMENT

This Vendor Agreement (\"Agreement\") is entered into as of February 1, 2026 by and between Bluebird Foods, Inc. (\"Customer\") and Lantern Software Ltd. (\"Provider\").

1. Services
Provider will supply hosted workflow software and standard implementation support. Provider will process Customer order data and user account information solely to provide the services and will comply with the Data Processing Addendum attached as Exhibit B.

2. Term and Renewal
The initial term of this Agreement is twelve (12) months from the Effective Date. Thereafter, this Agreement will automatically renew for successive one-year terms unless either party gives at least ninety (90) days' written notice before the end of the then-current term.

[[PAGE 2]]
3. Fees and Payment
Fees are fixed during the initial term. Renewal pricing may increase once per year by the Consumer Price Index (CPI), capped at three percent (3%). Customer will pay undisputed invoices within thirty (30) days of receipt.

4. Service Levels
Provider will make the hosted service available 99.95% of the time in each calendar month. Priority 1 incidents will receive an initial response within one (1) hour. Service credits are available under Schedule C for any month in which the service level is missed.

5. Termination
Either party may terminate this Agreement for material breach if the breach remains uncured for thirty (30) days after written notice.

6. Limitation of Liability
Except for fraud or willful misconduct, each party's aggregate liability under this Agreement will not exceed the fees paid or payable under this Agreement during the twelve (12) months preceding the event giving rise to the claim.

7. Governing Law
This Agreement is governed by the laws of the State of New York, without regard to conflict of law rules.
"""
