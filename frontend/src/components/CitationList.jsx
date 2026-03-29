function labelForCitation(citation) {
  if (!citation) return 'Source';
  const start = citation.page_start;
  const end = citation.page_end;
  if (start && end && start !== end) return `${citation.section} • pp. ${start}-${end}`;
  if (start) return `${citation.section} • p. ${start}`;
  return citation.section;
}

export default function CitationList({ citations = [], onSelectCitation }) {
  if (!citations.length) return <span className="muted">No citations</span>;
  return (
    <div className="citation-list">
      {citations.map((citation, index) => (
        <button
          key={`${citation.chunk_id}-${index}`}
          className="citation-chip"
          type="button"
          onClick={() => onSelectCitation?.(citation)}
          title={citation.excerpt || ''}
        >
          {labelForCitation(citation)}
        </button>
      ))}
    </div>
  );
}
