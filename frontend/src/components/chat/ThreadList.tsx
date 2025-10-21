/**
 * Thread List Component
 * Displays conversation threads in sidebar with switching and delete capabilities
 * Phase 3.7: Thread management sidebar
 */

import { useState, useEffect } from 'react'
import {
  makeStyles,
  tokens,
  Button,
  Text,
  Spinner,
  Tooltip,
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogBody,
  DialogTitle,
  DialogActions,
} from '@fluentui/react-components'
import {
  Delete20Regular as DeleteIcon,
  Add20Regular as AddIcon,
  Chat20Regular as ChatIcon,
} from '@fluentui/react-icons'
import { ChatThread } from '../../types/chat'
import { listThreads, deleteChatThread, createChatThread } from '../../services/chatService'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden',
  },
  header: {
    padding: '12px 16px',
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '8px',
  },
  headerText: {
    flex: 1,
    fontWeight: 600,
  },
  newButton: {
    minWidth: '32px',
    padding: '0 8px',
  },
  threadsList: {
    flex: 1,
    overflow: 'auto',
    padding: '8px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  threadItem: {
    padding: '12px',
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid transparent`,
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.2s ease-in-out',
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground2,
    },
  },
  threadItemActive: {
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
  },
  threadItemContent: {
    flex: 1,
    minWidth: 0,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  threadTitle: {
    flex: 1,
    minWidth: 0,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    fontSize: tokens.fontSizeBase200,
  },
  threadDate: {
    fontSize: tokens.fontSizeBase100,
    color: tokens.colorNeutralForeground3,
    whiteSpace: 'nowrap',
  },
  deleteButton: {
    minWidth: '32px',
    padding: '0 4px',
  },
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '12px',
    padding: '24px 16px',
    textAlign: 'center',
    color: tokens.colorNeutralForeground3,
  },
  loadingContainer: {
    flex: 1,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '24px',
  },
  deleteDialog: {
    maxWidth: '400px',
  },
})

export interface ThreadListProps {
  agentId: string
  currentThreadId?: string
  onThreadSelect: (threadId: string) => void
  onThreadCreate: (thread: ChatThread) => void
  onThreadDelete: (threadId: string) => void
}

/**
 * ThreadList Component
 * Displays and manages conversation threads for current agent
 */
export const ThreadList = ({
  agentId,
  currentThreadId,
  onThreadSelect,
  onThreadCreate,
  onThreadDelete,
}: ThreadListProps) => {
  const styles = useStyles()
  const [threads, setThreads] = useState<ChatThread[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [threadToDelete, setThreadToDelete] = useState<ChatThread | null>(null)

  // Load threads for current agent
  useEffect(() => {
    const loadThreads = async () => {
      if (!agentId) return

      setIsLoading(true)
      setError(null)
      try {
        const loadedThreads = await listThreads(agentId, 50)
        // Sort by creation date (newest first)
        const sorted = loadedThreads.sort((a, b) => {
          const dateA = new Date(a.createdAt || 0).getTime()
          const dateB = new Date(b.createdAt || 0).getTime()
          return dateB - dateA
        })
        setThreads(sorted)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load threads'
        const isServerError = errorMessage.includes('500') || errorMessage.includes('status code 500')
        
        if (isServerError) {
          setError('Thread service is temporarily unavailable. Check that the backend is running.')
        } else {
          setError(errorMessage)
        }
        
        console.error('Failed to load threads:', err)
      } finally {
        setIsLoading(false)
      }
    }

    loadThreads()
  }, [agentId])

  // Handle create new thread
  const handleCreateThread = async () => {
    if (isCreating) return

    setIsCreating(true)
    try {
      const newThread = await createChatThread(agentId)
      setThreads((prev) => [newThread, ...prev])
      onThreadCreate(newThread)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create thread'
      console.error('Failed to create thread:', err)
      setError(message)
    } finally {
      setIsCreating(false)
    }
  }

  // Handle delete thread
  const handleDeleteThread = async () => {
    if (!threadToDelete) return

    try {
      await deleteChatThread(agentId, threadToDelete.id)
      setThreads((prev) => prev.filter((t) => t.id !== threadToDelete.id))
      
      // If deleting current thread, select another one first before onThreadDelete
      if (currentThreadId === threadToDelete.id) {
        const remainingThreads = threads.filter((t) => t.id !== threadToDelete.id)
        if (remainingThreads.length > 0) {
          // Select next thread before notifying of deletion
          onThreadSelect(remainingThreads[0].id)
        } else {
          // No more threads, navigate to chat root
          onThreadDelete(threadToDelete.id)
        }
      } else {
        // Deleting a thread that's not current, just notify
        onThreadDelete(threadToDelete.id)
      }
      
      setThreadToDelete(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete thread'
      console.error('Failed to delete thread:', err)
      setError(message)
    }
  }

  // Format date for display
  const formatDate = (dateString?: string): string => {
    if (!dateString) return ''
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    // Less than 1 hour
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000)
      return `${minutes}m ago`
    }

    // Less than 1 day
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000)
      return `${hours}h ago`
    }

    // Less than 7 days
    if (diff < 604800000) {
      const days = Math.floor(diff / 86400000)
      return `${days}d ago`
    }

    // Default format
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className={styles.container}>
      {/* Header with new conversation button */}
      <div className={styles.header}>
        <Text className={styles.headerText}>Conversations</Text>
        <Tooltip content="New Conversation" relationship="label">
          <Button
            appearance="transparent"
            size="small"
            icon={<AddIcon />}
            onClick={handleCreateThread}
            disabled={isCreating}
            className={styles.newButton}
          />
        </Tooltip>
      </div>

      {/* Threads list or empty state */}
      {isLoading ? (
        <div className={styles.loadingContainer}>
          <Spinner size="small" label="Loading conversations..." />
        </div>
      ) : error ? (
        <div className={styles.emptyState}>
          <Text weight="semibold" style={{ color: tokens.colorPaletteRedForeground1 }}>
            {error}
          </Text>
          <Text style={{ fontSize: tokens.fontSizeBase100, marginTop: '8px' }}>
            Make sure the backend API is running and Cosmos DB is configured.
          </Text>
          <Button
            appearance="primary"
            size="small"
            onClick={() => window.location.reload()}
            style={{ marginTop: '12px' }}
          >
            Retry
          </Button>
        </div>
      ) : threads.length === 0 ? (
        <div className={styles.emptyState}>
          <ChatIcon style={{ fontSize: '32px', opacity: 0.5 }} />
          <Text>No conversations yet</Text>
          <Text style={{ fontSize: tokens.fontSizeBase100 }}>
            Start a new conversation to begin
          </Text>
        </div>
      ) : (
        <div className={styles.threadsList}>
          {threads.map((thread) => (
            <div
              key={thread.id}
              className={`${styles.threadItem} ${
                currentThreadId === thread.id ? styles.threadItemActive : ''
              }`}
              onClick={() => onThreadSelect(thread.id)}
            >
              <div className={styles.threadItemContent}>
                <ChatIcon style={{ fontSize: '16px', flexShrink: 0 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className={styles.threadTitle}>
                    {thread.title || 'Untitled'}
                  </div>
                  <div className={styles.threadDate}>
                    {formatDate(thread.createdAt)}
                  </div>
                </div>
              </div>

              {/* Delete button - show on hover */}
              <Dialog
                open={threadToDelete?.id === thread.id}
                onOpenChange={(open) => {
                  if (!open) setThreadToDelete(null)
                }}
              >
                <DialogTrigger disableButtonEnhancement>
                  <Tooltip
                    content="Delete conversation"
                    relationship="label"
                  >
                    <Button
                      appearance="transparent"
                      size="small"
                      icon={<DeleteIcon />}
                      onClick={(e) => {
                        e.stopPropagation()
                        setThreadToDelete(thread)
                      }}
                      className={styles.deleteButton}
                    />
                  </Tooltip>
                </DialogTrigger>
                <DialogContent className={styles.deleteDialog}>
                  <DialogTitle>Delete Conversation?</DialogTitle>
                  <DialogBody>
                    <Text>
                      Are you sure you want to delete "{thread.title || 'Untitled'}"? This action cannot be undone.
                    </Text>
                  </DialogBody>
                  <DialogActions>
                    <Button
                      appearance="secondary"
                      onClick={() => setThreadToDelete(null)}
                    >
                      Cancel
                    </Button>
                    <Button
                      appearance="primary"
                      onClick={handleDeleteThread}
                    >
                      Delete
                    </Button>
                  </DialogActions>
                </DialogContent>
              </Dialog>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
