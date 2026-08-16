const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Runs step 3-4 of the flow: once the user confirms they want the
 * requirement improved, send the original text + the issues they're
 * addressing (plus any extra notes they typed) and get back the enhanced
 * requirement, a new score, and a summary of what changed.
 *
 * @param {{ requirementText: string, issues: object[], userNotes?: string }} input
 */
export async function enhanceRequirement({ requirementText, issues, userNotes }) {
  let res
  try {
    res = await fetch(`${API_BASE}/api/enhance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requirement_text: requirementText,
        issues,
        user_notes: userNotes || null,
      }),
    })
  } catch {
    throw new Error('Could not reach the server. Check your connection and try again.')
  }

  const data = await res.json().catch(() => null)
  if (!res.ok) {
    throw new Error(data?.detail || 'Something went wrong enhancing the requirement.')
  }
  return data
}
