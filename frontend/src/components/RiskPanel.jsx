import CitationList from './CitationList';

export default function RiskPanel({ risks = [], onSelectCitation }) {
  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Flagged risks</h3>
          <p>Rule-based findings linked back to the extracted contract evidence.</p>
        </div>
      </div>
      {risks.length ? (
        <div className="stack gap-sm">
          {risks.map((risk) => (
            <article key={risk.id} className={`risk-card risk-${risk.severity}`}>
              <div className="risk-card-header">
                <span className={`severity-pill severity-${risk.severity}`}>{risk.severity}</span>
                <strong>{risk.title}</strong>
              </div>
              <p>{risk.explanation}</p>
              <p className="muted"><strong>Recommended action:</strong> {risk.recommended_action}</p>
              <CitationList citations={risk.citations} onSelectCitation={onSelectCitation} />
            </article>
          ))}
        </div>
      ) : (
        <p className="muted">No policy violations are currently flagged.</p>
      )}
    </section>
  );
}
