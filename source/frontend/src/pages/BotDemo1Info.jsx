import React from 'react'
import { Container, Header, SpaceBetween, Box, Grid, Button, ColumnLayout } from '@cloudscape-design/components'
import { useNavigate } from 'react-router-dom'

function BotDemo1Info() {
  const navigate = useNavigate()

  return (
    <SpaceBetween direction="vertical" size="l">
      {/* Page Header */}
      <Container>
        <SpaceBetween direction="vertical" size="m">
          <Header variant="h1" description="Information">
            Bot Demo 1: Timeout Induction
          </Header>
        </SpaceBetween>
      </Container>

      {/* Overview */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h2">Overview</Header>
          <Box>
            <p>This demo showcases how to waste bot resources by redirecting them to unreachable endpoints, causing timeouts and discouraging further scraping attempts.</p>
          </Box>

          {/* Responsive Explanation Cards */}
          <ColumnLayout columns={3} variant="text-grid">
            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h3">🎯 Objective</Header>
                <Box>
                  <ul>
                    <li>Waste bot computational resources</li>
                    <li>Increase bot operation costs</li>
                    <li>Discourage persistent scraping</li>
                    <li>Maintain normal user experience</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h3">⚙️ Technical Implementation</Header>
                <Box>
                  <ul>
                    <li>CloudFront Function detects bot traffic</li>
                    <li>70% probability redirect to timeout ALB</li>
                    <li>Unreachable backend causes 30s timeout</li>
                    <li>Normal users access content directly</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h3">📊 Expected Results</Header>
                <Box>
                  <ul>
                    <li>Bots experience frequent timeouts</li>
                    <li>Reduced bot crawling efficiency</li>
                    <li>Higher operational costs for attackers</li>
                    <li>Zero impact on legitimate users</li>
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
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-info">70%</Box>
                <Box fontSize="body-s" color="text-body-secondary">Redirect Probability</Box>
              </SpaceBetween>
            </Container>
            <Container>
              <SpaceBetween direction="vertical" size="xs" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-info">30s</Box>
                <Box fontSize="body-s" color="text-body-secondary">Timeout Duration</Box>
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
                  <Header variant="h4">Request Analysis</Header>
                </SpaceBetween>
                <Box>
                  <p>AWS WAF analyzes incoming requests and identifies bot traffic using machine learning and behavioral analysis.</p>
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
                  <Header variant="h4">Header Injection</Header>
                </SpaceBetween>
                <Box>
                  <p>WAF adds the <code>x-amzn-waf-targeted-bot-detected: true</code> header to requests identified as bot traffic.</p>
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
                  <Header variant="h4">CloudFront Function</Header>
                </SpaceBetween>
                <Box>
                  <p>CloudFront Function checks for the bot header and randomly redirects 70% of bot requests to an unreachable ALB.</p>
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
                  <Header variant="h4">Timeout Induction</Header>
                </SpaceBetween>
                <Box>
                  <p>The unreachable ALB causes a 30-second timeout, wasting bot resources while normal users access content directly.</p>
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
            <p>Click the button below to experience the timeout induction demo. The behavior will differ based on whether you're detected as a bot or legitimate user.</p>
          </Box>
          <SpaceBetween direction="horizontal" size="m">
            <Button variant="primary" onClick={() => navigate('/bot-demo-1')}>
              Start Demo 1
            </Button>
            <Button onClick={() => navigate('/bot-demo-2-info')}>
              Next: Demo 2 Info
            </Button>
            <Button variant="link" onClick={() => navigate('/')}>
              Back to Home
            </Button>
          </SpaceBetween>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  )
}

export default BotDemo1Info
