import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import styles from './NotFound.module.css';

/**
 * NotFound Page Component
 *
 * 404 error page displayed when a user navigates to an invalid route.
 * Provides options to navigate back or return to the home page.
 */
export function NotFound() {
  const navigate = useNavigate();

  return (
    <div className={styles.notFoundPage}>
      <div className={styles.notFoundContent}>
        <h1 className={styles.notFoundTitle}>404</h1>
        <h2 className={styles.notFoundSubtitle}>Page Not Found</h2>
        <p className={styles.notFoundMessage}>
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className={styles.notFoundActions}>
          <Button
            variant="primary"
            onClick={() => navigate('/')}
          >
            Go Home
          </Button>
          <Button
            variant="secondary"
            onClick={() => navigate(-1)}
          >
            Go Back
          </Button>
        </div>
      </div>
    </div>
  );
}
