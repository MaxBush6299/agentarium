/**
 * ConversationName Component
 * 
 * Editable conversation name display in the chat header.
 * - Shows current conversation title or "Untitled" for new conversations
 * - Click to edit mode with inline text field
 * - Saves to ChatThread.title via API on blur or Enter key
 * - Handles empty/whitespace-only names gracefully
 */

import { useEffect, useState, useRef } from 'react'
import { makeStyles, Input, Text, Tooltip } from '@fluentui/react-components'
import { EditRegular, DismissRegular } from '@fluentui/react-icons'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    minHeight: '32px',
  },
  displayMode: {
    flex: 1,
    cursor: 'pointer',
    padding: '4px 8px',
    borderRadius: '4px',
    transition: 'background-color 0.2s ease',
    '&:hover': {
      backgroundColor: 'var(--colorNeutralBackground1Hover)',
    },
  },
  editMode: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    flex: 1,
  },
  input: {
    flex: 1,
    minWidth: '150px',
  },
  editButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '24px',
    height: '24px',
    cursor: 'pointer',
    borderRadius: '4px',
    transition: 'background-color 0.2s ease',
    '&:hover': {
      backgroundColor: 'var(--colorNeutralBackground1Hover)',
    },
  },
  cancelButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '24px',
    height: '24px',
    cursor: 'pointer',
    borderRadius: '4px',
    transition: 'background-color 0.2s ease',
    '&:hover': {
      backgroundColor: 'var(--colorStatusDangerBackground1Hover)',
    },
  },
  untitledText: {
    fontStyle: 'italic',
    color: 'var(--colorNeutralForeground3)',
  },
})

interface ConversationNameProps {
  name?: string
  onNameChange: (name: string) => Promise<void>
  disabled?: boolean
  threadId?: string
}

/**
 * ConversationName: Editable name display for conversations
 */
export const ConversationName: React.FC<ConversationNameProps> = ({
  name = '',
  onNameChange,
  disabled = false,
  threadId,
}) => {
  const styles = useStyles()
  const [isEditing, setIsEditing] = useState(false)
  const [displayName, setDisplayName] = useState(name || 'Untitled')
  const [editValue, setEditValue] = useState(name || '')
  const [isSaving, setIsSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // Update display name when prop changes
  useEffect(() => {
    setDisplayName(name || 'Untitled')
    setEditValue(name || '')
  }, [name, threadId])

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  // Handle save on blur
  const handleSave = async () => {
    const trimmedValue = editValue.trim()

    // Don't save if empty (keep original name)
    if (!trimmedValue && !name) {
      setEditValue(name || '')
      setIsEditing(false)
      return
    }

    try {
      setIsSaving(true)
      await onNameChange(trimmedValue || 'Untitled')
      setDisplayName(trimmedValue || 'Untitled')
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save conversation name:', error)
      // Reset to previous value on error
      setEditValue(name || '')
      setIsEditing(false)
    } finally {
      setIsSaving(false)
    }
  }

  // Handle keyboard events in edit mode
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      setEditValue(name || '')
      setIsEditing(false)
    }
  }

  // Handle cancel
  const handleCancel = () => {
    setEditValue(name || '')
    setIsEditing(false)
  }

  if (isEditing) {
    return (
      <div className={styles.root}>
        <div className={styles.editMode}>
          <Input
            ref={inputRef}
            className={styles.input}
            value={editValue}
            onChange={(_, data) => setEditValue(data.value)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            placeholder="Enter conversation name..."
            disabled={isSaving || disabled}
            appearance="underline"
          />
          <Tooltip content="Cancel" relationship="label">
            <div
              className={styles.cancelButton}
              onClick={handleCancel}
              style={{
                opacity: isSaving ? 0.5 : 1,
                pointerEvents: isSaving ? 'none' : 'auto',
              }}
            >
              <DismissRegular fontSize="16px" />
            </div>
          </Tooltip>
        </div>
      </div>
    )
  }

  return (
    <Tooltip content="Click to edit" relationship="label">
      <div
        className={styles.root}
        onClick={() => !disabled && setIsEditing(true)}
        style={{ opacity: disabled ? 0.5 : 1, pointerEvents: disabled ? 'none' : 'auto' }}
      >
        <div className={styles.displayMode}>
          <Text
            weight="semibold"
            style={{ fontSize: '16px' }}
            className={displayName === 'Untitled' ? styles.untitledText : undefined}
          >
            {displayName}
          </Text>
        </div>
        <div className={styles.editButton}>
          <EditRegular fontSize="16px" />
        </div>
      </div>
    </Tooltip>
  )
}

export default ConversationName
