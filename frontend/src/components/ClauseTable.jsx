import CitationList from './CitationList';

export default function ClauseTable({ clauses = [], onSelectCitation }) {
  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Normalized clause pack</h3>
          <p>Every extracted clause is stored with normalized values and source evidence.</p>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Clause</th>
              <th>Normalized value</th>
              <th>Confidence</th>
              <th>Sources</th>
            </tr>
          </thead>
          <tbody>
            {clauses.map((clause) => (
              <tr key={clause.clause_type}>
                <td>
                  <strong>{clause.label}</strong>
                  <div className="muted small-text">{clause.clause_type}</div>
                </td>
                <td>{clause.display_value}</td>
                <td>{Math.round((clause.confidence || 0) * 100)}%</td>
                <td>
                  <CitationList citations={clause.citations} onSelectCitation={onSelectCitation} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
