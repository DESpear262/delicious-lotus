/**
 * Generate a UUID v4
 *
 * Uses the native crypto.randomUUID() API.
 * Requires HTTPS or localhost (secure context).
 */
export function generateUUID(): string {
  return crypto.randomUUID()
}
