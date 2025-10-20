/**
 * useSSE Hook
 * Custom hook for Server-Sent Events (SSE) streaming
 */

import { useEffect, useRef, useCallback } from 'react'

export interface SSEOptions {
  onMessage?: (data: unknown) => void
  onError?: (error: Error) => void
  onOpen?: () => void
  onClose?: () => void
  headers?: Record<string, string>
}

export const useSSE = (url: string, options: SSEOptions = {}) => {
  const eventSourceRef = useRef<EventSource | null>(null)
  const { onMessage, onError, onOpen, onClose, headers } = options

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      return // Already connected
    }

    try {
      eventSourceRef.current = new EventSource(url)

      eventSourceRef.current.onopen = () => {
        onOpen?.()
      }

      eventSourceRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch (error) {
          console.warn('Failed to parse SSE message:', error)
          onMessage?.(event.data)
        }
      }

      eventSourceRef.current.onerror = () => {
        const error = new Error('SSE connection error')
        onError?.(error)
        disconnect()
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      onError?.(err)
    }
  }, [url, onMessage, onError, onOpen])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      onClose?.()
    }
  }, [onClose])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    connect,
    disconnect,
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN,
  }
}
