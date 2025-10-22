/**
 * Main Application Component
 * Handles routing and layout
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { FluentProvider, webLightTheme, webDarkTheme } from '@fluentui/react-components'
import { useState, useEffect } from 'react'
import { AppLayout } from './components/navigation/AppLayout'
import { HomePage } from './pages/HomePage'
import { ChatPage } from './pages/ChatPage'
import { AgentsPage } from './pages/AgentsPage'
import { AgentEditorPage } from './pages/agent-editor/AgentEditorPage'
import './styles/App.css'

/**
 * Main App Component
 */
export const App = () => {
  const [isDark, setIsDark] = useState(false)

  // Detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    setIsDark(mediaQuery.matches)

    const handler = (e: MediaQueryListEvent) => setIsDark(e.matches)
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  const theme = isDark ? webDarkTheme : webLightTheme

  return (
    <FluentProvider theme={theme}>
      <Router>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<HomePage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="chat/:threadId" element={<ChatPage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="agents/:agentId/edit" element={<AgentEditorPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Router>
    </FluentProvider>
  )
}

export default App
