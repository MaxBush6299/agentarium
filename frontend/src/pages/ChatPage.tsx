/**
 * Chat Page
 * Main chat interface with agent selection and conversation
 */

import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import {
  makeStyles,
  tokens,
  Text,
} from '@fluentui/react-components'
import { MessageList } from '../components/chat/MessageList'
import { InputBox } from '../components/chat/InputBox'
import { RFQRequestForm, RFQFormData } from '../components/chat/RFQRequestForm'
import { ExportButton } from '../components/chat/ExportButton'
import { AgentSelector } from '../components/chat/AgentSelector'
import { ConversationName } from '../components/chat/ConversationName'
import { ThreadList } from '../components/chat/ThreadList'
import { Message, MessageRole } from '../types/message'
import { ChatThread } from '../types/chat'
import { useTraces } from '../hooks/useTraces'
import { streamChat } from '../services/api'
import { getChatThread, createChatThread, saveThreadMessage, updateChatThread } from '../services/chatService'

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
  workflowId?: string
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
  const [searchParams] = useSearchParams()
  const locationState = location.state as LocationState
  
  // Check for workflow in query params (from WorkflowCard) or location state
  const workflowParam = searchParams.get('workflow')
  const initialWorkflowId = workflowParam || locationState?.workflowId || 'sequential-data-analysis'
  
  // Agent and conversation state
  // Default to Sequential Data Analysis workflow
  const [currentAgentId, setCurrentAgentId] = useState<string>(locationState?.agentId || initialWorkflowId)
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(initialWorkflowId)
  const [conversationName, setConversationName] = useState<string>('')
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { traces, clearTraces, addTraceEvent } = useTraces()

  // Load thread data on mount
  useEffect(() => {
    const loadThreadData = async () => {
      if (threadId && currentAgentId) {
        try {
          const thread = await getChatThread(currentAgentId, threadId)
          setConversationName(thread.title || '')
          
          // Load messages from thread history and convert to local Message type
          if (thread.messages && thread.messages.length > 0) {
            const convertedMessages: Message[] = thread.messages.map(msg => ({
              id: msg.id,
              role: msg.role === 'user' ? MessageRole.USER : MessageRole.ASSISTANT,
              content: msg.content,
              timestamp: new Date(msg.timestamp),
            }))
            setMessages(convertedMessages)
          } else {
            setMessages([])
          }
        } catch (error) {
          console.error('Failed to load thread:', error)
        }
      }
    }

    loadThreadData()
  }, [threadId, currentAgentId])

  // Create a new thread eagerly when agent is selected but no thread exists
  // This ensures thread appears in sidebar immediately
  useEffect(() => {
    const createThreadEagerly = async () => {
      // Only create if:
      // 1. We have an agent/workflow selected
      // 2. We're not already viewing a thread
      // 3. We haven't just navigated from a workflow card (check if it's the initial load)
      if (currentAgentId && !threadId) {
        try {
          console.log('Creating thread eagerly for agent:', currentAgentId)
          const newThread = await createChatThread(currentAgentId)
          console.log('Thread created eagerly:', newThread.id)
          // Navigate to the new thread
          navigate(`/chat/${newThread.id}`, {
            state: { agentId: currentAgentId },
            replace: true, // Use replace to avoid adding to history
          })
        } catch (error) {
          console.error('Failed to create thread eagerly:', error)
          // Continue - user can still send messages and thread will be created then
        }
      }
    }

    // Debounce to avoid creating multiple threads on rapid agent switches
    const timer = setTimeout(createThreadEagerly, 300)
    return () => clearTimeout(timer)
  }, [currentAgentId, threadId, navigate])

  // Handle agent change
  const handleAgentChange = (agentId: string) => {
    setCurrentAgentId(agentId)
    setCurrentWorkflowId(null)  // Clear workflow when switching agents
    
    // Clear conversation and create new thread for new agent
    setMessages([])
    clearTraces()
    setConversationName('')

    console.log('Switched to agent:', agentId)
  }

  // Handle workflow change
  const handleWorkflowChange = (workflowId: string) => {
    setCurrentWorkflowId(workflowId)
    setCurrentAgentId(workflowId)  // Use workflow ID as the primary identifier
    
    // Clear conversation and create new thread for new workflow
    setMessages([])
    clearTraces()
    setConversationName('')
    
    // Navigate to chat root to trigger new thread creation
    navigate('/chat', {
      state: { agentId: workflowId },
      replace: true,
    })

    console.log('Switched to workflow:', workflowId)
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
    
    // Save to thread metadata via API
    if (threadId && currentAgentId) {
      try {
        await updateChatThread(currentAgentId, threadId, { title: newName })
      } catch (error) {
        console.error('Failed to save conversation name:', error)
        throw error
      }
    }
  }

  // Save user and assistant messages to thread
  const saveMessagesToThread = async (threadId: string, userMessage: string, assistantMessage: string) => {
    try {
      // Save user message
      await saveThreadMessage(currentAgentId, threadId, userMessage, 'user')
      
      // Save assistant message
      await saveThreadMessage(currentAgentId, threadId, assistantMessage, 'assistant')
      
      console.log('Saved messages to thread:', threadId)
    } catch (error) {
      console.error('Failed to save messages to thread:', error)
      // Don't throw - conversation should still work even if saving fails
    }
  }

  const handleSendMessage = async (content: string) => {
    console.log('Sending message to agent:', currentAgentId)
    console.log('Message:', content)
    console.log('Thread ID:', threadId)
    
    // Thread should already exist due to eager creation
    const activeThreadId = threadId
    if (!activeThreadId) {
      console.error('No thread ID available when sending message')
      return
    }
    
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

    // Stream response
    await streamChat(
      currentAgentId,
      content,
      activeThreadId,
      (chunk: string) => {
        // Update streaming message
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        )
      },
      (event: Record<string, unknown>) => {
        // Handle phase_complete events for RFQ workflow
        if (event.type === 'phase_complete') {
          const phaseMessage = event.message as string
          const phaseName = event.phase as string
          
          // Create a new assistant message for this phase
          const phaseMessageId = `${Date.now()}_${phaseName}`
          const newPhaseMessage: Message = {
            id: phaseMessageId,
            role: MessageRole.ASSISTANT,
            content: phaseMessage,
            timestamp: new Date(),
            agentId: currentAgentId,
            isStreaming: false,
            metadata: {
              phase: phaseName,
              isPhaseMessage: true,
              data: (event.data as Record<string, unknown>) || {},
            },
          }
          
          // Remove the original placeholder streaming message if this is the first phase
          setMessages((prev) => {
            const hasPlaceholder = prev.some(m => m.id === assistantMessageId && m.content === '')
            if (hasPlaceholder) {
              // Replace placeholder with first phase message
              return prev.map(m => m.id === assistantMessageId ? newPhaseMessage : m)
            } else {
              // Add as new message
              return [...prev, newPhaseMessage]
            }
          })
          
          // Save phase message to thread
          saveMessagesToThread(activeThreadId, '', phaseMessage).catch(err => 
            console.error('Failed to save phase message:', err)
          )
        } else {
          // Handle trace events (optional for workflows)
          console.debug('Trace event:', event)
          
          // Add trace event to traces state if it's a valid trace event
          // Filter out agent-framework traces that don't have workflow_id
          if (event.type && ['trace_start', 'trace_update', 'trace_end'].includes(event.type as string)) {
            // Only add traces that have workflow_id (our custom traces)
            // This filters out agent-framework's internal traces
            if (event.workflow_id || (event.type === 'trace_end' && event.output)) {
              addTraceEvent({
                ...event,
                timestamp: new Date().toISOString(),
              } as any)
            }
          }
        }
      },
      (fullMessage: string) => {
        // Finalize message (only for non-phase workflows)
        if (!currentAgentId.includes('rfq')) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: fullMessage, isStreaming: false }
                : msg
            )
          )
          
          // Save both messages to thread
          saveMessagesToThread(activeThreadId, content, fullMessage)
        } else {
          // For RFQ workflow, just remove placeholder if still there
          setMessages((prev) => prev.filter(m => !(m.id === assistantMessageId && m.content === '')))
        }
        setIsLoading(false)
      },
      (error: Error) => {
        // Handle error
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: '', error: error.message, isStreaming: false }
              : msg
          )
        )
        setIsLoading(false)
      }
    )
  }

  // Handler for RFQ form submission
  const handleRFQSubmit = async (rfqData: RFQFormData) => {
    // Convert RFQ form data to JSON string
    const rfqJson = JSON.stringify(rfqData, null, 2)
    
    // Update thread title with RFQ number
    if (threadId) {
      try {
        await updateChatThread(currentAgentId, threadId, {
          title: rfqData.request_id,
        })
        // Update local state
        setConversationName(rfqData.request_id)
      } catch (error) {
        console.error('Failed to update thread title:', error)
      }
    }
    
    // Send as a regular message
    await handleSendMessage(rfqJson)
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
              selectedWorkflowId={currentWorkflowId || undefined}
              onAgentChange={handleAgentChange}
              onWorkflowChange={handleWorkflowChange}
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
          {/* Show RFQ form for RFQ workflow, otherwise show regular input */}
          {currentWorkflowId === 'rfq-procurement' ? (
            <RFQRequestForm onSubmit={handleRFQSubmit} disabled={isLoading} />
          ) : (
            <InputBox onSend={handleSendMessage} disabled={isLoading} />
          )}
        </div>
      </div>
    </div>
  )
}
