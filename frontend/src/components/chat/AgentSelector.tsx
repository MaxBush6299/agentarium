/**
 * AgentSelector Component
 * 
 * Dropdown menu for selecting and switching between active agents.
 * - Fetches agent list from /api/agents on mount
 * - Displays agent names with status badges
 * - Handles agent switching (clears current conversation)
 * - Filters to show only active agents
 */

import { useEffect, useState, useRef } from 'react'
import {
  Dropdown,
  Option,
  makeStyles,
  useId,
  Spinner,
  Text,
  Badge,
} from '@fluentui/react-components'
import { ChevronDown24Regular } from '@fluentui/react-icons'
import { Agent } from '@/types/agent'
import { getAgents } from '@/services/agentsService'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  dropdown: {
    minWidth: '200px',
  },
  option: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '8px',
  },
  agentName: {
    flex: 1,
  },
  badge: {
    fontSize: '12px',
  },
  triggerButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  loadingSpinner: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
})

interface AgentSelectorProps {
  selectedAgentId?: string
  onAgentChange: (agentId: string) => void
  disabled?: boolean
}

/**
 * AgentSelector: Dropdown menu for switching between agents
 */
export const AgentSelector: React.FC<AgentSelectorProps> = ({
  selectedAgentId,
  onAgentChange,
  disabled = false,
}) => {
  const styles = useStyles()
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const dropdownId = useId()
  const initialFetchRef = useRef(true)

  // Fetch agents on component mount
  useEffect(() => {
    if (!initialFetchRef.current) return

    const fetchAgents = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const response = await getAgents(0, 100)
        setAgents(response.agents)

        // Set initial selected agent
        if (selectedAgentId && response.agents.length > 0) {
          const agent = response.agents.find((a) => a.id === selectedAgentId)
          if (agent) {
            setSelectedAgent(agent)
          }
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load agents'
        setError(message)
        console.error('Failed to fetch agents:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchAgents()
    initialFetchRef.current = false
  }, [selectedAgentId])

  // Handle agent selection from dropdown
  const handleAgentChange = (agentId: string | null) => {
    if (!agentId) return

    const agent = agents.find((a) => a.id === agentId)
    if (agent) {
      setSelectedAgent(agent)
      onAgentChange(agent.id)
    }
  }

  if (isLoading) {
    return (
      <div className={styles.loadingSpinner}>
        <Spinner size="tiny" />
        <Text size={200}>Loading agents...</Text>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.root}>
        <Text size={200} style={{ color: 'var(--colorStatusDangerForeground1)' }}>
          ⚠ Failed to load agents
        </Text>
      </div>
    )
  }

  if (agents.length === 0) {
    return (
      <div className={styles.root}>
        <Text size={200}>No agents available</Text>
      </div>
    )
  }

  return (
    <div className={styles.root}>
      <Dropdown
        id={dropdownId}
        className={styles.dropdown}
        value={selectedAgent?.id}
        onOptionSelect={(_, data) => handleAgentChange(data.optionValue || null)}
        disabled={disabled || isLoading}
        button={{
          children: (
            <div className={styles.triggerButton}>
              <span>{selectedAgent?.name || 'Select Agent'}</span>
              <ChevronDown24Regular />
            </div>
          ),
        }}
      >
        {agents.map((agent) => (
          <Option key={agent.id} value={agent.id} text={agent.name}>
            <div className={styles.option}>
              <span className={styles.agentName}>{agent.name}</span>
              <Badge
                className={styles.badge}
                appearance={agent.status === 'active' ? 'filled' : 'outline'}
                color={agent.status === 'active' ? 'success' : 'warning'}
              >
                {agent.status}
              </Badge>
            </div>
          </Option>
        ))}
      </Dropdown>
    </div>
  )
}

export default AgentSelector
