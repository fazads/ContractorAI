export const defaultPolicyPack = {
  min_renewal_notice_days: 90,
  max_payment_days: 60,
  min_sla_uptime_pct: 99.9,
  require_service_credits: true,
  require_liability_cap: true,
  requires_data_processing_terms: true,
  expiring_within_days: 120,
  preferred_payment_days: 45,
  preferred_renewal_increase_cap_pct: 5.0,
  allowed_governing_laws: ['New York', 'Delaware', 'California', 'England and Wales'],
  auto_approve_simple_inbound: true,
  max_auto_approve_medium_risks: 1,
  max_auto_approve_watch_items: 2,
};

export const helpContent = {
  hero: {
    title: 'Contract AI Assistant — local prototype',
    description:
      'This app turns the leadership presentation into a runnable local workflow: upload a contract, normalize key clauses, compare them to an illustrative benchmark pack, route simpler inbound paper through a playbook, ask grounded questions, and review policy-driven flags with citations.',
  },
  sections: [
    {
      title: 'What this prototype now implements',
      items: [
        'Orchestrator agent that routes ingestion, clause extraction, summarization, benchmarking, Q&A, risk analysis, and playbook automation.',
        'Shared contract state in structured JSON so every output stays traceable and reviewable.',
        'OCR-aware ingestion path for images, plus PDF, DOCX, and text parsing.',
        'Grounded answers that carry citations back to source sections.',
        'Reactive policy pack so legal, procurement, and operations teams can re-run risk checks, benchmark scores, and simple-inbound routing.',
        'Illustrative benchmark pack that mimics Spellbook-style coverage and TermScout-style market-fit summaries, without claiming proprietary vendor data.',
        'Juro-style playbook automation for simpler inbound contracts: auto-approve, send fallback language, or escalate to legal.',
      ],
    },
    {
      title: 'How the local build maps to the deck',
      table: [
        ['Deck idea', 'Local implementation'],
        ['Orchestrator agent', 'Backend `OrchestratorAgent` coordinates specialist agents and stores audit events.'],
        ['Document ingestion', 'FastAPI parses PDF, DOCX, TXT, and image uploads with optional OCR dependencies.'],
        ['Clause extraction and normalization', 'Regex + section heuristics produce normalized facts for term, renewal, SLA, pricing, liability, and more.'],
        ['Vector database / retrieval', 'Prototype uses an in-memory semantic index with TF-IDF by default and optional sentence-transformer embeddings.'],
        ['Grounded Q&A', 'The UI always shows evidence and citations; benchmark and playbook questions are answered from structured state first.'],
        ['Risk/compliance analysis', 'A configurable policy pack triggers rule-based flags for short notice windows, missing service credits, DPA gaps, and approaching expiry.'],
        ['Benchmarking', 'A benchmark agent compares extracted clauses against an illustrative market / house standard pack and scores playbook fit.'],
        ['Playbook automation', 'A routing agent places contracts into simple inbound, standard inbound, or complex lanes and suggests fallback redlines.'],
      ],
    },
    {
      title: 'Benchmarking and playbook logic',
      items: [
        'Coverage score mirrors the idea of checking whether the document contains the expected term families for that contract type.',
        'Playbook fit score is a simplified local signal that summarizes whether the extracted terms stay inside preferred market and house thresholds.',
        'Auto-approval is only allowed when the contract lands in the simple inbound lane, has no high risks, and stays inside the configured watch/fail limits.',
        'If a contract misses straight auto-approval but the benchmark gaps have fallback text, the tool recommends a business review lane with suggested redlines.',
        'If the contract is long, risky, or outside the benchmark band, the route becomes legal review.',
      ],
    },
    {
      title: 'Operating model from the presentation',
      items: [
        'Assistive system, not autonomous legal approval.',
        'Human reviewer keeps final control over clause interpretation and outbound actions.',
        'Citations are mandatory to reduce hallucinations and speed reviewer trust.',
        'The recommended production path is stronger parsing, a persistent vector store, identity controls, audit retention, benchmark calibration, and model evaluation before scale-up.',
      ],
    },
    {
      title: 'How to use the app',
      items: [
        'Load the review sample for a more mixed-risk MSA or the simple inbound sample to see playbook automation working cleanly.',
        'Review the executive summary, benchmark table, and normalized clause pack.',
        'Click citations to highlight the exact source section used by the assistant.',
        'Adjust the policy pack and re-run risk checks, benchmark scores, and routing without re-uploading the contract.',
        'Ask natural-language questions about clauses, market fit, or whether the contract can be auto-approved.',
      ],
    },
  ],
  references: [
    {
      label: 'World Commerce & Contracting — whitepaper used for the slide 2 business case metrics',
      url: 'https://info.worldcc.com/contract-management-aug-2025',
      note:
        'Used in the deck for the 8.6% value erosion figure, the “almost 90% difficult to understand” finding, and the average of 24 systems where contract data is scattered.',
    },
    {
      label: 'Spellbook Benchmarks overview',
      url: 'https://www.spellbook.legal/blog/benchmarks',
      note:
        'Public product overview describing at-a-glance checks against market standards or custom standards.',
    },
    {
      label: 'Spellbook Benchmarks FAQ',
      url: 'https://help.spellbook.legal/en/articles/9160166-how-to-review-documents-with-benchmarks',
      note:
        'Public description of standards, pass/fail rules, and coverage score behavior.',
    },
    {
      label: 'TermScout benchmarking overview',
      url: 'https://blog.termscout.com/benchmarking-what-top-vendors-get-right',
      note:
        'Public description of benchmarking using 800+ data points across thousands of contracts.',
    },
    {
      label: 'TermScout market benchmarking overview',
      url: 'https://www.termscout.com/',
      note:
        'Public overview of benchmarking against real-world market standards, contract Signals, and certification.',
    },
    {
      label: 'Juro AI contract review',
      url: 'https://juro.com/ai-contract-review',
      note:
        'Public description of reviewing and redlining third-party paper against playbooks.',
    },
    {
      label: 'Juro conditional logic for contract playbooks',
      url: 'https://juro.com/learn/automated-contract-playbook-dynamic-templates',
      note:
        'Public description of conditional logic for automating clauses, fallback positions, and contract workflows.',
    },
    {
      label: 'Case study prompt requirements',
      url: '#',
      note:
        'Summarization, Q&A, risky / expiring / non-compliant clause flags, orchestrator + specialist agents, structured shared state, and citations.',
    },
  ],
};
