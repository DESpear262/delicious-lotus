import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ad-generator/ui/Button';


/**
 * NotFound Page Component
 *
 * 404 error page displayed when a user navigates to an invalid route.
 * Provides options to navigate back or return to the home page.
 */
export function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-8 bg-background">
      <div className="text-center max-w-lg">
        <h1 className="text-9xl font-bold text-primary mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-foreground mb-4">Page Not Found</h2>
        <p className="text-lg text-muted-foreground mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex gap-4 justify-center">
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
