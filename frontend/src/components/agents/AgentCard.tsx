/**
 * Agent Card Component
 * Displays agent information in a card format
 */

import { useNavigate } from 'react-router-dom'
import {
  Card,
  CardHeader,
  Button,
  Badge,
  makeStyles,
  tokens,
  Tooltip,
} from '@fluentui/react-components'
import {
  Play24Regular,
  Settings24Regular,
} from '@fluentui/react-icons'
import { Agent, AgentStatus, ToolType } from '@/types/agent'
import { AgentManagementDialog } from './AgentManagementDialog'

const useStyles = makeStyles({
  card: {
    height: '300px',
    cursor: 'pointer',
    background: 'linear-gradient(135deg, #1a2530 0%, #243240 100%)',
    border: '1px solid #2d3e4a',
    boxShadow: '0 2px 8px rgba(27, 137, 187, 0.2)',
    transition: 'all 0.3s ease',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 8px 16px rgba(59, 176, 221, 0.3)',
      border: '1px solid #3fb0dd',
    },
  },
  content: {
    padding: '24px',
  },
  title: {
    fontSize: '20px',
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: '12px',
    color: '#f0fcff',
  },
  description: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: '#bdeffc',
    marginBottom: '20px',
    minHeight: '80px',
  },
  badges: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginBottom: '16px',
  },
  stats: {
    display: 'flex',
    gap: '16px',
    marginBottom: '16px',
    fontSize: '12px',
    color: tokens.colorNeutralForeground3,
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column',
  },
  statLabel: {
    fontWeight: tokens.fontWeightSemibold,
  },
  actions: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  tools: {
    display: 'flex',
    gap: '4px',
    marginTop: '8px',
  },
})

interface AgentCardProps {
  agent: Agent
  onAgentDeleted?: (agentId: string) => void
}

/**
 * AgentCard Component
 */
export const AgentCard = ({ agent, onAgentDeleted }: AgentCardProps) => {
  const styles = useStyles()
  const navigate = useNavigate()

  const handleChat = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigate('/chat', { state: { agentId: agent.id } })
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigate(`/agents/${agent.id}/edit`)
  }

  const getStatusColor = (status: AgentStatus) => {
    switch (status) {
      case AgentStatus.ACTIVE:
        return 'success'
      case AgentStatus.INACTIVE:
        return 'subtle'
      case AgentStatus.MAINTENANCE:
        return 'warning'
      default:
        return 'subtle'
    }
  }

  const getToolIcon = (toolType: ToolType) => {
    switch (toolType) {
      case ToolType.MCP:
        return '🔌'
      case ToolType.OPENAPI:
        return '🌐'
      case ToolType.A2A:
        return '🤝'
      case ToolType.BUILTIN:
        return '⚙️'
      default:
        return '🔧'
    }
  }

  return (
    <Card className={styles.card}>
      <div className={styles.content}>
        <CardHeader
          header={<div className={styles.title}>{agent.name}</div>}
          description={
            <div className={styles.badges}>
              <Badge appearance="filled" color={getStatusColor(agent.status)}>
                {agent.status.toUpperCase()}
              </Badge>
              <Badge appearance="outline">{agent.model}</Badge>
              {!agent.isPublic && (
                <Badge appearance="outline" color="important">
                  Private
                </Badge>
              )}
            </div>
          }
        />

        <p className={styles.description}>{agent.description}</p>

        {agent.totalRuns !== undefined && (
          <div className={styles.stats}>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>
                {agent.totalRuns?.toLocaleString() || 0}
              </span>
              <span>Runs</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>
                {agent.totalTokens?.toLocaleString() || 0}
              </span>
              <span>Tokens</span>
            </div>
            {agent.avgLatencyMs && (
              <div className={styles.statItem}>
                <span className={styles.statLabel}>
                  {agent.avgLatencyMs.toFixed(0)}ms
                </span>
                <span>Avg Latency</span>
              </div>
            )}
          </div>
        )}

        {agent.tools.length > 0 && (
          <div className={styles.tools}>
            {agent.tools.slice(0, 5).map((tool, index) => (
              <Tooltip
                key={index}
                content={`${tool.type}: ${tool.name}`}
                relationship="label"
              >
                <Badge size="small" appearance="outline">
                  {getToolIcon(tool.type)} {tool.name}
                </Badge>
              </Tooltip>
            ))}
            {agent.tools.length > 5 && (
              <Badge size="small" appearance="outline">
                +{agent.tools.length - 5} more
              </Badge>
            )}
          </div>
        )}

        <div className={styles.actions}>
          <Button
            appearance="primary"
            icon={<Play24Regular />}
            onClick={handleChat}
            disabled={agent.status !== AgentStatus.ACTIVE}
          >
            Start Chat
          </Button>
          <Button
            appearance="subtle"
            icon={<Settings24Regular />}
            onClick={handleEdit}
          >
            Edit
          </Button>
          <AgentManagementDialog agent={agent} onAgentDeleted={onAgentDeleted} />
        </div>
      </div>
    </Card>
  )
}
