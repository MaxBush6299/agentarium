/**
 * Agents Page
 * Browse and view available agents
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Spinner,
  makeStyles,
  tokens,
  SearchBox,
  Badge,
  Button,
} from '@fluentui/react-components'
import { Add24Regular } from '@fluentui/react-icons'
import { getAgents } from '@/services/agentsService'
import { Agent } from '@/types/agent'
import { AgentCard } from '@/components/agents/AgentCard'
import { WorkflowCard } from '@/components/workflows/WorkflowCard'
import { AgentCardService } from '@/services/agentCardService'
import { Workflow } from '../types/workflow'

type FilterType = 'all' | 'active' | 'inactive'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    padding: '24px',
    background: 'linear-gradient(135deg, #0e1419 0%, #1a2530 100%)',
    overflowY: 'auto', // single page-level scrollbar
    boxSizing: 'border-box',
  },

  // Generic section block with its own header + content
  section: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
  },

  // Optional inner scroll area (disabled by default; see JSX comment)
  scrollArea: {
    // turn this on if you want a second scrollbar for huge lists:
    // maxHeight: '70vh',
    // overflowY: 'auto',
  },

  sectionHeader: {
    marginBottom: '16px',
  },
  sectionTitle: {
    fontSize: '28px',
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: '8px',
    color: '#f0fcff',
  },
  sectionSubtitle: {
    fontSize: '14px',
    color: '#7ad4f0',
  },

  // whitespace strip between sections
  sectionSpacer: {
    height: '48px',
  },

  topBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },

  searchContainer: {
    marginBottom: '24px',
    maxWidth: '500px',
  },

  statsContainer: {
    display: 'flex',
    gap: '12px',
    marginBottom: '16px',
    flexWrap: 'wrap',
  },
  filterButton: {
    minWidth: '100px',
  },

  // Responsive, natural-height grids (no maxHeight, no nested scrolling)
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
    gap: '32px',
    alignItems: 'start',
  },

  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '200px',
  },
  error: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    color: tokens.colorPaletteRedForeground1,
    padding: '24px',
  },
  empty: {
    textAlign: 'center',
    padding: '48px',
    color: tokens.colorNeutralForeground3,
  },
})

export const AgentsPage = () => {
  const styles = useStyles()
  const navigate = useNavigate()
  const [agents, setAgents] = useState<Agent[]>([])
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<FilterType>('all')
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loadingWorkflows, setLoadingWorkflows] = useState(true)
  const [workflowError, setWorkflowError] = useState<string | null>(null)

  useEffect(() => {
    loadAgents()
  }, [])

  useEffect(() => {
    let filtered = agents

    if (statusFilter === 'active') {
      filtered = filtered.filter(a => a.status === 'active')
    } else if (statusFilter === 'inactive') {
      filtered = filtered.filter(a => a.status !== 'active')
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      filtered = filtered.filter(
        a =>
          a.name.toLowerCase().includes(q) ||
          a.description.toLowerCase().includes(q)
      )
    }

    setFilteredAgents(filtered)
  }, [searchQuery, agents, statusFilter])

  const loadAgents = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getAgents(0, 100)
      setAgents(response.agents)
      setFilteredAgents(response.agents)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agents')
    } finally {
      setLoading(false)
    }
  }

  const loadWorkflows = async () => {
    try {
      setLoadingWorkflows(true)
      setWorkflowError(null)
      const response = await new AgentCardService().listWorkflows()
      setWorkflows(Object.values(response))
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : 'Failed to load workflows')
    } finally {
      setLoadingWorkflows(false)
    }
  }

  useEffect(() => {
    loadWorkflows()
  }, [])

  const handleAgentDeleted = (agentId: string) => {
    setAgents(prev => prev.filter(a => a.id !== agentId))
    setFilteredAgents(prev => prev.filter(a => a.id !== agentId))
  }

  const activeCount = agents.filter(a => a.status === 'active').length
  const inactiveCount = agents.length - activeCount

  return (
    <div className={styles.container}>
      {/* Top bar */}
      <div className={styles.topBar}>
        <div>
          <h1 className={styles.sectionTitle}>Available Agents</h1>
          <p className={styles.sectionSubtitle}>
            Browse and explore our AI agents with specialized capabilities
          </p>
        </div>
        <Button
          appearance="primary"
          icon={<Add24Regular />}
          onClick={() => navigate('/agents/new')}
        >
          Create New Agent
        </Button>
      </div>

      {/* Agents section */}
      <section className={styles.section} aria-label="Available Agents">
        <div className={styles.statsContainer}>
          <Button
            appearance={statusFilter === 'active' ? 'primary' : 'outline'}
            className={styles.filterButton}
            onClick={() => setStatusFilter('active')}
          >
            <Badge appearance="filled" color="success" style={{ marginRight: 8 }}>
              {activeCount}
            </Badge>
            Active
          </Button>
          <Button
            appearance={statusFilter === 'inactive' ? 'primary' : 'outline'}
            className={styles.filterButton}
            onClick={() => setStatusFilter('inactive')}
          >
            <Badge appearance="filled" color="important" style={{ marginRight: 8 }}>
              {inactiveCount}
            </Badge>
            Inactive
          </Button>
          <Button
            appearance={statusFilter === 'all' ? 'primary' : 'outline'}
            className={styles.filterButton}
            onClick={() => setStatusFilter('all')}
          >
            <Badge appearance="outline" style={{ marginRight: 8 }}>
              {agents.length}
            </Badge>
            Total
          </Button>
        </div>

        <div className={styles.searchContainer}>
          <SearchBox
            placeholder="Search agents by name or description..."
            value={searchQuery}
            onChange={(_, data) => setSearchQuery(data.value)}
          />
        </div>

        {loading ? (
          <div className={styles.loading}>
            <Spinner label="Loading agents..." size="large" />
          </div>
        ) : error ? (
          <div className={styles.error}>
            <h2>Error Loading Agents</h2>
            <p>{error}</p>
          </div>
        ) : filteredAgents.length === 0 ? (
          <div className={styles.empty}>
            <h3>No agents found</h3>
            <p>Try adjusting your search query</p>
          </div>
        ) : (
          // If you want per-section scrolling, wrap this grid
          // with <div className={styles.scrollArea}> ... </div>
          <div className={styles.grid}>
            {filteredAgents.map(agent => (
              <AgentCard key={agent.id} agent={agent} onAgentDeleted={handleAgentDeleted} />
            ))}
          </div>
        )}
      </section>

      {/* whitespace strip between sections */}
      <div className={styles.sectionSpacer} />

      {/* Workflows section */}
      <section className={styles.section} aria-label="Available Workflows">
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Available Workflows</h2>
          <p className={styles.sectionSubtitle}>Browse and explore workflows</p>
        </div>

        {loadingWorkflows ? (
          <div className={styles.loading}>
            <Spinner label="Loading workflows..." size="large" />
          </div>
        ) : workflowError ? (
          <div className={styles.error}>
            <h2>Error Loading Workflows</h2>
            <p>{workflowError}</p>
          </div>
        ) : workflows.length === 0 ? (
          <div className={styles.empty}>
            <h3>No workflows found</h3>
            <p>Try adjusting your search query</p>
          </div>
        ) : (
          // Optional inner scroll: wrap with styles.scrollArea if desired
          <div className={styles.grid}>
            {workflows.map(workflow => (
              <WorkflowCard key={workflow.id} workflow={workflow} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
