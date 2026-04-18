export default function CitationCard({ citation }) {
  const sourceLabel = citation.source === 'web' ? 'Web' : 'Knowledge Base'
  const score = Number(citation.score)

  return (
    <article className="citation-card">
      <div className="citation-card__header">
        <strong className="citation-card__title">
          {citation.document_title || citation.title || 'Source'}
        </strong>
        <span className="citation-card__badge">{sourceLabel}</span>
      </div>

      {citation.snippet ? <p className="citation-card__snippet">{citation.snippet}</p> : null}

      <div className="citation-card__meta muted">
        {citation.source === 'kb' && Number.isInteger(citation.chunk_index) ? (
          <span>Chunk #{citation.chunk_index + 1}</span>
        ) : null}
        {citation.url ? (
          <a href={citation.url} target="_blank" rel="noreferrer" className="citation-card__link">
            Open source
          </a>
        ) : null}
        {Number.isFinite(score) ? <span>Score {(score * 100).toFixed(0)}%</span> : null}
      </div>
    </article>
  )
}
