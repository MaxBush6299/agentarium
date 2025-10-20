/**
 * Chat Service
 * Handles chat streaming and message operations using Server-Sent Events (SSE)
 */

import { Message, ChatThread, StreamEvent } from '@/types/chat'
import { getAccessToken } from './authService'
import { config } from '@/config'

const CHAT_ENDPOINT = '/chat'

export interface CreateChatRequest {
  agentId: string
  threadId?: string
  messages: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
}

export interface ChatStreamOptions {
  onMessage?: (message: Message) => void
  onEvent?: (event: StreamEvent) => void
  onError?: (error: Error) => void
  onComplete?: () => void
}

/**
 * Create or continue a chat session with streaming
 */
export const streamChat = async (
  request: CreateChatRequest,
  options: ChatStreamOptions = {}
): Promise<void> => {
  const { onMessage, onEvent, onError, onComplete } = options

  try {
    const token = await getAccessToken()
    if (!token) {
      throw new Error('No access token available')
    }

    const response = await fetch(`${config.apiBaseUrl}${CHAT_ENDPOINT}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    if (!response.body) {
      throw new Error('No response body')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        onComplete?.()
        break
      }

      buffer += decoder.decode(value, { stream: true })

      // Process complete lines
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim()) continue

        // Parse SSE format: data: {...}
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            const event: StreamEvent = {
              type: data.type,
              timestamp: data.timestamp || new Date().toISOString(),
              ...data,
            }

            onEvent?.(event)

            if (data.type === 'message' && onMessage) {
              onMessage(data.message as Message)
            }
          } catch (e) {
            console.warn('Failed to parse SSE event:', e)
          }
        }
      }
    }
  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error))
    onError?.(err)
    throw err
  }
}

/**
 * Get chat thread history
 */
export const getChatThread = async (threadId: string): Promise<ChatThread> => {
  const token = await getAccessToken()
  if (!token) {
    throw new Error('No access token available')
  }

  const response = await fetch(`${config.apiBaseUrl}${CHAT_ENDPOINT}/threads/${threadId}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Create new chat thread
 */
export const createChatThread = async (agentId: string): Promise<ChatThread> => {
  const token = await getAccessToken()
  if (!token) {
    throw new Error('No access token available')
  }

  const response = await fetch(`${config.apiBaseUrl}${CHAT_ENDPOINT}/threads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ agentId }),
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Delete chat thread
 */
export const deleteChatThread = async (threadId: string): Promise<void> => {
  const token = await getAccessToken()
  if (!token) {
    throw new Error('No access token available')
  }

  const response = await fetch(`${config.apiBaseUrl}${CHAT_ENDPOINT}/threads/${threadId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
}

/**
 * Export chat thread as JSON
 */
export const exportChatThread = async (threadId: string): Promise<ChatThread> => {
  const token = await getAccessToken()
  if (!token) {
    throw new Error('No access token available')
  }

  const response = await fetch(`${config.apiBaseUrl}${CHAT_ENDPOINT}/threads/${threadId}/export`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}
