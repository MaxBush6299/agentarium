/**
 * Agents Page
 * Browse and view available agents
 */

import { useState, useEffect } from 'react'
import {
  Spinner,
  makeStyles,
  tokens,
  SearchBox,
  Badge,
  Button,
} from '@fluentui/react-components'
import { getAgents } from '@/services/agentsService'
import { Agent } from '@/types/agent'
import { AgentCard } from '@/components/agents/AgentCard'

type FilterType = 'all' | 'active' | 'inactive'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    padding: '24px',
    background: 'linear-gradient(135deg, #0e1419 0%, #1a2530 100%)',
  },
  header: {
    marginBottom: '24px',
  },
  title: {
    fontSize: '28px',
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: '8px',
    color: '#f0fcff',
  },
  subtitle: {
    fontSize: '14px',
    color: '#7ad4f0',
    marginBottom: '16px',
  },
  searchContainer: {
    marginBottom: '24px',
    maxWidth: '500px',
  },
  agentsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(450px, 1fr))',
    gap: '32px',
    overflow: 'auto',
    alignItems: 'start',
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
  },
  error: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: tokens.colorPaletteRedForeground1,
  },
  empty: {
    textAlign: 'center',
    padding: '48px',
    color: tokens.colorNeutralForeground3,
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
})

/**
 * AgentsPage Component
 */
export const AgentsPage = () => {
  const styles = useStyles()
  const [agents, setAgents] = useState<Agent[]>([])
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<FilterType>('all')

  useEffect(() => {
    loadAgents()
  }, [])

  useEffect(() => {
    let filtered = agents

    // Apply status filter
    if (statusFilter === 'active') {
      filtered = filtered.filter(a => a.status === 'active')
    } else if (statusFilter === 'inactive') {
      filtered = filtered.filter(a => a.status !== 'active')
    }

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (agent) =>
          agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          agent.description.toLowerCase().includes(searchQuery.toLowerCase())
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

  const handleAgentDeleted = (agentId: string) => {
    // Remove the deleted agent from the list
    setAgents((prev) => prev.filter((agent) => agent.id !== agentId))
    setFilteredAgents((prev) => prev.filter((agent) => agent.id !== agentId))
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spinner label="Loading agents..." size="large" />
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.error}>
        <h2>Error Loading Agents</h2>
        <p>{error}</p>
      </div>
    )
  }

  const activeCount = agents.filter(a => a.status === 'active').length
  const inactiveCount = agents.length - activeCount

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Available Agents</h1>
        <p className={styles.subtitle}>
          Browse and explore our AI agents with specialized capabilities
        </p>
        <div className={styles.statsContainer}>
          <Button
            appearance={statusFilter === 'active' ? 'primary' : 'outline'}
            className={styles.filterButton}
            onClick={() => setStatusFilter('active')}
          >
            <Badge 
              appearance="filled" 
              color="success"
              style={{ marginRight: '8px' }}
            >
              {activeCount}
            </Badge>
            Active
          </Button>
          <Button
            appearance={statusFilter === 'inactive' ? 'primary' : 'outline'}
            className={styles.filterButton}
            onClick={() => setStatusFilter('inactive')}
          >
            <Badge 
              appearance="filled" 
              color="important"
              style={{ marginRight: '8px' }}
            >
              {inactiveCount}
            </Badge>
            Inactive
          </Button>
          <Button
            appearance={statusFilter === 'all' ? 'primary' : 'outline'}
            className={styles.filterButton}
            onClick={() => setStatusFilter('all')}
          >
            <Badge 
              appearance="outline"
              style={{ marginRight: '8px' }}
            >
              {agents.length}
            </Badge>
            Total
          </Button>
        </div>
      </div>

      <div className={styles.searchContainer}>
        <SearchBox
          placeholder="Search agents by name or description..."
          value={searchQuery}
          onChange={(_, data) => setSearchQuery(data.value)}
        />
      </div>

      {filteredAgents.length === 0 ? (
        <div className={styles.empty}>
          <h3>No agents found</h3>
          <p>Try adjusting your search query</p>
        </div>
      ) : (
        <div className={styles.agentsGrid}>
          {filteredAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} onAgentDeleted={handleAgentDeleted} />
          ))}
        </div>
      )}
    </div>
  )
}
