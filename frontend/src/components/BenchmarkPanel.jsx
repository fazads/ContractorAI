import CitationList from './CitationList';

function statusLabel(status) {
  switch (status) {
    case 'within_market':
      return 'Within market';
    case 'near_market':
      return 'Near market';
    case 'outside_market':
      return 'Outside market';
    case 'missing':
      return 'Missing';
    case 'not_applicable':
      return 'N/A';
    default:
      return status;
  }
}

function scoreClass(score) {
  if (score >= 85) return 'pill pill-pass';
  if (score >= 65) return 'pill pill-watch';
  return 'pill pill-fail';
}

function outcomeClass(outcome) {
  if (outcome === 'pass') return 'pill pill-pass';
  if (outcome === 'watch') return 'pill pill-watch';
  return 'pill pill-fail';
}

export default function BenchmarkPanel({ benchmarkPack, onSelectCitation }) {
  if (!benchmarkPack?.items?.length) {
    return (
      <section className="panel empty-panel">
        <h3>Benchmarks & market fit</h3>
        <p className="muted">Analyze a contract to compare extracted clauses against the local benchmark pack.</p>
      </section>
    );
  }

  const referenceMap = Object.fromEntries((benchmarkPack.references || []).map((reference) => [reference.reference_id, reference]));

  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Benchmarks & market fit</h3>
          <p>
            Illustrative benchmark pack modeled on Spellbook-style term coverage and TermScout-style market comparison.
          </p>
        </div>
      </div>

      <div className="summary-grid compact-metrics">
        <article className="summary-card metric-inline">
          <h4>Coverage</h4>
          <strong>{benchmarkPack.coverage_score_pct}%</strong>
          <span className="muted">term coverage score</span>
        </article>
        <article className="summary-card metric-inline">
          <h4>Playbook fit</h4>
          <strong>{benchmarkPack.playbook_fit_score}/100</strong>
          <span className="muted">benchmark fit score</span>
        </article>
        <article className="summary-card metric-inline">
          <h4>Pass</h4>
          <strong>{benchmarkPack.counts?.pass || 0}</strong>
          <span className="muted">clauses in band</span>
        </article>
        <article className="summary-card metric-inline">
          <h4>Watch / fail</h4>
          <strong>
            {(benchmarkPack.counts?.watch || 0) + (benchmarkPack.counts?.fail || 0)}
          </strong>
          <span className="muted">clauses needing attention</span>
        </article>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Clause</th>
              <th>Contract value</th>
              <th>Benchmark view</th>
              <th>Playbook</th>
              <th>Score</th>
              <th>Sources</th>
            </tr>
          </thead>
          <tbody>
            {benchmarkPack.items.map((item) => {
              const reference = referenceMap[item.benchmark_reference_id];
              return (
                <tr key={item.clause_type}>
                  <td>
                    <strong>{item.label}</strong>
                    <div className="muted small-text">{item.market_standard}</div>
                  </td>
                  <td>
                    <div>{item.contract_value}</div>
                    {item.fallback_position ? <div className="muted small-text">Fallback: {item.fallback_position}</div> : null}
                    <div className="small-text subtle-copy">{item.reasoning}</div>
                    {reference ? (
                      <div className="muted small-text">
                        Reference: {reference.url ? (
                          <a href={reference.url} target="_blank" rel="noreferrer">{reference.label}</a>
                        ) : reference.label}
                      </div>
                    ) : null}
                  </td>
                  <td>
                    <span className={outcomeClass(item.market_alignment === 'outside_market' || item.market_alignment === 'missing' ? 'fail' : item.market_alignment === 'near_market' || item.market_alignment === 'not_applicable' ? 'watch' : 'pass')}>
                      {statusLabel(item.market_alignment)}
                    </span>
                    <div className="muted small-text">Coverage: {item.coverage_status}</div>
                  </td>
                  <td>
                    <span className={outcomeClass(item.playbook_outcome)}>{item.playbook_outcome}</span>
                  </td>
                  <td>
                    <span className={scoreClass(item.score)}>{item.score}</span>
                  </td>
                  <td>
                    <CitationList citations={item.citations} onSelectCitation={onSelectCitation} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="two-column-copy">
        <div>
          <h4>Notes</h4>
          <ul className="clean-list">
            {(benchmarkPack.notes || []).map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4>Benchmark references</h4>
          <ul className="clean-list">
            {(benchmarkPack.references || []).slice(0, 4).map((reference) => (
              <li key={reference.reference_id}>
                <strong>{reference.url ? <a href={reference.url} target="_blank" rel="noreferrer">{reference.label}</a> : reference.label}</strong>
                {reference.note ? <div className="muted small-text">{reference.note}</div> : null}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
