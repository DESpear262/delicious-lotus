import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { PipelineSelection } from './pages/PipelineSelection';
import { AdCreativeForm } from './pages/AdCreativeForm';
import { History } from './pages/History';
import { VideoPreview } from './pages/VideoPreview';
import { GenerationProgress } from './pages/GenerationProgress';
import { NotFound } from './pages/NotFound';
import { ErrorBoundary } from './components/ErrorBoundary';
import { OfflineBanner } from './components/OfflineBanner';
import { NotificationProvider } from './contexts/NotificationContext';
import { useNotification } from './hooks/useNotification';
import {
  initializeGlobalErrorHandler,
  cleanupGlobalErrorHandler,
} from './utils/globalErrorHandler';

/**
 * App Content Component
 * Contains the routing logic and initializes global error handler
 */
function AppContent() {
  const notification = useNotification();

  // Initialize global error handler
  useEffect(() => {
    initializeGlobalErrorHandler(notification);

    return () => {
      cleanupGlobalErrorHandler();
    };
  }, [notification]);

  return (
    <>
      <OfflineBanner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<PipelineSelection />} />
            <Route path="create/ad-creative" element={<AdCreativeForm />} />
            <Route path="history" element={<History />} />
            <Route path="generation/:id" element={<GenerationProgress />} />
            <Route path="preview/:id" element={<VideoPreview />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  );
}

/**
 * App Component
 *
 * Main application component with error handling and notification system.
 * Wraps the entire app with:
 * - ErrorBoundary: Catches React component errors
 * - NotificationProvider: Global toast notification system
 * - OfflineBanner: Network status indicator
 * - Global error handler: Catches unhandled promise rejections
 */
function App() {
  return (
    <ErrorBoundary>
      <NotificationProvider position="top-right" maxToasts={5}>
        <AppContent />
      </NotificationProvider>
    </ErrorBoundary>
  );
}

export default App;
