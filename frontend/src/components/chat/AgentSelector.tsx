/**
 * AgentSelector Component
 * 
 * Unified selector for both individual agents and multi-agent workflows.
 * 
 * Structure:
 * - INDIVIDUAL AGENTS section (data-agent, analyst, order-agent, etc.)
 * - MULTI-AGENT WORKFLOWS section (intelligent-handoff, sequential, etc.)
 * 
 * - Fetches both agents and workflows from API on mount
 * - Displays status badges and workflow type indicators
 * - Handles switching between agents and workflows
 * - Filters to show only active agents (workflows always available)
 */

import { useEffect, useState, useRef } from 'react'
import {
  Dropdown,
  Option,
  OptionGroup,
  makeStyles,
  useId,
  Spinner,
  Text,
  Badge,
} from '@fluentui/react-components'
import { Agent } from '@/types/agent'
import { getAgents } from '@/services/agentsService'
import { apiGet } from '@/services/api'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  dropdown: {
    minWidth: '200px',
  },
  optionContent: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '8px',
    width: '100%',
  },
  optionLabel: {
    flex: 1,
  },
  badge: {
    fontSize: '12px',
  },
  loadingSpinner: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  sectionHeader: {
    paddingLeft: '8px',
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--colorNeutralForeground3)',
    textTransform: 'uppercase',
  },
})

interface AgentSelectorProps {
  selectedAgentId?: string
  selectedWorkflowId?: string
  onAgentChange?: (agentId: string) => void
  onWorkflowChange?: (workflowId: string) => void
  disabled?: boolean
}

interface Workflow {
  id: string
  name: string
  type: 'handoff' | 'sequential' | 'parallel' | 'approval_chain'
  description?: string
}

/**
 * AgentSelector: Unified dropdown for agents and workflows
 */
export const AgentSelector: React.FC<AgentSelectorProps> = ({
  selectedAgentId,
  selectedWorkflowId,
  onAgentChange,
  onWorkflowChange,
  disabled = false,
}) => {
  const styles = useStyles()
  const [agents, setAgents] = useState<Agent[]>([])
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedValue, setSelectedValue] = useState<string>('')
  const [selectedLabel, setSelectedLabel] = useState<string>('Select Agent or Workflow')
  const dropdownId = useId()
  const initialFetchRef = useRef(true)

  // Fetch agents and workflows on component mount
  useEffect(() => {
    if (!initialFetchRef.current) return

    const fetchData = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Fetch agents
        const agentResponse = await getAgents(0, 100)
        setAgents(agentResponse.agents)

        // Set initial agent if needed
        if (selectedAgentId && agentResponse.agents.length > 0) {
          const agent = agentResponse.agents.find((a) => a.id === selectedAgentId)
          if (agent) {
            setSelectedLabel(agent.name)
            setSelectedValue(`agent:${agent.id}`)
          }
        }

        // Set initial workflow if needed
        try {
          console.log('[AgentSelector] Fetching workflows from /api/workflows')
          const workflowData = await apiGet<Record<string, Workflow>>('/workflows')
          console.log('[AgentSelector] Workflows fetched:', workflowData)
          const workflowList: Workflow[] = Object.values(workflowData || {})
          console.log('[AgentSelector] Workflow list:', workflowList)
          setWorkflows(workflowList)

            if (selectedWorkflowId && workflowList.length > 0) {
              const workflow = workflowList.find((w) => w.id === selectedWorkflowId)
              if (workflow) {
                setSelectedLabel(workflow.name)
                setSelectedValue(`workflow:${workflow.id}`)
              }
            }
        } catch (err) {
          console.warn('[AgentSelector] Could not fetch workflows:', err)
          // Workflows are optional, continue anyway
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load agents and workflows'
        setError(message)
        console.error('Failed to fetch data:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
    initialFetchRef.current = false
  }, [selectedAgentId, selectedWorkflowId])

  // Handle selection from dropdown
  const handleChange = (value: string | null) => {
    if (!value) return

    const [type, id] = value.split(':')

    if (type === 'agent' && onAgentChange) {
      const agent = agents.find((a) => a.id === id)
      if (agent) {
        setSelectedLabel(agent.name)
        setSelectedValue(value)
        onAgentChange(agent.id)
      }
    } else if (type === 'workflow' && onWorkflowChange) {
      const workflow = workflows.find((w) => w.id === id)
      if (workflow) {
        setSelectedLabel(workflow.name)
        setSelectedValue(value)
        onWorkflowChange(workflow.id)
      }
    }
  }

  if (isLoading) {
    return (
      <div className={styles.loadingSpinner}>
        <Spinner size="tiny" />
        <Text size={200}>Loading...</Text>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.root}>
        <Text size={200} style={{ color: 'var(--colorStatusDangerForeground1)' }}>
          ⚠ {error}
        </Text>
      </div>
    )
  }

  const hasAgents = agents.length > 0
  const hasWorkflows = workflows.length > 0

  if (!hasAgents && !hasWorkflows) {
    return (
      <div className={styles.root}>
        <Text size={200}>No agents or workflows available</Text>
      </div>
    )
  }

  return (
    <div className={styles.root}>
      <Dropdown
        id={dropdownId}
        className={styles.dropdown}
        value={selectedValue}
        onOptionSelect={(_, data) => handleChange(data.optionValue || null)}
        disabled={disabled || isLoading}
        button={{
          children: selectedLabel,
        }}
      >
        {/* Individual Agents Section */}
        {hasAgents && (
          <OptionGroup label="INDIVIDUAL AGENTS">
            {agents.map((agent) => (
              <Option
                key={agent.id}
                value={`agent:${agent.id}`}
                text={agent.name}
              >
                <div className={styles.optionContent}>
                  <span className={styles.optionLabel}>{agent.name}</span>
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
          </OptionGroup>
        )}

        {/* Multi-Agent Workflows Section */}
        {hasWorkflows && (
          <OptionGroup label="MULTI-AGENT WORKFLOWS">
            {workflows.map((workflow) => (
              <Option
                key={workflow.id}
                value={`workflow:${workflow.id}`}
                text={workflow.name}
              >
                <div className={styles.optionContent}>
                  <span className={styles.optionLabel}>{workflow.name}</span>
                  <Badge
                    className={styles.badge}
                    appearance="filled"
                    color="informative"
                  >
                    {workflow.type}
                  </Badge>
                </div>
              </Option>
            ))}
          </OptionGroup>
        )}
      </Dropdown>
    </div>
  )
}

export default AgentSelector
