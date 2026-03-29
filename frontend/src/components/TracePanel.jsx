export default function TracePanel({ contract }) {
  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Trace & shared state</h3>
          <p>The assistant keeps an audit trail plus a structured JSON contract state.</p>
        </div>
      </div>
      {contract ? (
        <>
          <div className="trace-list">
            {contract.audit_trail.map((event, index) => (
              <div key={`${event.agent}-${event.action}-${index}`} className="trace-item">
                <strong>{event.agent}</strong>
                <span>{event.action}</span>
                <span className="muted">{event.status}</span>
              </div>
            ))}
          </div>
          <details>
            <summary>View shared contract JSON</summary>
            <pre className="json-box">{JSON.stringify(contract, null, 2)}</pre>
          </details>
        </>
      ) : (
        <p className="muted">Analyze a contract to view the shared state and agent trace.</p>
      )}
    </section>
  );
}
