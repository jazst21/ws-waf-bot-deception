import React from 'react'
import { Container, Header, Box, Button, SpaceBetween } from '@cloudscape-design/components'
import { useNavigate } from 'react-router-dom'

function NotFound() {
  const navigate = useNavigate()

  const handleGoHome = () => {
    navigate('/')
  }

  return (
    <Container>
      <SpaceBetween direction="vertical" size="l">
        <Box textAlign="center">
          <SpaceBetween direction="vertical" size="m">
            <Header variant="h1">404 - Page Not Found</Header>
            <Box fontSize="display-l">🤖</Box>
            <Box>
              <p>The page you're looking for doesn't exist or has been moved.</p>
              <p>This might be a trap for bots, or you may have followed a broken link.</p>
            </Box>
            <Button variant="primary" onClick={handleGoHome}>
              Go to Home
            </Button>
          </SpaceBetween>
        </Box>
      </SpaceBetween>
    </Container>
  )
}

export default NotFound
