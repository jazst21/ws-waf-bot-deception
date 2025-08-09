import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import api from '../services/api'

export const useAppStore = create(
  devtools(
    (set, get) => ({
      // State - PRESERVE EXACT state from Pinia store
      isLoading: false,
      isBot: false,
      botMessage: '',
      notifications: [],
      apiStatus: null,

      // Getters - PRESERVE same computed logic
      getBotStatus: () => {
        const state = get()
        return {
          isBot: state.isBot,
          message: state.botMessage
        }
      },

      getNotifications: () => {
        const state = get()
        return state.notifications
      },

      // Actions - PRESERVE same action behaviors
      setLoading: (loading) => {
        set({ isLoading: loading })
      },

      setBotStatus: (status, message = '') => {
        set({ 
          isBot: status, 
          botMessage: message 
        })
      },

      addNotification: (message, type = 'info', duration = 3000) => {
        const id = Date.now() + Math.random()
        const notification = {
          id,
          message,
          type
        }

        set((state) => ({
          notifications: [...state.notifications, notification]
        }))

        // Auto remove after duration - PRESERVE same timing
        setTimeout(() => {
          get().removeNotification(id)
        }, duration)

        return id
      },

      removeNotification: (id) => {
        set((state) => ({
          notifications: state.notifications.filter(n => n.id !== id)
        }))
      },

      clearNotifications: () => {
        set({ notifications: [] })
      },

      checkBotStatus: async () => {
        try {
          get().setLoading(true)
          const response = await api.getStatus()

          get().setBotStatus(response.data.isBot, response.data.message)
          set({ apiStatus: response.data })

          if (response.data.isBot) {
            get().addNotification('Bot traffic detected!', 'warning', 5000)
          }
        } catch (error) {
          console.error('Failed to check bot status:', error)
          get().addNotification('Failed to connect to API', 'error')
        } finally {
          get().setLoading(false)
        }
      },

      handleApiError: (error) => {
        console.error('API Error:', error)

        let message = 'An error occurred'
        if (error.response) {
          message = error.response.data?.message || `Server error: ${error.response.status}`
        } else if (error.request) {
          message = 'Network error - please check your connection'
        } else {
          message = error.message
        }

        get().addNotification(message, 'error')
      }
    }),
    {
      name: 'app-store', // For Redux DevTools
    }
  )
)
