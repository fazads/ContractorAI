import CitationList from './CitationList';

export default function SummaryCards({ contract, onSelectCitation }) {
  if (!contract) {
    return (
      <section className="panel empty-panel">
        <h3>Executive summary</h3>
        <p className="muted">Upload a contract to generate a structured summary.</p>
      </section>
    );
  }

  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Executive summary</h3>
          <p>{contract.summary.executive_summary}</p>
        </div>
      </div>

      <div className="summary-grid">
        {contract.summary.clause_pack.map((item) => (
          <article key={item.label} className="summary-card">
            <div className="summary-card-header">
              <h4>{item.label}</h4>
              <span className="confidence-pill">{Math.round((item.confidence || 0) * 100)}%</span>
            </div>
            <p>{item.value}</p>
            <CitationList citations={item.citations} onSelectCitation={onSelectCitation} />
          </article>
        ))}
      </div>

      <div className="two-column-copy">
        <div>
          <h4>Key findings</h4>
          <ul className="clean-list">
            {contract.summary.key_findings.map((finding) => (
              <li key={finding}>{finding}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4>Open questions</h4>
          {contract.summary.open_questions.length ? (
            <ul className="clean-list">
              {contract.summary.open_questions.map((question) => (
                <li key={question}>{question}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">No obvious missing clause families in the extracted core text.</p>
          )}
        </div>
      </div>
    </section>
  );
}
