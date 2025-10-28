/**
 * Chat Page
 * Main chat interface with agent selection and conversation
 */

import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import {
  makeStyles,
  tokens,
  Text,
} from '@fluentui/react-components'
import { MessageList } from '../components/chat/MessageList'
import { InputBox } from '../components/chat/InputBox'
import { ExportButton } from '../components/chat/ExportButton'
import { AgentSelector } from '../components/chat/AgentSelector'
import { ConversationName } from '../components/chat/ConversationName'
import { ThreadList } from '../components/chat/ThreadList'
import { Message, MessageRole } from '../types/message'
import { ChatThread } from '../types/chat'
import { useTraces } from '../hooks/useTraces'
import { streamChat } from '../services/api'
import { getChatThread } from '../services/chatService'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    height: '100%',
    background: 'linear-gradient(135deg, #0e1419 0%, #1a2530 100%)',
  },
  sidebar: {
    width: '300px',
    borderRight: `1px solid #2d3e4a`,
    display: 'flex',
    flexDirection: 'column',
    background: 'linear-gradient(180deg, #1a2530 0%, #243240 100%)',
    boxShadow: '2px 0 8px rgba(27, 137, 187, 0.15)',
  },
  sidebarHeader: {
    padding: '16px',
    borderBottom: `1px solid #2d3e4a`,
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  chatHeader: {
    padding: '16px 24px',
    borderBottom: `1px solid #2d3e4a`,
    background: 'linear-gradient(90deg, #1a2530 0%, #243240 100%)',
    boxShadow: '0 2px 8px rgba(27, 137, 187, 0.2)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '16px',
  },
  chatHeaderLeft: {
    flex: 1,
  },
  chatHeaderActions: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
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
 * Phase 3.2: Agent selector + Conversation naming
 * Phase 3.5: Real SSE streaming chat implementation
 * Phase 3.7: Thread management sidebar
 */
export const ChatPage = () => {
  const styles = useStyles()
  const navigate = useNavigate()
  const { threadId } = useParams<{ threadId?: string }>()
  const location = useLocation()
  const locationState = location.state as LocationState
  
  // Agent and conversation state
  const [currentAgentId, setCurrentAgentId] = useState<string>(locationState?.agentId || 'azure-ops')
  const [conversationName, setConversationName] = useState<string>('')
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { traces, addTraceEvent, clearTraces } = useTraces()

  // Load thread data on mount
  useEffect(() => {
    const loadThreadData = async () => {
      if (threadId && currentAgentId) {
        try {
          const thread = await getChatThread(currentAgentId, threadId)
          setConversationName(thread.title || '')
        } catch (error) {
          console.error('Failed to load thread:', error)
        }
      }
    }

    loadThreadData()
  }, [threadId, currentAgentId])

  // Handle agent change
  const handleAgentChange = (agentId: string) => {
    setCurrentAgentId(agentId)
    
    // Clear conversation and create new thread for new agent
    setMessages([])
    clearTraces()
    setConversationName('')

    console.log('Switched to agent:', agentId)
  }

  // Handle thread selection/switching
  const handleThreadSelect = (newThreadId: string) => {
    // Navigate to the thread
    navigate(`/chat/${newThreadId}`, {
      state: { agentId: currentAgentId },
    })
  }

  // Handle new thread creation
  const handleThreadCreate = (newThread: ChatThread) => {
    // Navigate to the new thread
    navigate(`/chat/${newThread.id}`, {
      state: { agentId: currentAgentId },
    })
    setConversationName(newThread.title || '')
    setMessages([])
    clearTraces()
  }

  // Handle thread deletion
  const handleThreadDelete = (deletedThreadId: string) => {
    if (threadId === deletedThreadId) {
      // Current thread was deleted, navigate to chat root
      navigate('/chat', {
        state: { agentId: currentAgentId },
      })
      setMessages([])
      clearTraces()
      setConversationName('')
    }
  }

  // Handle conversation name change
  const handleNameChange = async (newName: string) => {
    setConversationName(newName)
    
    // TODO: Save to thread metadata via API
    // if (threadId) {
    //   try {
    //     await updateChatThread(currentAgentId, threadId, { title: newName })
    //   } catch (error) {
    //     console.error('Failed to save conversation name:', error)
    //     throw error
    //   }
    // }
  }

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
    console.log('Sending message to agent:', currentAgentId)
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
      agentId: currentAgentId,
      isStreaming: true,
    }
    setMessages((prev) => [...prev, assistantMessage])
    setIsLoading(true)
    clearTraces()

    console.log('Starting stream to:', `${currentAgentId}/chat`)
    
    try {
      await streamChat(
        currentAgentId,
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
        <ThreadList
          agentId={currentAgentId}
          currentThreadId={threadId}
          onThreadSelect={handleThreadSelect}
          onThreadCreate={handleThreadCreate}
          onThreadDelete={handleThreadDelete}
        />
      </div>

      {/* Chat area */}
      <div className={styles.main}>
        {/* Chat header */}
        <div className={styles.chatHeader}>
          <div className={styles.chatHeaderLeft}>
            <ConversationName
              name={conversationName}
              onNameChange={handleNameChange}
              disabled={isLoading}
              threadId={threadId}
            />
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
          <div className={styles.chatHeaderActions}>
            <AgentSelector
              selectedAgentId={currentAgentId}
              onAgentChange={handleAgentChange}
              disabled={isLoading}
            />
            <ExportButton messages={messages} traces={traces} agentId={currentAgentId} />
          </div>
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
