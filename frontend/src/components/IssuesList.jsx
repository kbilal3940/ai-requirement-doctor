const SEVERITY_ORDER = ['critical', 'important', 'minor']
const SEVERITY_META = {
  critical: { dot: '🔴', label: 'Critical' },
  important: { dot: '🟠', label: 'Important' },
  minor: { dot: '🟡', label: 'Minor' },
}

export default function IssuesList({ issues, selected, onToggle }) {
  const grouped = SEVERITY_ORDER.map((severity) => ({
    severity,
    items: issues
      .map((issue, idx) => ({ issue, idx }))
      .filter(({ issue }) => issue.severity === severity),
  })).filter((g) => g.items.length > 0)

  if (issues.length === 0) {
    return <p className="issues-empty">No issues found — this requirement is in good shape.</p>
  }

  return (
    <div className="issues">
      {grouped.map(({ severity, items }) => (
        <div className="issues__group" key={severity}>
          <h3 className="issues__group-title">
            {SEVERITY_META[severity].dot} {SEVERITY_META[severity].label}
            <span className="issues__group-count">{items.length}</span>
          </h3>
          <ul className="issues__list">
            {items.map(({ issue, idx }) => (
              <li className={`issue issue--${severity}`} key={idx}>
                <label className="issue__check">
                  <input
                    type="checkbox"
                    checked={selected.has(idx)}
                    onChange={() => onToggle(idx)}
                  />
                  <div>
                    <span className="issue__title">{issue.title}</span>
                    <p className="issue__explanation">{issue.explanation}</p>
                  </div>
                </label>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
