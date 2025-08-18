import React, { useEffect, useState } from 'react'
import { Container, Header, SpaceBetween, Button, Box, Alert, Grid } from '@cloudscape-design/components'
import { useApi } from '../hooks/useApi'
import { useBotStatus } from '../hooks/useBotStatus'

// Function to extract meaningful content from HTML without styling
const extractContentFromHTML = (doc) => {
  const result = {
    title: '',
    userProfile: {},
    sections: [],
    isPrivateContent: false
  }

  // Check if this is the private content page
  const title = doc.querySelector('title')?.textContent || ''
  result.title = title
  result.isPrivateContent = title.includes('Private Content') || title.includes('Bot Deception Demo')

  // Extract user profile information from info-item elements
  const infoItems = doc.querySelectorAll('.info-item')
  infoItems.forEach(item => {
    const label = item.querySelector('.info-label')?.textContent?.trim()
    const value = item.querySelector('.info-value')?.textContent?.trim()
    if (label && value) {
      result.userProfile[label.toLowerCase().replace(/\s+/g, '_')] = value
    }
  })

  // Extract section content
  const sections = doc.querySelectorAll('.section')
  sections.forEach(section => {
    const heading = section.querySelector('h2')?.textContent?.trim()
    const content = []
    
    // Get lists from this section
    const lists = section.querySelectorAll('ul li')
    lists.forEach(li => {
      const text = li.textContent?.trim()
      if (text) content.push(text)
    })
    
    // Get paragraphs from this section
    const paragraphs = section.querySelectorAll('p')
    paragraphs.forEach(p => {
      const text = p.textContent?.trim()
      if (text) content.push(text)
    })

    if (heading && content.length > 0) {
      result.sections.push({ heading, content })
    }
  })

  return result
}

function BotDemoPrivate() {
  const [demoData, setDemoData] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const { loading } = useApi()
  const { isBot } = useBotStatus()

  const handleRunDemo = async () => {
    try {
      setIsRunning(true)
      
      // Make actual fetch request to /private endpoint
      const response = await fetch('/private', {
        method: 'GET',
        headers: {
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
      })
      
      const contentType = response.headers.get('content-type')
      const statusCode = response.status
      
      if (contentType && contentType.includes('text/html')) {
        // If it's HTML content, parse and extract meaningful content
        const htmlContent = await response.text()
        
        // Parse HTML to extract content without styling
        const parser = new DOMParser()
        const doc = parser.parseFromString(htmlContent, 'text/html')
        
        // Extract user profile data and other meaningful content
        const extractedContent = extractContentFromHTML(doc)
        
        setDemoData({ 
          type: 'structured',
          content: extractedContent,
          statusCode,
          contentType,
          rawHtml: htmlContent
        })
      } else {
        // If it's not HTML, treat as JSON or plain text
        const textContent = await response.text()
        try {
          const jsonContent = JSON.parse(textContent)
          setDemoData({ 
            type: 'json',
            content: jsonContent,
            statusCode,
            contentType 
          })
        } catch {
          setDemoData({ 
            type: 'text',
            content: textContent,
            statusCode,
            contentType 
          })
        }
      }
    } catch (error) {
      console.error('Demo failed:', error)
      setDemoData({ 
        type: 'error',
        content: error.message,
        statusCode: 0,
        contentType: 'error' 
      })
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <SpaceBetween direction="vertical" size="l">
      {/* Page Header */}
      <Container>
        <SpaceBetween direction="vertical" size="m">
          <Header variant="h1">Bot Demo - Private Access Test</Header>
          <Box>
            <p>This page allows you to test accessing protected endpoints. The behavior will differ based on your traffic classification.</p>
          </Box>
        </SpaceBetween>
      </Container>

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
            <Alert 
              type={demoData.statusCode >= 200 && demoData.statusCode < 300 ? "success" : "warning"} 
              header={`HTTP ${demoData.statusCode} - ${demoData.contentType}`}
            >
              <Box>
                <p>Response from the `/private` endpoint. The content differs based on your traffic classification:</p>
              </Box>
            </Alert>
            
            {demoData.type === 'structured' && (
              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Header variant="h4">Private Content Response</Header>
                  
                  {/* User Profile Section */}
                  {Object.keys(demoData.content.userProfile).length > 0 && (
                    <Container>
                      <SpaceBetween direction="vertical" size="s">
                        <Header variant="h5">👤 User Profile</Header>
                        <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
                          {Object.entries(demoData.content.userProfile).map(([key, value], index) => (
                            <Box key={index}>
                              <div style={{ marginBottom: '8px' }}>
                                <div style={{ 
                                  fontSize: '0.875rem', 
                                  fontWeight: '600', 
                                  color: '#666',
                                  textTransform: 'capitalize',
                                  marginBottom: '4px'
                                }}>
                                  {key.replace(/_/g, ' ')}
                                </div>
                                <div style={{ fontSize: '1rem', color: '#333' }}>
                                  {value}
                                </div>
                              </div>
                            </Box>
                          ))}
                        </Grid>
                      </SpaceBetween>
                    </Container>
                  )}
                  
                  {/* Additional Sections */}
                  {demoData.content.sections.map((section, index) => (
                    <Container key={index}>
                      <SpaceBetween direction="vertical" size="s">
                        <Header variant="h5">{section.heading}</Header>
                        <Box>
                          <ul style={{ marginLeft: '20px' }}>
                            {section.content.map((item, itemIndex) => (
                              <li key={itemIndex} style={{ marginBottom: '8px' }}>
                                {item}
                              </li>
                            ))}
                          </ul>
                        </Box>
                      </SpaceBetween>
                    </Container>
                  ))}
                  
                  {/* Show success message if private content detected */}
                  {demoData.content.isPrivateContent && (
                    <Alert type="success" header="✅ Access Granted">
                      You have successfully accessed protected user profile data from the private content bucket.
                    </Alert>
                  )}
                </SpaceBetween>
              </Container>
            )}
            
            {demoData.type === 'json' && (
              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Header variant="h4">JSON Response</Header>
                  <Box variant="code">
                    <pre style={{ whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(demoData.content, null, 2)}
                    </pre>
                  </Box>
                </SpaceBetween>
              </Container>
            )}
            
            {demoData.type === 'text' && (
              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Header variant="h4">Text Response</Header>
                  <Box>
                    <pre style={{ 
                      whiteSpace: 'pre-wrap', 
                      backgroundColor: '#f9f9f9',
                      padding: '12px',
                      borderRadius: '4px',
                      maxHeight: '300px',
                      overflow: 'auto'
                    }}>
                      {demoData.content}
                    </pre>
                  </Box>
                </SpaceBetween>
              </Container>
            )}
            
            {demoData.type === 'error' && (
              <Container>
                <SpaceBetween direction="vertical" size="s">
                  <Header variant="h4">Error</Header>
                  <Alert type="error" header="Request Failed">
                    <Box>{demoData.content}</Box>
                  </Alert>
                </SpaceBetween>
              </Container>
            )}
          </SpaceBetween>
        </Container>
      )}
    </SpaceBetween>
  )
}

export default BotDemoPrivate
