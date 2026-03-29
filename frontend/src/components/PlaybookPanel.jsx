import CitationList from './CitationList';

function routeLabel(route) {
  switch (route) {
    case 'auto_approve':
      return 'Auto-approve';
    case 'business_review':
      return 'Business review';
    case 'legal_review':
      return 'Legal review';
    default:
      return route;
  }
}

function routeClass(route) {
  if (route === 'auto_approve') return 'route-banner route-pass';
  if (route === 'business_review') return 'route-banner route-watch';
  return 'route-banner route-fail';
}

function outcomeClass(outcome) {
  if (outcome === 'pass') return 'pill pill-pass';
  if (outcome === 'watch') return 'pill pill-watch';
  return 'pill pill-fail';
}

export default function PlaybookPanel({ playbookDecision, onSelectCitation }) {
  if (!playbookDecision?.rule_results?.length) {
    return (
      <section className="panel empty-panel">
        <h3>Playbook automation</h3>
        <p className="muted">Analyze a contract to route it through the simple-inbound playbook.</p>
      </section>
    );
  }

  const priorityResults = playbookDecision.rule_results.filter((result) => result.outcome !== 'pass');
  const passResults = playbookDecision.rule_results.filter((result) => result.outcome === 'pass');

  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Playbook automation</h3>
          <p>Juro-style routing for simpler inbound contracts: auto-approve safe paper, send fallback language, or escalate.</p>
        </div>
      </div>

      <div className={routeClass(playbookDecision.recommended_route)}>
        <div className="route-header-row">
          <span className="route-badge">{routeLabel(playbookDecision.recommended_route)}</span>
          <span className="muted small-text">Lane: {playbookDecision.contract_lane.replaceAll('_', ' ')}</span>
        </div>
        <p>{playbookDecision.decision_summary}</p>
        <div className="meta-row">
          <span className="muted">Playbook score {playbookDecision.score}/100</span>
          <span className="muted">Auto-approval eligible: {playbookDecision.auto_approval_eligible ? 'yes' : 'no'}</span>
          <span className="muted">Fallback-ready: {playbookDecision.approved_if_using_fallbacks ? 'yes' : 'no'}</span>
        </div>
      </div>

      <div className="stack gap-sm">
        {(priorityResults.length ? priorityResults : playbookDecision.rule_results).map((result) => (
          <article key={result.rule_id} className="playbook-card">
            <div className="playbook-card-header">
              <span className={outcomeClass(result.outcome)}>{result.outcome}</span>
              <strong>{result.title}</strong>
              <span className="muted small-text">Owner: {result.owner}</span>
            </div>
            <p>{result.explanation}</p>
            {result.suggested_redline ? (
              <div className="playbook-fallback">
                <strong>Suggested fallback</strong>
                <p>{result.suggested_redline}</p>
              </div>
            ) : null}
            <CitationList citations={result.citations} onSelectCitation={onSelectCitation} />
          </article>
        ))}
      </div>

      {passResults.length ? (
        <details>
          <summary>Show passed playbook checks ({passResults.length})</summary>
          <div className="stack gap-sm details-stack">
            {passResults.map((result) => (
              <article key={result.rule_id} className="playbook-card playbook-card-pass">
                <div className="playbook-card-header">
                  <span className={outcomeClass(result.outcome)}>{result.outcome}</span>
                  <strong>{result.title}</strong>
                </div>
                <p>{result.explanation}</p>
                <CitationList citations={result.citations} onSelectCitation={onSelectCitation} />
              </article>
            ))}
          </div>
        </details>
      ) : null}

      <div>
        <h4>Next steps</h4>
        <ul className="clean-list">
          {(playbookDecision.next_steps || []).map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
