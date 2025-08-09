import React from 'react'
import { Alert, Box, Button, SpaceBetween } from '@cloudscape-design/components'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    })
    
    // Log error for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box padding="l">
          <Alert
            type="error"
            header="Something went wrong"
            action={
              <Button onClick={this.handleReload}>
                Reload Page
              </Button>
            }
          >
            <SpaceBetween direction="vertical" size="s">
              <div>
                An unexpected error occurred while rendering this component.
              </div>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <Box variant="code">
                  <details>
                    <summary>Error Details (Development Only)</summary>
                    <pre>{this.state.error.toString()}</pre>
                    <pre>{this.state.errorInfo.componentStack}</pre>
                  </details>
                </Box>
              )}
            </SpaceBetween>
          </Alert>
        </Box>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
