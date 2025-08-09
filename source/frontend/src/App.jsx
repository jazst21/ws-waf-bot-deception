import React, { useState, useEffect } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { AppLayout } from '@cloudscape-design/components'
import Navigation from './components/Navigation'
import AppRouter from './router/AppRouter'
import NotificationSystem from './components/NotificationSystem'
import ErrorBoundary from './components/ErrorBoundary'
import { useAppStore } from './store/useAppStore'
import './styles/theme.js' // Import theme configuration
import './styles/custom.css' // Import custom styles

function App() {
  const [navigationOpen, setNavigationOpen] = useState(false)
  
  // Initialize app store
  const { checkBotStatus } = useAppStore()

  useEffect(() => {
    // Initialize bot status check on app load (same as Vue version)
    checkBotStatus()
  }, [checkBotStatus])

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div id="app" className="container">
          <AppLayout
            navigation={<Navigation />}
            navigationOpen={navigationOpen}
            onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
            content={<AppRouter />}
            notifications={<NotificationSystem />}
            toolsHide={true}
            navigationHide={false}
            contentType="default"
          />
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
