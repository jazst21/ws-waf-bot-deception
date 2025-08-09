import { useAppStore } from '../store/useAppStore'

export function useNotifications() {
  const notifications = useAppStore((state) => state.notifications)
  const addNotification = useAppStore((state) => state.addNotification)
  const removeNotification = useAppStore((state) => state.removeNotification)
  const clearNotifications = useAppStore((state) => state.clearNotifications)

  // PRESERVE same notification behaviors as Vue version
  const showSuccess = (message, duration = 3000) => {
    return addNotification(message, 'success', duration)
  }

  const showError = (message, duration = 5000) => {
    return addNotification(message, 'error', duration)
  }

  const showWarning = (message, duration = 4000) => {
    return addNotification(message, 'warning', duration)
  }

  const showInfo = (message, duration = 3000) => {
    return addNotification(message, 'info', duration)
  }

  return {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo
  }
}
