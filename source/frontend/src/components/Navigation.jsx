import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { SideNavigation, Box, SpaceBetween } from '@cloudscape-design/components'

function Navigation() {
  const location = useLocation()
  const navigate = useNavigate()

  // Clean navigation items without icons
  const navigationItems = [
    {
      type: 'link',
      text: 'Home',
      href: '/'
    },
    {
      type: 'divider'
    },
    {
      type: 'section',
      text: 'Bot Demo 1 - Timeout',
      items: [
        {
          type: 'link',
          text: 'Demo 1 Info',
          href: '/bot-demo-1-info'
        },
        {
          type: 'link',
          text: 'Demo 1 Interactive',
          href: '/bot-demo-1'
        }
      ]
    },
    {
      type: 'section',
      text: 'Bot Demo 2 - Silent Discard',
      items: [
        {
          type: 'link',
          text: 'Demo 2 Info',
          href: '/bot-demo-2-info'
        },
        {
          type: 'link',
          text: 'Demo 2 Interactive',
          href: '/bot-demo-2'
        }
      ]
    },
    {
      type: 'section',
      text: 'Flight Booking',
      items: [
        {
          type: 'link',
          text: 'About FlightBooker',
          href: '/pricing-demo-3-info'
        },
        {
          type: 'link',
          text: 'Search Flights',
          href: '/pricing-demo-3'
        }
      ]
    },
    {
      type: 'divider'
    },
    {
      type: 'link',
      text: 'AWS Edge Services',
      href: '/aws-edge-services'
    }
  ]

  const handleFollow = (event) => {
    event.preventDefault()
    const href = event.detail.href
    navigate(href)
  }

  return (
    <SpaceBetween direction="vertical" size="l">
      {/* Logo section - Clean branding */}
      <Box padding="l">
        <div className="logo">
          <h2>Bot Deception</h2>
          <p>AWS WAF Demo</p>
        </div>
      </Box>

      {/* Navigation menu - Clean without header */}
      <SideNavigation
        activeHref={location.pathname}
        items={navigationItems}
        onFollow={handleFollow}
      />
    </SpaceBetween>
  )
}

export default Navigation
