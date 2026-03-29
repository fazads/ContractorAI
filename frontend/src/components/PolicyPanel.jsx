export default function PolicyPanel({ policyPack, onPolicyChange, onReassess, disabled, canReassess }) {
  const handleNumber = (key) => (event) => {
    const value = event.target.value;
    onPolicyChange({ ...policyPack, [key]: value === '' ? '' : Number(value) });
  };

  const handleBoolean = (key) => (event) => {
    onPolicyChange({ ...policyPack, [key]: event.target.checked });
  };

  const handleList = (key) => (event) => {
    const values = event.target.value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    onPolicyChange({ ...policyPack, [key]: values });
  };

  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Policy pack</h3>
          <p>Reactive thresholds for risk review, market-fit scoring, and simple inbound playbook automation.</p>
        </div>
        <button className="button secondary" type="button" onClick={onReassess} disabled={disabled || !canReassess}>
          Re-run checks
        </button>
      </div>

      <div className="subsection-label">Risk thresholds</div>

      <label className="field">
        <span>Minimum renewal notice (days)</span>
        <input type="number" min="0" value={policyPack.min_renewal_notice_days} onChange={handleNumber('min_renewal_notice_days')} />
      </label>

      <label className="field">
        <span>Maximum payment cycle (days)</span>
        <input type="number" min="0" value={policyPack.max_payment_days} onChange={handleNumber('max_payment_days')} />
      </label>

      <label className="field">
        <span>Minimum SLA uptime (%)</span>
        <input type="number" min="0" step="0.1" value={policyPack.min_sla_uptime_pct} onChange={handleNumber('min_sla_uptime_pct')} />
      </label>

      <label className="field">
        <span>Expiry watch window (days)</span>
        <input type="number" min="0" value={policyPack.expiring_within_days} onChange={handleNumber('expiring_within_days')} />
      </label>

      <label className="checkbox-row">
        <input type="checkbox" checked={policyPack.require_service_credits} onChange={handleBoolean('require_service_credits')} />
        <span>Require service credits when SLA targets exist</span>
      </label>

      <label className="checkbox-row">
        <input type="checkbox" checked={policyPack.require_liability_cap} onChange={handleBoolean('require_liability_cap')} />
        <span>Require a limitation-of-liability cap</span>
      </label>

      <label className="checkbox-row">
        <input type="checkbox" checked={policyPack.requires_data_processing_terms} onChange={handleBoolean('requires_data_processing_terms')} />
        <span>Require DPA / data-processing language when customer data is handled</span>
      </label>

      <div className="divider" />
      <div className="subsection-label">Benchmark & playbook</div>

      <label className="field">
        <span>Preferred payment cycle (days)</span>
        <input type="number" min="0" value={policyPack.preferred_payment_days} onChange={handleNumber('preferred_payment_days')} />
      </label>

      <label className="field">
        <span>Preferred renewal uplift cap (%)</span>
        <input
          type="number"
          min="0"
          step="0.1"
          value={policyPack.preferred_renewal_increase_cap_pct}
          onChange={handleNumber('preferred_renewal_increase_cap_pct')}
        />
      </label>

      <label className="field">
        <span>Allowed governing laws (comma-separated)</span>
        <input value={(policyPack.allowed_governing_laws || []).join(', ')} onChange={handleList('allowed_governing_laws')} />
      </label>

      <label className="field">
        <span>Max medium risks for auto-approval</span>
        <input type="number" min="0" value={policyPack.max_auto_approve_medium_risks} onChange={handleNumber('max_auto_approve_medium_risks')} />
      </label>

      <label className="field">
        <span>Max watch items for auto-approval</span>
        <input type="number" min="0" value={policyPack.max_auto_approve_watch_items} onChange={handleNumber('max_auto_approve_watch_items')} />
      </label>

      <label className="checkbox-row">
        <input type="checkbox" checked={policyPack.auto_approve_simple_inbound} onChange={handleBoolean('auto_approve_simple_inbound')} />
        <span>Enable auto-approval for simple inbound contracts that clear the playbook</span>
      </label>
    </section>
  );
}
