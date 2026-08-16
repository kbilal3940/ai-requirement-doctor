const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Runs step 1-2 of the flow: send the requirement (as pasted text or a
 * .txt file) to the backend and get back a score + issue list + a quick
 * suggested rewrite.
 *
 * @param {{ text?: string, file?: File }} input
 */
export async function analyzeRequirement({ text, file }) {
  const form = new FormData()
  if (file) {
    form.append('file', file)
  } else {
    form.append('requirement_text', text ?? '')
  }

  let res
  try {
    res = await fetch(`${API_BASE}/api/analyze`, { method: 'POST', body: form })
  } catch {
    throw new Error('Could not reach the server. Check your connection and try again.')
  }

  const data = await res.json().catch(() => null)
  if (!res.ok) {
    throw new Error(data?.detail || 'Something went wrong analyzing the requirement.')
  }
  return data
}
