/**
 * API Client Service
 * Axios instance with interceptors for authentication and error handling
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import { config } from '@/config'
import { getAccessToken } from './authService'

let apiClient: AxiosInstance | null = null

/**
 * Initialize API client with interceptors
 */
export const initializeApiClient = (): AxiosInstance => {
  if (apiClient) {
    return apiClient
  }

  apiClient = axios.create({
    baseURL: config.apiBaseUrl,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor: Add authorization header
  apiClient.interceptors.request.use(
    async (requestConfig) => {
      const token = await getAccessToken()
      if (token) {
        requestConfig.headers.Authorization = `Bearer ${token}`
      }
      return requestConfig
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor: Handle errors
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Redirect to login on 401
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )

  return apiClient
}

/**
 * Get API client instance
 */
export const getApiClient = (): AxiosInstance => {
  return apiClient || initializeApiClient()
}

/**
 * Make GET request
 */
export const apiGet = async <T>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> => {
  const client = getApiClient()
  const response = await client.get<T>(url, config)
  return response.data
}

/**
 * Make POST request
 */
export const apiPost = async <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> => {
  const client = getApiClient()
  const response = await client.post<T>(url, data, config)
  return response.data
}

/**
 * Make PUT request
 */
export const apiPut = async <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> => {
  const client = getApiClient()
  const response = await client.put<T>(url, data, config)
  return response.data
}

/**
 * Make DELETE request
 */
export const apiDelete = async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  const client = getApiClient()
  const response = await client.delete<T>(url, config)
  return response.data
}

/**
 * Stream chat messages using Server-Sent Events (SSE)
 * @param agentId - The agent to chat with
 * @param message - The user's message
 * @param threadId - Optional thread ID for continuing a conversation
 * @param onChunk - Callback for each content chunk
 * @param onComplete - Callback when streaming completes
 * @param onError - Callback for errors
 */
export const streamChat = async (
  agentId: string,
  message: string,
  threadId: string | null,
  onChunk: (chunk: string) => void,
  onTraceEvent: ((event: Record<string, unknown>) => void) | ((fullMessage: string) => void),
  onComplete?: ((fullMessage: string) => void) | ((error: Error) => void),
  onError?: (error: Error) => void
): Promise<void> => {
  // Determine if we're using the new signature (7 params) or old (6 params)
  // New: streamChat(id, msg, threadId, onChunk, onTraceEvent, onComplete, onError)
  // Old: streamChat(id, msg, threadId, onChunk, onComplete, onError)
  let completeCallback: ((fullMessage: string) => void) | undefined
  let errorCallback: ((error: Error) => void) | undefined
  let traceEventCallback: ((event: Record<string, unknown>) => void) | undefined

  if (onComplete !== undefined) {
    // New signature: 7 parameters
    completeCallback = onComplete as (fullMessage: string) => void
    errorCallback = onError
    traceEventCallback = onTraceEvent as (event: Record<string, unknown>) => void
  } else {
    // Old signature: 6 parameters (onTraceEvent is actually onComplete, onError is undefined)
    completeCallback = onTraceEvent as (fullMessage: string) => void
    errorCallback = onError
    traceEventCallback = undefined
  }

  let timeoutId: NodeJS.Timeout | undefined
  
  try {
    const token = await getAccessToken()
    
    // Determine if this is a workflow or agent based on known workflow IDs
    const workflowIds = ['intelligent-handoff', 'sequential-data-analysis', 'data-analysis-pipeline', 'multi-perspective-analysis', 'change-approval-workflow', 'rfq-procurement']
    const isWorkflow = workflowIds.includes(agentId)
    
    const url = isWorkflow 
      ? `${config.apiBaseUrl}/workflows/${agentId}/chat`
      : `${config.apiBaseUrl}/agents/${agentId}/chat`
    
    // Create AbortController with timeout for streaming requests
    // Workflows may take longer than regular agent requests
    const timeoutMs = isWorkflow ? 180000 : 60000 // 3 min for workflows, 1 min for agents
    const controller = new AbortController()
    timeoutId = setTimeout(() => controller.abort(), timeoutMs)
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        message,
        thread_id: threadId,
        stream: true,
      }),
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    if (!response.body) {
      throw new Error('Response body is null')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullMessage = ''

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        break
      }

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true })
      
      // Process complete SSE messages (split by \n\n)
      const messages = buffer.split('\n\n')
      buffer = messages.pop() || '' // Keep incomplete message in buffer

      for (const msg of messages) {
        if (!msg.trim()) continue

        // Parse SSE format: "event: type\ndata: {...}"
        const lines = msg.split('\n')
        let eventType = 'message' // default event type
        let eventData = ''
        
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.substring(7).trim()
          } else if (line.startsWith('data: ')) {
            eventData = line.substring(6).trim()
          }
        }
        
        if (!eventData) continue
        
        // Handle special events
        if (eventData === '[DONE]') {
          completeCallback?.(fullMessage)
          return
        }

        try {
          const parsed = JSON.parse(eventData)
          
          // Handle phase_complete events from RFQ workflow
          if (eventType === 'phase_complete') {
            // Phase complete event: create a new message for this phase
            // Pass to trace event handler which we'll use for phases
            if (traceEventCallback) {
              traceEventCallback({
                type: 'phase_complete',
                phase: parsed.phase,
                message: parsed.message,
                data: parsed.data,
              })
            }
            console.debug('Received phase complete:', parsed.phase)
            continue
          }
          
          // Handle different event types from backend
          // Match the actual SSE events from the backend streaming:
          if (parsed.type === 'token' && parsed.content) {
            const chunk = parsed.content
            fullMessage += chunk
            onChunk(chunk)
          } else if (parsed.message) {
            // Handle message events from backend (both agents and workflows)
            // Backend sends: { "message": "..." }
            fullMessage = parsed.message
            onChunk(parsed.message)
          } else if (parsed.type === 'done' || parsed.complete) {
            completeCallback?.(fullMessage)
            return
          } else if (parsed.type === 'error') {
            errorCallback?.(new Error(parsed.error || 'Unknown error'))
            return
          } else if (parsed.type === 'trace_start' || parsed.type === 'trace_update' || parsed.type === 'trace_end') {
            // Pass trace events to the trace event handler if provided
            if (traceEventCallback) {
              traceEventCallback(parsed)
            }
            console.debug('Received trace event:', parsed.type)
          } else if (parsed.workflow_type || parsed.workflow_id) {
            // Handle workflow metadata events - convert to trace events for display
            // Example: { workflow_id: 'sequential-data-analysis', workflow_type: 'sequential', pattern: '...', ... }
            const traceEvent = {
              type: 'trace_end',
              tool_name: parsed.pattern || `${parsed.workflow_type} workflow`,
              step_id: parsed.workflow_id,
              metadata: parsed,
            }
            if (traceEventCallback) {
              traceEventCallback(traceEvent)
            }
            console.debug('Received workflow metadata:', parsed.workflow_type)
          } else if (parsed.type === 'heartbeat') {
            // Ignore heartbeat events
            console.debug('Received heartbeat')
          }
        } catch (e) {
          // If not JSON, treat as plain text chunk
          console.warn('Failed to parse SSE event:', e)
        }
      }
    }

    // If loop exits without [DONE], complete anyway
    completeCallback?.(fullMessage)
  } catch (error) {
    errorCallback?.(error instanceof Error ? error : new Error(String(error)))
  } finally {
    // Clean up timeout
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
  }
}
