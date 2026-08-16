import { useState } from 'react'

export default function SuggestedRewrite({ text }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      // Clipboard API unavailable — silently ignore, box remains selectable.
    }
  }

  return (
    <div className="rewrite-box">
      <div className="rewrite-box__header">
        <span className="rewrite-box__label">Enhanced requirement</span>
        <button type="button" className="btn btn--small" onClick={handleCopy}>
          {copied ? 'Copied ✓' : 'Copy'}
        </button>
      </div>
      <p className="rewrite-box__text">{text}</p>
    </div>
  )
}
