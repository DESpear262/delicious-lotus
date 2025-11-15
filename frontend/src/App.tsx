import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { PipelineSelection } from './pages/PipelineSelection';
import { History } from './pages/History';
import { VideoPreview } from './pages/VideoPreview';
import { GenerationProgress } from './pages/GenerationProgress';
import { NotFound } from './pages/NotFound';

/**
 * App Component
 *
 * Main application component with React Router v7 configuration.
 * Routes are wrapped in MainLayout for consistent header/footer.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<PipelineSelection />} />
          <Route path="history" element={<History />} />
          <Route path="generation/:id" element={<GenerationProgress />} />
          <Route path="preview/:id" element={<VideoPreview />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
