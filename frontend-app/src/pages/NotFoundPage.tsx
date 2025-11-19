import { Link } from 'react-router';
import { ROUTES } from '../types/routes';
import { AlertCircle, Home } from 'lucide-react';

/**
 * 404 Not Found page with navigation back to home
 */
export default function NotFoundPage() {
  return (
    <div className="min-h-full flex items-center justify-center p-8">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <AlertCircle className="w-20 h-20 text-red-500" />
        </div>

        <div className="space-y-2">
          <h1 className="text-6xl font-bold text-zinc-100">404</h1>
          <h2 className="text-2xl font-semibold text-zinc-300">Page Not Found</h2>
          <p className="text-zinc-500">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <div className="pt-4">
          <Link
            to={ROUTES.HOME}
            className="inline-flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            <Home className="w-5 h-5" />
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
