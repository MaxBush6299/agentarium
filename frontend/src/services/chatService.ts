/**
 * Chat Service
 * Handles chat streaming and message operations using Server-Sent Events (SSE)
 */

import { Message, ChatThread, StreamEvent } from '@/types/chat'
import { getAccessToken } from './authService'
import { apiGet, apiPost, apiDelete, apiPut } from './api'
import { config } from '@/config'

const CHAT_ENDPOINT = '/agents'

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

    // Use the correct endpoint: /api/agents/{agentId}/chat
    const endpoint = `${config.apiBaseUrl}${CHAT_ENDPOINT}/${request.agentId}/chat`
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        message: request.messages[request.messages.length - 1]?.content || '',
        thread_id: request.threadId,
        stream: true,
      }),
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
 * List all threads for an agent or workflow
 */
export const listThreads = async (agentId: string, limit?: number): Promise<ChatThread[]> => {
  const params = new URLSearchParams()
  if (limit) {
    params.append('limit', limit.toString())
  }
  
  const query = params.toString() ? `?${params.toString()}` : ''
  
  // Check if this is a workflow ID or agent ID
  const workflowIds = ['intelligent-handoff', 'sequential-data-analysis', 'data-analysis-pipeline', 'multi-perspective-analysis', 'change-approval-workflow', 'rfq-procurement']
  const isWorkflow = workflowIds.includes(agentId)
  
  const endpoint = isWorkflow 
    ? `/workflows/${agentId}/threads${query}`
    : `/agents/${agentId}/threads${query}`
  
  const response = await apiGet<{ threads: ChatThread[]; total: number; page: number; page_size: number }>(endpoint)
  return response.threads
}

/**
 * Get chat thread history
 */
export const getChatThread = async (agentId: string, threadId: string): Promise<ChatThread> => {
  // Check if this is a workflow ID or agent ID
  const workflowIds = ['intelligent-handoff', 'sequential-data-analysis', 'data-analysis-pipeline', 'multi-perspective-analysis', 'change-approval-workflow', 'rfq-procurement']
  const isWorkflow = workflowIds.includes(agentId)
  
  const endpoint = isWorkflow 
    ? `/workflows/${agentId}/threads/${threadId}`
    : `/agents/${agentId}/threads/${threadId}`
  
  return apiGet<ChatThread>(endpoint)
}

/**
 * Create new chat thread
 */
export const createChatThread = async (agentId: string, title?: string): Promise<ChatThread> => {
  // Check if this is a workflow ID or agent ID
  const workflowIds = ['intelligent-handoff', 'sequential-data-analysis', 'data-analysis-pipeline', 'multi-perspective-analysis', 'change-approval-workflow', 'rfq-procurement']
  const isWorkflow = workflowIds.includes(agentId)
  
  const endpoint = isWorkflow 
    ? `/workflows/${agentId}/threads`
    : `/agents/${agentId}/threads`
  
  return apiPost<ChatThread>(endpoint, { agentId, title })
}

/**
 * Delete chat thread
 */
export const deleteChatThread = async (agentId: string, threadId: string): Promise<void> => {
  // Check if this is a workflow ID or agent ID
  const workflowIds = ['intelligent-handoff', 'sequential-data-analysis', 'data-analysis-pipeline', 'multi-perspective-analysis', 'change-approval-workflow', 'rfq-procurement']
  const isWorkflow = workflowIds.includes(agentId)
  
  const endpoint = isWorkflow 
    ? `/workflows/${agentId}/threads/${threadId}`
    : `/agents/${agentId}/threads/${threadId}`
  
  await apiDelete(endpoint)
}

/**
 * Update chat thread (title, metadata, etc)
 */
export const updateChatThread = async (agentId: string, threadId: string, updates: { title?: string }): Promise<ChatThread> => {
  // Check if this is a workflow ID or agent ID
  const workflowIds = ['intelligent-handoff', 'sequential-data-analysis', 'data-analysis-pipeline', 'multi-perspective-analysis', 'change-approval-workflow', 'rfq-procurement']
  const isWorkflow = workflowIds.includes(agentId)
  
  const endpoint = isWorkflow 
    ? `/workflows/${agentId}/threads/${threadId}`
    : `/agents/${agentId}/threads/${threadId}`
  
  return apiPut<ChatThread>(endpoint, updates)
}

/**
 * Export chat thread as JSON
 */
export const exportChatThread = async (agentId: string, threadId: string): Promise<ChatThread> => {
  const token = await getAccessToken()
  if (!token) {
    throw new Error('No access token available')
  }

  const response = await fetch(`${config.apiBaseUrl}${CHAT_ENDPOINT}/${agentId}/threads/${threadId}/export`, {
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
 * Save a message to a thread (for workflows or agents)
 */
export const saveThreadMessage = async (
  agentId: string,
  threadId: string,
  message: string,
  role: 'user' | 'assistant' = 'assistant'
): Promise<ChatThread> => {
  // Check if this is a workflow ID or agent ID
  const workflowIds = ['intelligent-handoff', 'sequential-data-analysis', 'data-analysis-pipeline', 'multi-perspective-analysis', 'change-approval-workflow', 'rfq-procurement']
  const isWorkflow = workflowIds.includes(agentId)
  
  const endpoint = isWorkflow 
    ? `/workflows/${agentId}/threads/${threadId}/messages`
    : `/agents/${agentId}/threads/${threadId}/messages`
  
  return apiPost<ChatThread>(endpoint, { message, role })
}

