import './App.css'
import { AppRoutes } from './routes/AppRoutes'
import { ErrorBoundary } from './components/ErrorBoundary'
import { StoreProvider } from './contexts/StoreContext'
import { WebSocketProvider } from './contexts/WebSocketContext'

function App() {
  return (
    <ErrorBoundary>
      <StoreProvider>
        <WebSocketProvider>
          <AppRoutes />
        </WebSocketProvider>
      </StoreProvider>
    </ErrorBoundary>
  )
}

export default App
