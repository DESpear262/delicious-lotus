/**
 * Generate a UUID v4
 *
 * Uses crypto.randomUUID() when available (HTTPS/localhost),
 * falls back to Math.random() for HTTP contexts.
 */
export function generateUUID(): string {
  // Try to use crypto.randomUUID if available (requires secure context)
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  // Fallback for non-secure contexts (HTTP)
  // Based on https://stackoverflow.com/a/2117523
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}
