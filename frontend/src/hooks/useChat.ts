/**
 * useChat Hook
 * Custom hook for managing chat state and operations
 */

import { useEffect, useState, useCallback } from 'react'
import { Message, ChatThread, ToolCall } from '@/types/chat'
import { streamChat, CreateChatRequest, ChatStreamOptions, getChatThread, createChatThread, deleteChatThread } from '@/services/chatService'

export interface UseChatState {
  threadId: string | null
  messages: Message[]
  isStreaming: boolean
  error: string | null
  toolCalls: ToolCall[]
}

export const useChat = (agentId: string) => {
  const [state, setState] = useState<UseChatState>({
    threadId: null,
    messages: [],
    isStreaming: false,
    error: null,
    toolCalls: [],
  })

  // Initialize chat thread
  const initializeThread = useCallback(async () => {
    try {
      const thread = await createChatThread(agentId)
      setState((prev) => ({
        ...prev,
        threadId: thread.id,
        messages: thread.messages || [],
      }))
      return thread
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to initialize thread'
      setState((prev) => ({ ...prev, error: message }))
      throw error
    }
  }, [agentId])

  // Load thread history
  const loadThread = useCallback(async (threadId: string) => {
    try {
      const thread = await getChatThread(threadId)
      setState((prev) => ({
        ...prev,
        threadId: thread.id,
        messages: thread.messages || [],
        error: null,
      }))
      return thread
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load thread'
      setState((prev) => ({ ...prev, error: message }))
      throw error
    }
  }, [])

  // Send message with streaming
  const sendMessage = useCallback(
    async (userMessage: string) => {
      if (!state.threadId) {
        await initializeThread()
      }

      const threadId = state.threadId || (await initializeThread()).id

      try {
        setState((prev) => ({
          ...prev,
          isStreaming: true,
          error: null,
        }))

        const request: CreateChatRequest = {
          agentId,
          threadId,
          messages: [
            ...state.messages,
            {
              role: 'user',
              content: userMessage,
            },
          ],
        }

        const streamOptions: ChatStreamOptions = {
          onMessage: (message) => {
            setState((prev) => ({
              ...prev,
              messages: [...prev.messages, message],
            }))
          },
          onEvent: (event) => {
            if (event.type === 'tool_call') {
              setState((prev) => ({
                ...prev,
                toolCalls: [...prev.toolCalls, event as unknown as ToolCall],
              }))
            }
          },
          onError: (error) => {
            setState((prev) => ({
              ...prev,
              error: error.message,
              isStreaming: false,
            }))
          },
          onComplete: () => {
            setState((prev) => ({
              ...prev,
              isStreaming: false,
            }))
          },
        }

        await streamChat(request, streamOptions)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to send message'
        setState((prev) => ({
          ...prev,
          error: message,
          isStreaming: false,
        }))
      }
    },
    [state.threadId, state.messages, agentId, initializeThread]
  )

  // Delete thread
  const deleteThread = useCallback(async () => {
    if (!state.threadId) return

    try {
      await deleteChatThread(state.threadId)
      setState({
        threadId: null,
        messages: [],
        isStreaming: false,
        error: null,
        toolCalls: [],
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete thread'
      setState((prev) => ({ ...prev, error: message }))
    }
  }, [state.threadId])

  // Clear messages
  const clearMessages = useCallback(() => {
    setState((prev) => ({
      ...prev,
      messages: [],
      toolCalls: [],
      error: null,
    }))
  }, [])

  return {
    ...state,
    initializeThread,
    loadThread,
    sendMessage,
    deleteThread,
    clearMessages,
  }
}
