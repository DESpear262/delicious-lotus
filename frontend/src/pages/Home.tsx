import styles from './Home.module.css';

/**
 * Home Page Component
 *
 * Landing page placeholder for the AI Video Generation Pipeline.
 * Full implementation will be added in PR-F006 (Pipeline Selection).
 */
export function Home() {
  return (
    <div className={styles.homePage}>
      <div className={styles.homeContent}>
        <h1 className={styles.homeTitle}>Delicious Lotus</h1>
        <p className={styles.homeDescription}>
          Welcome to Delicious Lotus
        </p>
        <p className={styles.homeNote}>
          Pipeline selection coming in PR-F006
        </p>
      </div>
    </div>
  );
}
