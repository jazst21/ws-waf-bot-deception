import React from 'react'
import { Spinner, Box } from '@cloudscape-design/components'

function LoadingSpinner({ size = 'normal', text = 'Loading...' }) {
  return (
    <Box textAlign="center" padding="l">
      <Spinner size={size} />
      {text && (
        <Box variant="p" color="text-status-info" margin={{ top: 's' }}>
          {text}
        </Box>
      )}
    </Box>
  )
}

export default LoadingSpinner
