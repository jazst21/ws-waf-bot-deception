import { useAppStore } from '../store/useAppStore'

export function useBotStatus() {
  const isBot = useAppStore((state) => state.isBot)
  const botMessage = useAppStore((state) => state.botMessage)
  const isLoading = useAppStore((state) => state.isLoading)
  const apiStatus = useAppStore((state) => state.apiStatus)
  const checkBotStatus = useAppStore((state) => state.checkBotStatus)
  const setBotStatus = useAppStore((state) => state.setBotStatus)

  // PRESERVE same bot status logic as Vue version
  const getBotStatus = () => ({
    isBot,
    message: botMessage
  })

  const refreshBotStatus = async () => {
    await checkBotStatus()
  }

  return {
    isBot,
    botMessage,
    isLoading,
    apiStatus,
    getBotStatus,
    setBotStatus,
    checkBotStatus,
    refreshBotStatus
  }
}
