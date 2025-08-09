import { applyMode, Mode } from '@cloudscape-design/global-styles'

// Apply light mode for a clean, professional look
applyMode(Mode.Light)

// Custom theme configuration with light mode colors
export const customTheme = {
  // Color mapping - light mode palette
  colors: {
    // Primary colors - AWS blue theme
    primary: '#0073bb',
    primaryDark: '#005a9f',
    
    // Secondary colors
    secondary: '#7c3aed',
    accent: '#0073bb',
    
    // Status colors - accessible light mode colors
    success: '#037f0c',
    warning: '#b7791f',
    error: '#d13212',
    
    // Background colors - light theme
    backgroundPrimary: '#ffffff',
    backgroundSecondary: '#f9f9f9',
    backgroundTertiary: '#f1f1f1',
    
    // Text colors - light theme
    textPrimary: '#16191f',
    textSecondary: '#5f6b7a',
    textMuted: '#879596',
    
    // Border colors
    border: '#d5dbdb'
  },
  
  // Spacing system - same as before
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  
  // Typography - clean, professional fonts
  typography: {
    fontFamily: "'Amazon Ember', 'Helvetica Neue', Roboto, Arial, sans-serif",
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      xxl: '1.5rem',
      xxxl: '1.875rem'
    }
  },
  
  // Border radius - modern, subtle
  borderRadius: {
    sm: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem'
  },
  
  // Shadows - light, subtle shadows
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    lg: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    xl: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
  },
  
  // Layout dimensions - same as before
  layout: {
    sidebarWidth: '280px',
    sidebarWidthTablet: '240px',
    headerHeight: '80px',
    contentMaxWidth: '1200px'
  }
}

export default customTheme
