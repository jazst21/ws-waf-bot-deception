import React from 'react'
import { Flashbar } from '@cloudscape-design/components'
import { useNotifications } from '../hooks/useNotifications'

function NotificationSystem() {
  const { notifications, removeNotification } = useNotifications()

  // Convert notifications to Cloudscape Flashbar format
  const flashbarItems = notifications.map(notification => ({
    id: notification.id,
    type: notification.type,
    content: notification.message,
    dismissible: true,
    onDismiss: () => removeNotification(notification.id)
  }))

  return (
    <Flashbar items={flashbarItems} />
  )
}

export default NotificationSystem
