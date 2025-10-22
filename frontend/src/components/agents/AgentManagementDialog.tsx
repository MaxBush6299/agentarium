/**
 * Agent Management Dialog - Delete Button
 * Simple delete button for agent cards
 */

import { useState } from 'react'
import {
  Button,
  makeStyles,
} from '@fluentui/react-components'
import { Delete24Regular } from '@fluentui/react-icons'
import { Agent } from '@/types/agent'
import { deleteAgent } from '@/services/agentsService'

const useStyles = makeStyles({
  deleteButton: {
    minWidth: '32px',
    padding: '4px',
  },
})

interface AgentManagementDialogProps {
  agent: Agent
  onAgentDeleted?: (agentId: string) => void
}

export const AgentManagementDialog = ({
  agent,
  onAgentDeleted,
}: AgentManagementDialogProps) => {
  const styles = useStyles()
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete "${agent.name}"? This cannot be undone.`)) {
      setIsDeleting(true)
      try {
        await deleteAgent(agent.id)
        setTimeout(() => {
          onAgentDeleted?.(agent.id)
        }, 300)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete agent'
        alert(`Error: ${errorMessage}`)
      } finally {
        setIsDeleting(false)
      }
    }
  }

  return (
    <Button
      className={styles.deleteButton}
      icon={<Delete24Regular />}
      appearance="subtle"
      title="Delete agent"
      onClick={handleDelete}
      disabled={isDeleting}
    />
  )
}
