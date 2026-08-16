import { useRef, useState } from 'react'

const MAX_CHARS = 5000

export default function RequirementInput({ onAnalyze, loading }) {
  const [text, setText] = useState('')
  const [fileName, setFileName] = useState(null)
  const [fileObj, setFileObj] = useState(null)
  const fileInputRef = useRef(null)

  const overLimit = text.length > MAX_CHARS
  const hasInput = fileObj ? true : text.trim().length > 0
  const canAnalyze = hasInput && !overLimit && !loading

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setFileObj(file)
    setFileName(file.name)
    setText('')
  }

  function clearFile() {
    setFileObj(null)
    setFileName(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!canAnalyze) return
    onAnalyze({ text: fileObj ? undefined : text, file: fileObj || undefined })
  }

  return (
    <section className="panel">
      <form onSubmit={handleSubmit}>
        <label className="field" htmlFor="requirement-text">
          <span className="field__label">Requirement statement</span>
          <textarea
            id="requirement-text"
            className="field__textarea"
            placeholder='e.g. "The application should load quickly and support many users."'
            rows={7}
            value={text}
            disabled={!!fileObj}
            onChange={(e) => setText(e.target.value)}
          />
        </label>

        <div className="input-footer">
          <div className="upload-row">
            <label className="upload-btn">
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt"
                onChange={handleFileChange}
                hidden
              />
              Upload .txt instead
            </label>
            {fileName && (
              <span className="upload-chip">
                {fileName}
                <button type="button" className="upload-chip__remove" onClick={clearFile} aria-label="Remove file">
                  ×
                </button>
              </span>
            )}
          </div>
          <span className={`char-counter${overLimit ? ' char-counter--over' : ''}`}>
            {text.length} / {MAX_CHARS}
          </span>
        </div>

        {overLimit && (
          <p className="field__error">
            That's over the {MAX_CHARS}-character limit — trim it down before analyzing.
          </p>
        )}

        <button type="submit" className="btn btn--primary btn--wide" disabled={!canAnalyze}>
          {loading ? 'Running diagnosis…' : 'Analyze requirement'}
        </button>
      </form>
    </section>
  )
}
