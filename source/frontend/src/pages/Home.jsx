import React, { useEffect } from 'react'
import { Container, Header, SpaceBetween, Box, Badge, ColumnLayout, Alert } from '@cloudscape-design/components'
import { useBotStatus } from '../hooks/useBotStatus'
import LoadingSpinner from '../components/LoadingSpinner'

function Home() {
  const { isBot, botMessage, isLoading, checkBotStatus } = useBotStatus()

  useEffect(() => {
    // Check bot status on component mount - PRESERVE same behavior as Vue
    checkBotStatus()
  }, [checkBotStatus])

  return (
    <SpaceBetween direction="vertical" size="l">
      {/* Page Header with Status */}
      <Container>
        <SpaceBetween direction="vertical" size="m">
          <Header variant="h1" description="AWS WAF Bot Control Demonstration">
            Bot Deception Demo
          </Header>
          <Box>
            <Badge 
              color={isBot ? 'red' : 'green'}
            >
              {isLoading ? 'Checking status...' : (botMessage || 'Status unknown')}
            </Badge>
          </Box>
        </SpaceBetween>
      </Container>

      {/* Welcome Section */}
      <Container>
        <SpaceBetween direction="vertical" size="l">
          <Header variant="h2">Welcome to AWS WAF Bot Control Demo</Header>
          <Box>
            <p>This demonstration showcases advanced techniques for detecting bot traffic and implementing deception strategies using AWS WAF Bot Control and related services.</p>
          </Box>

          {/* Demo Overview Cards */}
          <SpaceBetween direction="vertical" size="m">
            <Header variant="h3">Demo Configuration</Header>
            <ColumnLayout columns={3}>
              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Box fontSize="heading-xl" textAlign="center">🕷️</Box>
                  <Header variant="h4">robots.txt Trap</Header>
                  <Box>
                    <p>Displays AI-generated fake websites to bots accessing restricted <code>/private/*</code> paths, powered by Amazon Bedrock.</p>
                  </Box>
                </SpaceBetween>
              </Container>

              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Box fontSize="heading-xl" textAlign="center">⏱️</Box>
                  <Header variant="h4">Timeout Induction</Header>
                  <Box>
                    <p>Routes bot traffic accessing <code>/bot-demo-1</code> with 70% probability to induce timeout responses.</p>
                  </Box>
                </SpaceBetween>
              </Container>

              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Box fontSize="heading-xl" textAlign="center">🤫</Box>
                  <Header variant="h4">Silent Discard</Header>
                  <Box>
                    <p>Silently discards comments from bots on <code>/bot-demo-2</code> while showing success responses.</p>
                  </Box>
                </SpaceBetween>
              </Container>
            </ColumnLayout>
          </SpaceBetween>

          {/* Technology Stack */}
          <SpaceBetween direction="vertical" size="m">
            <Header variant="h3">Technology Stack</Header>
            <SpaceBetween direction="horizontal" size="s">
              <Badge color="blue">AWS WAF</Badge>
              <Badge color="blue">CloudFront</Badge>
              <Badge color="blue">Lambda</Badge>
              <Badge color="blue">Amazon Bedrock</Badge>
              <Badge color="green">React SPA</Badge>
              <Badge color="green">Cloudscape Design</Badge>
              <Badge color="grey">JSON Storage</Badge>
            </SpaceBetween>
          </SpaceBetween>

          {/* Getting Started */}
          <SpaceBetween direction="vertical" size="m">
            <Header variant="h3">Getting Started</Header>
            <Alert type="info" header="Explore the Demos">
              Use the navigation menu to explore different bot deception techniques. Each demo includes detailed information about the implementation and real-time interaction capabilities.
            </Alert>
            <ColumnLayout columns={2}>
              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Header variant="h4">📚 Information Pages</Header>
                  <Box>
                    <p>Learn about each demo's technical implementation, AWS services used, and bot detection strategies.</p>
                  </Box>
                </SpaceBetween>
              </Container>
              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Header variant="h4">🎮 Interactive Demos</Header>
                  <Box>
                    <p>Experience real-time bot detection and deception techniques through interactive demonstrations.</p>
                  </Box>
                </SpaceBetween>
              </Container>
            </ColumnLayout>
          </SpaceBetween>

          {/* Architecture Overview */}
          <SpaceBetween direction="vertical" size="m">
            <Header variant="h3">Architecture Overview</Header>
            <Container>
              <SpaceBetween direction="vertical" size="s">
                <Box>
                  <p><strong>Serverless Architecture:</strong> This demo runs entirely on AWS serverless services for optimal scalability and cost-effectiveness.</p>
                </Box>
                <Box>
                  <p><strong>Frontend:</strong> React SPA with Cloudscape Design System, deployed to S3 and served via CloudFront.</p>
                </Box>
                <Box>
                  <p><strong>Backend:</strong> AWS Lambda functions with Function URLs for API endpoints and bot detection logic.</p>
                </Box>
                <Box>
                  <p><strong>Security:</strong> AWS WAF Bot Control provides intelligent bot detection and traffic filtering.</p>
                </Box>
              </SpaceBetween>
            </Container>
          </SpaceBetween>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  )
}

export default Home
