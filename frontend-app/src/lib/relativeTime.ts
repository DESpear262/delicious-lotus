/**
 * Format a date as a relative time string
 *
 * Rules:
 * - < 10 seconds: "Just now"
 * - 10-59 seconds: "X sec ago" (whole number)
 * - 1-59 minutes: "X.X min ago" (1 decimal)
 * - 1-23 hours: "X.X hours ago" (1 decimal)
 * - >= 1 day: "X.X days ago" (1 decimal)
 */
export function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  // Just now (< 10 seconds)
  if (diffInSeconds < 10) {
    return 'Just now';
  }

  // Seconds (10-59 seconds)
  if (diffInSeconds < 60) {
    return `${diffInSeconds} sec ago`;
  }

  // Minutes (1-59 minutes)
  const diffInMinutes = diffInSeconds / 60;
  if (diffInMinutes < 60) {
    return `${diffInMinutes.toFixed(1)} min ago`;
  }

  // Hours (1-23 hours)
  const diffInHours = diffInMinutes / 60;
  if (diffInHours < 24) {
    return `${diffInHours.toFixed(1)} hours ago`;
  }

  // Days (>= 1 day)
  const diffInDays = diffInHours / 24;
  return `${diffInDays.toFixed(1)} days ago`;
}
