import { useState } from 'react'
import RequirementInput from './components/RequirementInput.jsx'
import ScoreGauge from './components/ScoreGauge.jsx'
import IssuesList from './components/IssuesList.jsx'
import SuggestedRewrite from './components/SuggestedRewrite.jsx'
import { analyzeRequirement } from './api/analyzeRequirement.js'
import { enhanceRequirement } from './api/enhanceRequirement.js'

// Flow stages:
// input        -> user is writing/pasting the requirement
// diagnosed    -> analysis came back: score + issues shown, waiting on user confirmation
// enhanced     -> enhancement came back: rewritten requirement + new score
const STAGE = { INPUT: 'input', DIAGNOSED: 'diagnosed', ENHANCED: 'enhanced' }

export default function App() {
  const [stage, setStage] = useState(STAGE.INPUT)
  const [originalText, setOriginalText] = useState('')
  const [analysis, setAnalysis] = useState(null) // { score, issues, suggested_rewrite }
  const [selectedIssueIdx, setSelectedIssueIdx] = useState(new Set())
  const [userNotes, setUserNotes] = useState('')
  const [enhancement, setEnhancement] = useState(null) // { enhanced_requirement, new_score, summary_of_changes }
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleAnalyze({ text, file }) {
    setError(null)
    setLoading(true)
    try {
      const result = await analyzeRequirement({ text, file })
      setOriginalText(text || '(from uploaded file)')
      // if it came from a file we don't have the raw text client-side for
      // re-use in step 3, so ask the backend result to stand in — but we
      // still keep the pasted-text path exact.
      if (file) setOriginalText(await file.text())
      setAnalysis(result)
      setSelectedIssueIdx(new Set(result.issues.map((_, i) => i))) // default: address everything
      setStage(STAGE.DIAGNOSED)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleConfirmEnhance() {
    setError(null)
    setLoading(true)
    try {
      const issuesToFix = analysis.issues.filter((_, i) => selectedIssueIdx.has(i))
      const result = await enhanceRequirement({
        requirementText: originalText,
        issues: issuesToFix,
        userNotes,
      })
      setEnhancement(result)
      setStage(STAGE.ENHANCED)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setStage(STAGE.INPUT)
    setOriginalText('')
    setAnalysis(null)
    setSelectedIssueIdx(new Set())
    setUserNotes('')
    setEnhancement(null)
    setError(null)
  }

  return (
    <div className="page">
      <header className="masthead">
        <span className="masthead__eyebrow">Requirement Diagnostics</span>
        <h1 className="masthead__title">AI Requirement Doctor</h1>
        <p className="masthead__sub">
          Paste a requirement. Get a diagnosis. Confirm a treatment. Walk away with a
          requirement that actually holds up under test.
        </p>
      </header>

      {error && (
        <div className="alert" role="alert">
          <strong>Something went wrong.</strong> {error}
        </div>
      )}

      {stage === STAGE.INPUT && (
        <RequirementInput onAnalyze={handleAnalyze} loading={loading} />
      )}

      {stage === STAGE.DIAGNOSED && analysis && (
        <section className="panel">
          <div className="diagnosis-layout">
            <ScoreGauge score={analysis.score} label="Current score" />
            <div className="diagnosis-body">
              <h2 className="panel__title">Diagnosis</h2>
              <p className="panel__lede">
                Select which findings you'd like addressed, add any known specifics, then
                confirm to generate the enhanced requirement.
              </p>
              <IssuesList
                issues={analysis.issues}
                selected={selectedIssueIdx}
                onToggle={(i) => {
                  setSelectedIssueIdx((prev) => {
                    const next = new Set(prev)
                    next.has(i) ? next.delete(i) : next.add(i)
                    return next
                  })
                }}
              />
              <label className="field" htmlFor="user-notes">
                <span className="field__label">
                  Extra context <span className="field__optional">(optional)</span>
                </span>
                <textarea
                  id="user-notes"
                  className="field__textarea field__textarea--compact"
                  placeholder="e.g. we expect 5,000 concurrent users; response target is 1.5s"
                  value={userNotes}
                  onChange={(e) => setUserNotes(e.target.value)}
                  rows={3}
                />
              </label>
              <div className="action-row">
                <button
                  className="btn btn--primary"
                  onClick={handleConfirmEnhance}
                  disabled={loading || selectedIssueIdx.size === 0}
                >
                  {loading ? 'Prescribing improvements…' : 'Confirm & enhance requirement'}
                </button>
                <button className="btn btn--ghost" onClick={handleReset} disabled={loading}>
                  Start over
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {stage === STAGE.ENHANCED && enhancement && analysis && (
        <section className="panel">
          <div className="diagnosis-layout">
            <ScoreGauge
              score={enhancement.new_score}
              label="New score"
              delta={enhancement.new_score - analysis.score}
            />
            <div className="diagnosis-body">
              <h2 className="panel__title">Treatment complete</h2>
              {enhancement.summary_of_changes?.length > 0 && (
                <ul className="change-summary">
                  {enhancement.summary_of_changes.map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              )}
              <SuggestedRewrite text={enhancement.enhanced_requirement} />
              <div className="action-row">
                <button className="btn btn--primary" onClick={handleReset}>
                  Analyze another requirement
                </button>
                <button className="btn btn--ghost" onClick={() => setStage(STAGE.DIAGNOSED)}>
                  Back to diagnosis
                </button>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
