import { useState } from 'react';
import CitationList from './CitationList';

export default function QAPanel({ contract, onAskQuestion, onSelectCitation, loading }) {
  const [question, setQuestion] = useState('What is the renewal notice period?');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!question.trim() || !contract) return;
    onAskQuestion(question);
  };

  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Ask the contract</h3>
          <p>Answers are grounded in extracted clauses or retrieved source sections.</p>
        </div>
      </div>
      <form className="stack gap-xs" onSubmit={handleSubmit}>
        <textarea
          rows={3}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about pricing, renewal, liability, market fit, or whether the contract can be auto-approved..."
        />
        <button className="button" type="submit" disabled={!contract || loading || !question.trim()}>
          {loading ? 'Answering…' : 'Ask question'}
        </button>
      </form>

      <div className="stack gap-sm">
        {contract?.answers?.length ? (
          [...contract.answers].slice().reverse().map((answer, index) => (
            <article key={`${answer.timestamp}-${index}`} className="answer-card">
              <strong>{answer.question}</strong>
              <p>{answer.answer}</p>
              <div className="meta-row">
                <span className="muted">Confidence {Math.round((answer.confidence || 0) * 100)}%</span>
                {answer.abstained ? <span className="warning-inline">Abstained / low evidence</span> : null}
              </div>
              <CitationList citations={answer.citations} onSelectCitation={onSelectCitation} />
            </article>
          ))
        ) : (
          <p className="muted">No questions asked yet.</p>
        )}
      </div>
    </section>
  );
}
