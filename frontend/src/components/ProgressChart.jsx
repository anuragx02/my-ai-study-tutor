export default function ProgressChart({ values = [] }) {
  const numericValues = values.map((value) => Number(value) || 0)
  const hasData = numericValues.length > 0
  const first = hasData ? numericValues[0] : 0
  const last = hasData ? numericValues[numericValues.length - 1] : 0
  const delta = Number((last - first).toFixed(2))
  const trendLabel =
    !hasData
      ? 'No data yet'
      : delta > 0
        ? `Improving (+${delta})`
        : delta < 0
          ? `Declining (${delta})`
          : 'Stable (0)'

  return (
    <div className="card">
      <strong>Progress</strong>
      <div className="muted" style={{ marginTop: 6 }}>{trendLabel}</div>
      {hasData ? (
        <>
          <div className="muted" style={{ marginTop: 6 }}>Recent scores: {numericValues.join(' -> ')}</div>
          <div style={{ display: 'flex', gap: 8, marginTop: 12, alignItems: 'flex-end' }}>
            {numericValues.map((value, index) => {
              const height = Math.max(8, Math.round((value / 100) * 56))
              return (
                <div
                  key={`${index}-${value}`}
                  title={`Attempt ${index + 1}: ${value}%`}
                  style={{
                    width: 18,
                    height,
                    borderRadius: 6,
                    background: 'linear-gradient(180deg, #6ad8ff 0%, #2e8bff 100%)',
                    border: '1px solid rgba(123, 199, 255, 0.35)',
                  }}
                />
              )
            })}
          </div>
        </>
      ) : null}
    </div>
  )
}
