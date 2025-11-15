import styles from './History.module.css';

/**
 * History Page Component
 *
 * Placeholder for the generation history page.
 * Full implementation will be added in PR-F011.
 */
export function History() {
  return (
    <div className={styles.historyPage}>
      <h1 className={styles.historyTitle}>Generation History</h1>
      <p className={styles.historyDescription}>
        Your video generation history will appear here.
      </p>
      <p className={styles.historyNote}>
        Full history implementation coming in PR-F011
      </p>
    </div>
  );
}
