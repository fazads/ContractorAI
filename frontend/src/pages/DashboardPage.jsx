import { useMemo, useState } from 'react';
import { analyzeText, analyzeUpload, askQuestion, getSampleContract, reassessContract } from '../api';
import BenchmarkPanel from '../components/BenchmarkPanel';
import ClauseTable from '../components/ClauseTable';
import PlaybookPanel from '../components/PlaybookPanel';
import PolicyPanel from '../components/PolicyPanel';
import QAPanel from '../components/QAPanel';
import RiskPanel from '../components/RiskPanel';
import SourceSections from '../components/SourceSections';
import SummaryCards from '../components/SummaryCards';
import TracePanel from '../components/TracePanel';
import UploadPanel from '../components/UploadPanel';
import { defaultPolicyPack } from '../data/helpContent';

function routeLabel(route) {
  switch (route) {
    case 'auto_approve':
      return 'Auto-approve';
    case 'business_review':
      return 'Business review';
    case 'legal_review':
      return 'Legal review';
    default:
      return route ? route.replaceAll('_', ' ') : '—';
  }
}

export default function DashboardPage() {
  const [contract, setContract] = useState(null);
  const [policyPack, setPolicyPack] = useState(defaultPolicyPack);
  const [selectedChunkIds, setSelectedChunkIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [qaLoading, setQaLoading] = useState(false);
  const [error, setError] = useState('');

  const riskCounts = useMemo(() => {
    const counts = { high: 0, medium: 0, low: 0 };
    (contract?.risks || []).forEach((risk) => {
      counts[risk.severity] += 1;
    });
    return counts;
  }, [contract]);

  const applyContract = (nextContract) => {
    setContract(nextContract);
    setPolicyPack(nextContract.policy_pack || defaultPolicyPack);
    setSelectedChunkIds([]);
  };

  const handleAnalyzeText = async ({ text, fileName }) => {
    setLoading(true);
    setError('');
    try {
      const payload = await analyzeText({ text, fileName, policyPack });
      applyContract(payload.contract);
    } catch (err) {
      setError(err.message || 'Failed to analyze text.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeUpload = async (file) => {
    setLoading(true);
    setError('');
    try {
      const payload = await analyzeUpload({ file, policyPack });
      applyContract(payload.contract);
    } catch (err) {
      setError(err.message || 'Failed to analyze file.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async (kind = 'default') => {
    setLoading(true);
    setError('');
    try {
      const sample = await getSampleContract(kind);
      const payload = await analyzeText({ text: sample.text, fileName: sample.file_name, policyPack: sample.policy_pack });
      applyContract(payload.contract);
    } catch (err) {
      setError(err.message || 'Failed to load the sample contract.');
    } finally {
      setLoading(false);
    }
  };

  const handleReassess = async () => {
    if (!contract) return;
    setLoading(true);
    setError('');
    try {
      const payload = await reassessContract(contract.contract_id, policyPack);
      applyContract(payload.contract);
    } catch (err) {
      setError(err.message || 'Failed to reassess contract.');
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (question) => {
    if (!contract) return;
    setQaLoading(true);
    setError('');
    try {
      const payload = await askQuestion(contract.contract_id, question);
      setContract(payload.contract);
      const citations = payload.contract.answers?.at(-1)?.citations || [];
      if (citations.length) {
        setSelectedChunkIds(citations.map((citation) => citation.chunk_id));
      }
    } catch (err) {
      setError(err.message || 'Failed to answer question.');
    } finally {
      setQaLoading(false);
    }
  };

  const handleSelectCitation = (citation) => {
    if (!citation?.chunk_id) return;
    setSelectedChunkIds([citation.chunk_id]);
    const element = document.getElementById(citation.chunk_id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className="dashboard stack gap-md">
      <section className="hero panel">
        <div>
          <p className="eyebrow">Local review workspace</p>
          <h2>Upload contracts, benchmark terms, route simpler inbound paper, and keep legal in control.</h2>
          <p className="hero-copy">
            This UI is intentionally assistive: every summary, benchmark, answer, and playbook decision links back to the contract text so legal and business reviewers stay in control.
          </p>
        </div>
        <div className="hero-metrics hero-metrics-wide">
          <div className="metric-card">
            <strong>{contract?.clauses?.length || 0}</strong>
            <span>normalized clauses</span>
          </div>
          <div className="metric-card">
            <strong>{contract?.benchmark_pack?.playbook_fit_score || 0}</strong>
            <span>playbook fit score</span>
          </div>
          <div className="metric-card">
            <strong>{contract?.benchmark_pack?.coverage_score_pct || 0}%</strong>
            <span>benchmark coverage</span>
          </div>
          <div className="metric-card">
            <strong>{routeLabel(contract?.playbook_decision?.recommended_route)}</strong>
            <span>recommended route</span>
          </div>
          <div className="metric-card">
            <strong>{riskCounts.high}</strong>
            <span>high risks</span>
          </div>
          <div className="metric-card">
            <strong>{riskCounts.medium}</strong>
            <span>medium risks</span>
          </div>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="workspace-grid">
        <aside className="workspace-sidebar stack gap-md">
          <UploadPanel
            onAnalyzeText={handleAnalyzeText}
            onAnalyzeUpload={handleAnalyzeUpload}
            onLoadSample={() => handleLoadSample('default')}
            onLoadSimpleInboundSample={() => handleLoadSample('simple_inbound')}
            loading={loading}
            docMeta={contract?.doc_meta}
          />
          <PolicyPanel policyPack={policyPack} onPolicyChange={setPolicyPack} onReassess={handleReassess} disabled={loading} canReassess={!!contract} />
        </aside>

        <section className="workspace-main stack gap-md">
          <SummaryCards contract={contract} onSelectCitation={handleSelectCitation} />
          <BenchmarkPanel benchmarkPack={contract?.benchmark_pack} onSelectCitation={handleSelectCitation} />
          <ClauseTable clauses={contract?.clauses || []} onSelectCitation={handleSelectCitation} />
          <SourceSections sections={contract?.sections || []} selectedChunkIds={selectedChunkIds} />
        </section>

        <aside className="workspace-sidebar stack gap-md">
          <PlaybookPanel playbookDecision={contract?.playbook_decision} onSelectCitation={handleSelectCitation} />
          <QAPanel contract={contract} onAskQuestion={handleAskQuestion} onSelectCitation={handleSelectCitation} loading={qaLoading} />
          <RiskPanel risks={contract?.risks || []} onSelectCitation={handleSelectCitation} />
          <TracePanel contract={contract} />
        </aside>
      </div>
    </div>
  );
}
