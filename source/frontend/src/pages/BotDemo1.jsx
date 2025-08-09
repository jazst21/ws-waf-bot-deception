import React, { useEffect, useState } from 'react'
import { Container, Header, SpaceBetween, Button, Box, Alert, Grid, Badge } from '@cloudscape-design/components'
import { useApi } from '../hooks/useApi'
import { useBotStatus } from '../hooks/useBotStatus'
import LoadingSpinner from '../components/LoadingSpinner'

function BotDemo1() {
  const [demoData, setDemoData] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const [demoMessage, setDemoMessage] = useState('Timeout Induction Demo')
  const { getBotDemo1, loading } = useApi()
  const { isBot, botMessage } = useBotStatus()

  useEffect(() => {
    // Set demo message based on bot status
    if (isBot) {
      setDemoMessage('Bot Traffic Detected - Timeout Induction Active')
    } else {
      setDemoMessage('Normal User - Direct Access Granted')
    }
  }, [isBot])

  const handleRunDemo = async () => {
    try {
      setIsRunning(true)
      const response = await getBotDemo1()
      setDemoData(response.data)
    } catch (error) {
      console.error('Demo failed:', error)
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <SpaceBetween direction="vertical" size="l">
      {/* Page Header */}
      <Container>
        <SpaceBetween direction="vertical" size="m">
          <Header variant="h1">Bot Demo 1: Timeout Induction</Header>
          <Badge color={isBot ? 'red' : 'green'}>
            {isBot ? 'Bot Detected' : 'Normal User'}
          </Badge>
        </SpaceBetween>
      </Container>

      {/* Demo Message */}
      <Container>
        <Header variant="h2">{demoMessage}</Header>
      </Container>

      {/* How This Demo Works */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h3">How This Demo Works</Header>
          <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h4">For Normal Users</Header>
                <Box>
                  <ul>
                    <li>Direct access to this page</li>
                    <li>Fast response time</li>
                    <li>Normal user experience</li>
                    <li>No redirects or delays</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h4">For Bots</Header>
                <Box>
                  <ul>
                    <li>70% chance of redirect to timeout ALB</li>
                    <li>Unreachable backend causes timeout</li>
                    <li>Wastes bot resources and time</li>
                    <li>Discourages further scraping</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>
          </Grid>
        </SpaceBetween>
      </Container>

      {/* Bot-specific Information */}
      {isBot && (
        <Container>
          <Alert type="warning" header="🤖 Bot Behavior Simulation">
            <SpaceBetween direction="vertical" size="s">
              <Box>
                <p>As a bot, you have a 70% chance of being redirected to a timeout ALB when accessing this page. The CloudFront function detects bot traffic and redirects it to an unreachable endpoint.</p>
              </Box>
              <Box>
                <p><strong>In production:</strong> Most bot requests to this endpoint would result in timeouts, effectively wasting the bot's time and resources.</p>
              </Box>
              <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
                <Box>
                  <strong>Redirect Probability:</strong> 70%
                </Box>
                <Box>
                  <strong>Expected Outcome:</strong> Connection Timeout
                </Box>
              </Grid>
            </SpaceBetween>
          </Alert>
        </Container>
      )}

      {/* Normal User Information */}
      {!isBot && (
        <Container>
          <Alert type="success" header="✅ Normal User Experience">
            <SpaceBetween direction="vertical" size="s">
              <Box>
                <p>As a legitimate user, you have direct access to this content without any redirects or delays. The system recognizes your traffic as normal and provides the best possible experience.</p>
              </Box>
              <Box>
                <p><strong>Benefits:</strong> Fast loading times, direct access, no interference from bot protection mechanisms.</p>
              </Box>
            </SpaceBetween>
          </Alert>
        </Container>
      )}

      {/* Demo Controls */}
      <Container>
        <SpaceBetween direction="vertical" size="m">
          <Header variant="h3">Test the Demo</Header>
          <Box>
            <p>Click the button below to simulate accessing a protected endpoint. The behavior will differ based on your traffic classification.</p>
          </Box>
          <Button 
            variant="primary" 
            onClick={handleRunDemo}
            loading={isRunning || loading}
          >
            {isBot ? 'Simulate Bot Request (May Timeout)' : 'Access Protected Content'}
          </Button>
        </SpaceBetween>
      </Container>

      {/* Demo Results */}
      {demoData && (
        <Container>
          <SpaceBetween direction="vertical" size="m">
            <Header variant="h3">Demo Results</Header>
            <Alert type="info" header="Response Data">
              <Box variant="code">
                <pre>{JSON.stringify(demoData, null, 2)}</pre>
              </Box>
            </Alert>
          </SpaceBetween>
        </Container>
      )}

      {/* Technical Details */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h3">Technical Implementation</Header>
          <Grid gridDefinition={[{ colspan: 4 }, { colspan: 4 }, { colspan: 4 }]}>
            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h4">AWS WAF</Header>
                <Box>
                  <p>Analyzes request patterns and identifies bot traffic using machine learning algorithms.</p>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h4">CloudFront Function</Header>
                <Box>
                  <p>Processes WAF headers and randomly redirects 70% of bot traffic to timeout endpoints.</p>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h4">Timeout ALB</Header>
                <Box>
                  <p>Unreachable Application Load Balancer that causes 30-second timeouts for bot requests.</p>
                </Box>
              </SpaceBetween>
            </Container>
          </Grid>
        </SpaceBetween>
      </Container>

      {/* Performance Impact */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h3">Performance Impact</Header>
          <Grid gridDefinition={[{ colspan: 3 }, { colspan: 3 }, { colspan: 3 }, { colspan: 3 }]}>
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-success">0ms</Box>
                <Box fontSize="body-s" color="text-body-secondary">User Latency</Box>
              </SpaceBetween>
            </Container>
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-error">30s</Box>
                <Box fontSize="body-s" color="text-body-secondary">Bot Timeout</Box>
              </SpaceBetween>
            </Container>
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-info">70%</Box>
                <Box fontSize="body-s" color="text-body-secondary">Bot Redirect Rate</Box>
              </SpaceBetween>
            </Container>
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-success">100%</Box>
                <Box fontSize="body-s" color="text-body-secondary">User Success Rate</Box>
              </SpaceBetween>
            </Container>
          </Grid>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  )
}

export default BotDemo1
