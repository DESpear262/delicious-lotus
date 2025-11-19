import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { enableMapSet } from 'immer'
import { ThemeProvider } from './contexts/ThemeContext'
import './index.css'
import App from './App.tsx'

// Enable Immer support for Map and Set
enableMapSet()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="chronos-ui-theme">
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
)
