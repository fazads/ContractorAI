export default function SourceSections({ sections = [], selectedChunkIds = [] }) {
  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>Source sections</h3>
          <p>Click citations anywhere in the UI to highlight the underlying section here.</p>
        </div>
      </div>
      <div className="stack gap-sm">
        {sections.map((section) => {
          const active = selectedChunkIds.includes(section.id);
          return (
            <article key={section.id} id={section.id} className={`section-card ${active ? 'section-card-active' : ''}`}>
              <div className="section-card-header">
                <strong>{section.heading}</strong>
                <span className="muted">
                  {section.page_start && section.page_end && section.page_start !== section.page_end
                    ? `pp. ${section.page_start}-${section.page_end}`
                    : section.page_start
                    ? `p. ${section.page_start}`
                    : 'no page'}
                </span>
              </div>
              <p>{section.text}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
