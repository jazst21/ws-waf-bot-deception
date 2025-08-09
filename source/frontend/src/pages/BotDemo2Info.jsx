import React from 'react'
import { Container, Header, SpaceBetween, Box, Button, ColumnLayout } from '@cloudscape-design/components'
import { useNavigate } from 'react-router-dom'

function BotDemo2Info() {
  const navigate = useNavigate()

  return (
    <SpaceBetween direction="vertical" size="l">
      {/* Page Header */}
      <Container>
        <SpaceBetween direction="vertical" size="m">
          <Header variant="h1" description="Silent Discard Bot Protection Technique">
            Bot Demo 2: Silent Discard
          </Header>
        </SpaceBetween>
      </Container>

      {/* Overview */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h2">Overview</Header>
          <Box>
            <p>This demo demonstrates how to silently discard bot-generated content while making the bot believe its actions were successful, effectively wasting bot resources and preventing spam.</p>
          </Box>

          {/* Responsive Explanation Cards */}
          <ColumnLayout columns={3} variant="text-grid">
            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Box fontSize="heading-xl" textAlign="center">🎯</Box>
                <Header variant="h4">Objective</Header>
                <Box>
                  <ul>
                    <li>Prevent bot-generated spam</li>
                    <li>Deceive bots into thinking they succeeded</li>
                    <li>Maintain clean user experience</li>
                    <li>Reduce bot motivation to continue</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Box fontSize="heading-xl" textAlign="center">⚙️</Box>
                <Header variant="h4">Technical Implementation</Header>
                <Box>
                  <ul>
                    <li>Server detects bot via WAF headers</li>
                    <li>Bot comments marked as "silent_discard"</li>
                    <li>Success response sent to bot</li>
                    <li>Comments hidden from public view</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Box fontSize="heading-xl" textAlign="center">📊</Box>
                <Header variant="h4">Expected Results</Header>
                <Box>
                  <ul>
                    <li>Zero spam in public comments</li>
                    <li>Bots believe they're successful</li>
                    <li>Continued bot engagement (wasting resources)</li>
                    <li>Clean experience for real users</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>
          </ColumnLayout>
        </SpaceBetween>
      </Container>

      {/* Configuration Details */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h2">Configuration Details</Header>
          <ColumnLayout columns={4} variant="text-grid">
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-info">100%</Box>
                <Box fontSize="body-s" color="text-body-secondary">Success Response Rate</Box>
              </SpaceBetween>
            </Container>
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-error">0%</Box>
                <Box fontSize="body-s" color="text-body-secondary">Bot Reviews Stored</Box>
              </SpaceBetween>
            </Container>
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-success">0ms</Box>
                <Box fontSize="body-s" color="text-body-secondary">User Impact</Box>
              </SpaceBetween>
            </Container>
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-success">100%</Box>
                <Box fontSize="body-s" color="text-body-secondary">Bot Detection Rate</Box>
              </SpaceBetween>
            </Container>
          </ColumnLayout>
        </SpaceBetween>
      </Container>

      {/* How It Works */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h2">How It Works</Header>
          
          <SpaceBetween direction="vertical" size="m">
            {/* Step 1 */}
            <Container>
              <SpaceBetween direction="vertical" size="xs">
                <SpaceBetween direction="horizontal" size="m" alignItems="center">
                  <Box>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      backgroundColor: '#0073bb',
                      color: 'white',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      fontSize: '1.125rem'
                    }}>
                      1
                    </div>
                  </Box>
                  <Header variant="h4">Bot Detection</Header>
                </SpaceBetween>
                <Box>
                  <p>AWS WAF analyzes incoming review submissions and identifies bot traffic using machine learning and behavioral analysis.</p>
                </Box>
              </SpaceBetween>
            </Container>

            {/* Step 2 */}
            <Container>
              <SpaceBetween direction="vertical" size="xs">
                <SpaceBetween direction="horizontal" size="m" alignItems="center">
                  <Box>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      backgroundColor: '#0073bb',
                      color: 'white',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      fontSize: '1.125rem'
                    }}>
                      2
                    </div>
                  </Box>
                  <Header variant="h4">Success Response</Header>
                </SpaceBetween>
                <Box>
                  <p>Lambda function returns HTTP 200 with "Review submitted successfully!" message to make bots believe they succeeded.</p>
                </Box>
              </SpaceBetween>
            </Container>

            {/* Step 3 */}
            <Container>
              <SpaceBetween direction="vertical" size="xs">
                <SpaceBetween direction="horizontal" size="m" alignItems="center">
                  <Box>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      backgroundColor: '#0073bb',
                      color: 'white',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      fontSize: '1.125rem'
                    }}>
                      3
                    </div>
                  </Box>
                  <Header variant="h4">Silent Discard</Header>
                </SpaceBetween>
                <Box>
                  <p>Bot reviews are never stored in the database, while legitimate user reviews are processed and displayed normally.</p>
                </Box>
              </SpaceBetween>
            </Container>

            {/* Step 4 */}
            <Container>
              <SpaceBetween direction="vertical" size="xs">
                <SpaceBetween direction="horizontal" size="m" alignItems="center">
                  <Box>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      backgroundColor: '#0073bb',
                      color: 'white',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      fontSize: '1.125rem'
                    }}>
                      4
                    </div>
                  </Box>
                  <Header variant="h4">Resource Waste</Header>
                </SpaceBetween>
                <Box>
                  <p>Bots continue submitting fake reviews believing they're successful, wasting their resources while keeping the platform clean.</p>
                </Box>
              </SpaceBetween>
            </Container>
          </SpaceBetween>
        </SpaceBetween>
      </Container>

      {/* Next Steps */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h2">Ready to Test?</Header>
          <Box>
            <p>Try the interactive hotel review platform to see how the silent discard mechanism works in practice.</p>
          </Box>
          <SpaceBetween direction="horizontal" size="m">
            <Button variant="primary" onClick={() => navigate('/bot-demo-2')}>
              Start Demo 2
            </Button>
            <Button onClick={() => navigate('/bot-demo-3-info')}>
              Next: Demo 3 Info
            </Button>
            <Button variant="link" onClick={() => navigate('/bot-demo-1-info')}>
              Back: Demo 1 Info
            </Button>
          </SpaceBetween>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  )
}

export default BotDemo2Info
