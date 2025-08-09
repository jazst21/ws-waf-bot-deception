import axios from 'axios'

// Create axios instance with default config - PRESERVE EXACT config from Vue
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - PRESERVE same logging and behavior
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - PRESERVE same logging and error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

// API methods - PRESERVE EXACT same methods and endpoints as Vue
const api = {
  // Health and status
  getStatus() {
    return apiClient.get('/status')
  },
  
  // Bot Demo 1 - Timeout induction
  getBotDemo1() {
    return apiClient.get('/bot-demo-1')
  },
  
  getBotDemo1Info() {
    return apiClient.get('/info/bot-demo-1')
  },
  
  // Bot Demo 2 - Silent discard
  getBotDemo2Comments() {
    return apiClient.get('/bot-demo-2/comments')
  },
  
  postBotDemo2Comment(commentData) {
    return apiClient.post('/bot-demo-2/comments', commentData)
  },
  
  getBotDemo2Info() {
    return apiClient.get('/info/bot-demo-2')
  },
  
  // Bot Demo 3 - Price manipulation
  getBotDemo3Flights() {
    return apiClient.get('/bot-demo-3/flights')
  },
  
  getBotDemo3Info() {
    return apiClient.get('/info/bot-demo-3')
  },
  
  // Utility
  getRobotsTxt() {
    return apiClient.get('/robots.txt')
  }
}

export default api
