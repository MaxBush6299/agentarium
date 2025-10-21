/**
 * Chat Page
 * Main chat interface with agent selection and conversation
 */

import { useState, useEffect } from 'react'
import { useParams, useLocation } from 'react-router-dom'
import {
  makeStyles,
  tokens,
  Text,
} from '@fluentui/react-components'
import { MessageList } from '../components/chat/MessageList'
import { InputBox } from '../components/chat/InputBox'
import { Message, MessageRole } from '../types/message'
import { useTraces } from '../hooks/useTraces'
import { streamChat } from '../services/api'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    height: '100%',
    backgroundColor: tokens.colorNeutralBackground1,
  },
  sidebar: {
    width: '300px',
    borderRight: `1px solid ${tokens.colorNeutralStroke2}`,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: tokens.colorNeutralBackground2,
  },
  sidebarHeader: {
    padding: '16px',
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  chatHeader: {
    padding: '16px 24px',
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground1,
  },
  chatContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  chatContentWrapper: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    padding: '12px',
    overflow: 'auto',
  },
  messagesContainer: {
    flex: 1,
    overflow: 'auto',
  },
})

interface LocationState {
  agentId?: string
}

/**
 * ChatPage Component
 * Phase 3.5: Real SSE streaming chat implementation
 */
export const ChatPage = () => {
  const styles = useStyles()
  const { threadId } = useParams<{ threadId?: string }>()
  const location = useLocation()
  const locationState = location.state as LocationState
  
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { traces, addTraceEvent, clearTraces } = useTraces()

  useEffect(() => {
    // TODO: Load thread messages from API
    if (threadId) {
      console.log('Loading thread:', threadId)
      // Future: Fetch thread messages from GET /api/threads/{threadId}/messages
    }
    if (locationState?.agentId) {
      console.log('Starting chat with agent:', locationState.agentId)
    }
  }, [threadId, locationState])

  const handleSendMessage = async (content: string) => {
    const agentId = locationState?.agentId || 'azure-ops'
    
    console.log('Sending message to agent:', agentId)
    console.log('Message:', content)
    console.log('Thread ID:', threadId)
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: MessageRole.USER,
      content,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Create placeholder for assistant message
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: MessageRole.ASSISTANT,
      content: '',
      timestamp: new Date(),
      agentId,
      isStreaming: true,
    }
    setMessages((prev) => [...prev, assistantMessage])
    setIsLoading(true)
    clearTraces()

    console.log('Starting stream to:', `${agentId}/chat`)
    
    try {
      await streamChat(
        agentId,
        content,
        threadId || null,
        // onChunk: Update message content as chunks arrive
        (chunk: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + chunk, isStreaming: true }
                : msg
            )
          )
        },
        // onTraceEvent: Add trace events as they arrive
        (traceEvent: unknown) => {
          const event = traceEvent as Record<string, unknown>
          addTraceEvent(event as any)
        },
        // onComplete: Mark streaming as done
        (fullMessage: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: fullMessage, isStreaming: false }
                : msg
            )
          )
          setIsLoading(false)
        },
        // onError: Show error message
        (error: Error) => {
          console.error('Streaming error:', error)
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: `Error: ${error.message}`,
                    error: error.message,
                    isStreaming: false,
                  }
                : msg
            )
          )
          setIsLoading(false)
        }
      )
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
                error: error instanceof Error ? error.message : 'Unknown error',
                isStreaming: false,
              }
            : msg
        )
      )
      setIsLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      {/* Thread list sidebar - Phase 3.7 */}
      <div className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <Text weight="semibold">Conversations</Text>
          <Text
            style={{
              fontSize: tokens.fontSizeBase200,
              color: tokens.colorNeutralForeground3,
              marginTop: '8px',
            }}
          >
            Thread management coming in Phase 3.7
          </Text>
        </div>
      </div>

      {/* Chat area */}
      <div className={styles.main}>
        {/* Chat header */}
        <div className={styles.chatHeader}>
          <Text weight="semibold" style={{ fontSize: '16px' }}>
            {locationState?.agentId 
              ? `Chat with Agent: ${locationState.agentId}` 
              : 'New Conversation'}
          </Text>
          {threadId && (
            <Text
              style={{
                fontSize: tokens.fontSizeBase200,
                color: tokens.colorNeutralForeground3,
                marginTop: '4px',
              }}
            >
              Thread: {threadId}
            </Text>
          )}
        </div>

        {/* Chat content */}
        <div className={styles.chatContent}>
          <div className={styles.chatContentWrapper}>
            <div className={styles.messagesContainer}>
              <MessageList messages={messages} traces={traces} isLoading={isLoading} />
            </div>
          </div>
          <InputBox onSend={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  )
}
