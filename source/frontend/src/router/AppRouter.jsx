import React, { useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'

// Import page components (will be created in Phase 4)
import Home from '../pages/Home'
import BotDemo1Info from '../pages/BotDemo1Info'
import BotDemo1 from '../pages/BotDemo1'
import BotDemo2Info from '../pages/BotDemo2Info'
import BotDemo2 from '../pages/BotDemo2'
import BotDemo3Info from '../pages/BotDemo3Info'
import BotDemo3 from '../pages/BotDemo3'
import AwsEdgeServices from '../pages/AwsEdgeServices'
import NotFound from '../pages/NotFound'

// Route configuration - PRESERVE EXACT ROUTES from Vue version
const routes = [
  {
    path: '/',
    element: <Home />,
    title: 'Bot Deception Demo'
  },
  {
    path: '/bot-demo-1-info',
    element: <BotDemo1Info />,
    title: 'Bot Demo 1 Info'
  },
  {
    path: '/bot-demo-1',
    element: <BotDemo1 />,
    title: 'Bot Demo 1'
  },
  {
    path: '/bot-demo-2-info',
    element: <BotDemo2Info />,
    title: 'Bot Demo 2 Info'
  },
  {
    path: '/bot-demo-2',
    element: <BotDemo2 />,
    title: 'Bot Demo 2'
  },
  {
    path: '/pricing-demo-3-info',
    element: <BotDemo3Info />,
    title: 'FlightBooker Info'
  },
  {
    path: '/pricing-demo-3',
    element: <BotDemo3 />,
    title: 'FlightBooker'
  },
  {
    path: '/aws-edge-services',
    element: <AwsEdgeServices />,
    title: 'AWS Edge Services'
  },
  {
    path: '*',
    element: <NotFound />,
    title: 'Page Not Found'
  }
]

// Title management component - PRESERVE same title behavior as Vue
function TitleManager() {
  const location = useLocation()

  useEffect(() => {
    const currentRoute = routes.find(route => {
      if (route.path === '*') return false
      if (route.path === '/') return location.pathname === '/'
      return location.pathname === route.path
    })

    const title = currentRoute ? currentRoute.title : 'Page Not Found'
    document.title = `${title} - Bot Deception Demo`
  }, [location])

  return null
}

// Scroll behavior component - PRESERVE same scroll behavior as Vue
function ScrollManager() {
  const location = useLocation()

  useEffect(() => {
    // Scroll to top on route change (same as Vue scrollBehavior)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [location])

  return null
}

function AppRouter() {
  return (
    <>
      <TitleManager />
      <ScrollManager />
      <Routes>
        {routes.map((route, index) => (
          <Route
            key={index}
            path={route.path}
            element={route.element}
          />
        ))}
      </Routes>
    </>
  )
}

export default AppRouter
