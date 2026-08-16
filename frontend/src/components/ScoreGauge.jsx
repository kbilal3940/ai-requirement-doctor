function bandFor(score) {
  if (score < 40) return { name: 'poor', color: 'var(--critical)' }
  if (score < 70) return { name: 'fair', color: 'var(--important)' }
  return { name: 'healthy', color: 'var(--good)' }
}

export default function ScoreGauge({ score, label, delta }) {
  const band = bandFor(score)
  const circumference = 2 * Math.PI * 52
  const offset = circumference * (1 - score / 100)

  return (
    <div className="gauge">
      <svg className="gauge__ring" viewBox="0 0 120 120" width="150" height="150">
        <circle cx="60" cy="60" r="52" className="gauge__track" />
        <circle
          cx="60"
          cy="60"
          r="52"
          className="gauge__value"
          style={{ stroke: band.color, strokeDasharray: circumference, strokeDashoffset: offset }}
        />
      </svg>
      <div className="gauge__readout">
        <span className="gauge__number">{score}</span>
        <span className="gauge__scale">/100</span>
      </div>
      <span className="gauge__label">{label}</span>
      <span className="gauge__band" style={{ color: band.color }}>
        {band.name}
      </span>
      {typeof delta === 'number' && (
        <span className={`gauge__delta${delta >= 0 ? ' gauge__delta--up' : ' gauge__delta--down'}`}>
          {delta >= 0 ? '▲' : '▼'} {Math.abs(delta)} pts
        </span>
      )}
    </div>
  )
}
