import React from 'react'
import { Container, Header, SpaceBetween, Box, Button, ColumnLayout } from '@cloudscape-design/components'
import { useNavigate } from 'react-router-dom'

function BotDemo3Info() {
  const navigate = useNavigate()

  return (
    <SpaceBetween direction="vertical" size="l">
      {/* Page Header */}
      <Container>
        <SpaceBetween direction="vertical" size="m">
          <Header variant="h1" description="Information">
            Bot Demo 3: Price Manipulation
          </Header>
        </SpaceBetween>
      </Container>

      {/* Overview */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h2">Overview</Header>
          <Box>
            <p>This demo shows how to protect pricing strategies by showing inflated prices to bots while offering competitive discounts to legitimate users.</p>
          </Box>

          {/* Responsive Explanation Cards */}
          <ColumnLayout columns={3} variant="text-grid">
            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h3">🎯 Objective</Header>
                <Box>
                  <ul>
                    <li>Protect competitive pricing</li>
                    <li>Prevent price scraping</li>
                    <li>Reward legitimate customers</li>
                    <li>Discourage bot-driven competition</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h3">⚙️ Technical Implementation</Header>
                <Box>
                  <ul>
                    <li>Dynamic pricing based on bot detection</li>
                    <li>Bots see inflated prices (+30%)</li>
                    <li>Users see discounted prices (-25%)</li>
                    <li>Real-time price adjustment</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Container>

            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h3">📊 Expected Results</Header>
                <Box>
                  <ul>
                    <li>Protected pricing intelligence</li>
                    <li>Reduced competitive scraping</li>
                    <li>Better user experience</li>
                    <li>Maintained profit margins</li>
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
          <Header variant="h2">Pricing Strategy</Header>
          <ColumnLayout columns={2} variant="text-grid">
            <Container>
              <SpaceBetween direction="vertical" size="s" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-error">+30%</Box>
                <Box fontSize="body-s" color="text-body-secondary">Bot Price Inflation</Box>
                <Box fontSize="body-s">Bots see inflated prices to protect competitive intelligence</Box>
              </SpaceBetween>
            </Container>
            <Container>
              <SpaceBetween direction="vertical" size="s" alignItems="center">
                <Box fontSize="heading-xl" fontWeight="bold" color="text-status-success">-25%</Box>
                <Box fontSize="body-s" color="text-body-secondary">User Discount</Box>
                <Box fontSize="body-s">Legitimate users receive competitive pricing</Box>
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
                  <Header variant="h4">Traffic Classification</Header>
                </SpaceBetween>
                <Box>
                  <p>AWS WAF analyzes incoming requests and classifies traffic as bot or legitimate user based on behavioral patterns.</p>
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
                  <Header variant="h4">Dynamic Price Calculation</Header>
                </SpaceBetween>
                <Box>
                  <p>The backend API adjusts prices in real-time based on the traffic classification headers from WAF.</p>
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
                  <Header variant="h4">Price Differentiation</Header>
                </SpaceBetween>
                <Box>
                  <p>Bots receive inflated prices (+30%) while legitimate users see discounted competitive prices (-25%).</p>
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
                  <Header variant="h4">Competitive Protection</Header>
                </SpaceBetween>
                <Box>
                  <p>Competitors using bots see misleading pricing data while real customers benefit from better deals and protected pricing intelligence.</p>
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
            <p>Browse flight prices to see how the system shows different pricing based on your traffic classification.</p>
          </Box>
          <SpaceBetween direction="horizontal" size="m">
            <Button variant="primary" onClick={() => navigate('/pricing-demo-3')}>
              Start FlightBooker
            </Button>
            <Button onClick={() => navigate('/aws-edge-services')}>
              AWS Edge Services
            </Button>
            <Button variant="link" onClick={() => navigate('/bot-demo-2-info')}>
              Back: Demo 2 Info
            </Button>
          </SpaceBetween>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  )
}

export default BotDemo3Info
