/**
 * Main Application Component
 * Handles routing and layout
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { FluentProvider, createDarkTheme, BrandVariants } from '@fluentui/react-components'
import { AppLayout } from './components/navigation/AppLayout'
import { HomePage } from './pages/HomePage'
import { ChatPage } from './pages/ChatPage'
import { AgentsPage } from './pages/AgentsPage'
import { AgentEditorPage } from './pages/agent-editor/AgentEditorPage'
import { HowItWorksLanding } from './pages/how-it-works/HowItWorksLanding'
import { ThreadManagementArticle } from './pages/how-it-works/ThreadManagementArticle'
import { AgentDefinitionsArticle } from './pages/how-it-works/AgentDefinitionsArticle'
import './styles/App.css'

/**
 * Agentarium Brand Colors - Blue/Green Theme
 * Primary: Deep ocean blue to cyan gradient
 * Accent: Emerald green to mint green
 */
const agentariumBrand: BrandVariants = {
  10: "#021014",
  20: "#0a1f28",
  30: "#0e2f3f",
  40: "#124056",
  50: "#15516e",
  60: "#186387",
  70: "#1a76a1",
  80: "#1b89bb",
  90: "#2b9dcc",
  100: "#3fb0dd",
  110: "#5bc3e8",
  120: "#7ad4f0",
  130: "#9be3f7",
  140: "#bdeffc",
  150: "#ddf9ff",
  160: "#f0fcff"
};

/**
 * Main App Component
 */
export const App = () => {
  // Create custom dark theme with Agentarium branding (always blue theme)
  const theme = createDarkTheme(agentariumBrand)

  return (
    <FluentProvider theme={theme}>
      <Router>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<HomePage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="chat/:threadId" element={<ChatPage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="agents/new" element={<AgentEditorPage />} />
            <Route path="agents/:agentId/edit" element={<AgentEditorPage />} />
            <Route path="how-it-works">
              <Route index element={<HowItWorksLanding />} />
              <Route path="thread-management" element={<ThreadManagementArticle />} />
              <Route path="agent-definitions" element={<AgentDefinitionsArticle />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Router>
    </FluentProvider>
  )
}

export default App
