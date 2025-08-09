import { useState, useCallback } from 'react'
import { useAppStore } from '../store/useAppStore'
import api from '../services/api'

export function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const handleApiError = useAppStore((state) => state.handleApiError)

  // Generic API call wrapper - PRESERVE same error handling as Vue
  const callApi = useCallback(async (apiFunction, ...args) => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiFunction(...args)
      return response
    } catch (err) {
      setError(err)
      handleApiError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  // Specific API methods - PRESERVE same API calls as Vue
  const getStatus = useCallback(() => callApi(api.getStatus), [callApi])
  const getBotDemo1 = useCallback(() => callApi(api.getBotDemo1), [callApi])
  const getBotDemo1Info = useCallback(() => callApi(api.getBotDemo1Info), [callApi])
  const getBotDemo2Comments = useCallback(() => callApi(api.getBotDemo2Comments), [callApi])
  const postBotDemo2Comment = useCallback((data) => callApi(api.postBotDemo2Comment, data), [callApi])
  const getBotDemo2Info = useCallback(() => callApi(api.getBotDemo2Info), [callApi])
  const getBotDemo3Flights = useCallback(() => callApi(api.getBotDemo3Flights), [callApi])
  const getBotDemo3Info = useCallback(() => callApi(api.getBotDemo3Info), [callApi])
  const getRobotsTxt = useCallback(() => callApi(api.getRobotsTxt), [callApi])

  return {
    loading,
    error,
    callApi,
    // API methods
    getStatus,
    getBotDemo1,
    getBotDemo1Info,
    getBotDemo2Comments,
    postBotDemo2Comment,
    getBotDemo2Info,
    getBotDemo3Flights,
    getBotDemo3Info,
    getRobotsTxt
  }
}
