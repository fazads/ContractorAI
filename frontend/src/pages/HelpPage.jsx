import { helpContent } from '../data/helpContent';

function SectionBlock({ section }) {
  return (
    <section className="panel stack gap-sm">
      <div className="panel-header">
        <div>
          <h3>{section.title}</h3>
        </div>
      </div>
      {section.items ? (
        <ul className="clean-list">
          {section.items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {section.table ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {section.table[0].map((heading) => (
                  <th key={heading}>{heading}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {section.table.slice(1).map((row) => (
                <tr key={row[0]}>
                  {row.map((cell) => (
                    <td key={cell}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

export default function HelpPage() {
  return (
    <div className="stack gap-md help-page">
      <section className="hero panel">
        <div>
          <p className="eyebrow">Presentation map</p>
          <h2>{helpContent.hero.title}</h2>
          <p className="hero-copy">{helpContent.hero.description}</p>
        </div>
      </section>

      <div className="help-grid">
        {helpContent.sections.map((section) => (
          <SectionBlock key={section.title} section={section} />
        ))}
      </div>

      <section className="panel stack gap-sm">
        <div className="panel-header">
          <div>
            <h3>References</h3>
            <p>These notes mirror the business case and design choices discussed in the presentation.</p>
          </div>
        </div>
        <ul className="clean-list">
          {helpContent.references.map((reference) => (
            <li key={reference.label}>
              <strong>{reference.label}</strong>
              <div>{reference.note}</div>
              {reference.url !== '#' ? (
                <a href={reference.url} target="_blank" rel="noreferrer">
                  {reference.url}
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
