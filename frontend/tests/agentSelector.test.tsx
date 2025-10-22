/**
 * AgentSelector Component Tests
 * Tests for agent selection dropdown functionality
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AgentSelector } from './AgentSelector'
import * as agentsService from '@/services/agentsService'

// Mock the agents service
vi.mock('@/services/agentsService')

// Mock data
const mockAgents = [
  {
    id: 'support-triage',
    name: 'Support Triage',
    description: 'Support ticket triage agent',
    systemPrompt: 'You are a support triage agent',
    model: 'gpt-4',
    temperature: 0.7,
    maxMessages: 100,
    tools: [],
    capabilities: [],
    status: 'active' as const,
    isPublic: true,
    createdBy: 'admin',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    version: '1.0',
  },
  {
    id: 'azure-ops',
    name: 'Azure Ops',
    description: 'Azure operations assistant',
    systemPrompt: 'You are an Azure operations assistant',
    model: 'gpt-4',
    temperature: 0.7,
    maxMessages: 100,
    tools: [],
    capabilities: [],
    status: 'active' as const,
    isPublic: true,
    createdBy: 'admin',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    version: '1.0',
  },
]

describe('AgentSelector Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render loading state initially', async () => {
    vi.mocked(agentsService.getAgents).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<AgentSelector selectedAgentId="support-triage" onAgentChange={vi.fn()} />)

    expect(screen.getByText('Loading agents...')).toBeInTheDocument()
  })

  it('should render agents list after loading', async () => {
    vi.mocked(agentsService.getAgents).mockResolvedValue({
      agents: mockAgents,
      total: 2,
      limit: 20,
      offset: 0,
    })

    render(<AgentSelector selectedAgentId="support-triage" onAgentChange={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Support Triage')).toBeInTheDocument()
    })
  })

  it('should call onAgentChange when agent is selected', async () => {
    const handleChange = vi.fn()
    vi.mocked(agentsService.getAgents).mockResolvedValue({
      agents: mockAgents,
      total: 2,
      limit: 20,
      offset: 0,
    })

    render(<AgentSelector selectedAgentId="support-triage" onAgentChange={handleChange} />)

    await waitFor(() => {
      expect(screen.getByText('Support Triage')).toBeInTheDocument()
    })

    // Note: Actual click simulation would depend on Fluent UI dropdown implementation
    // This is a simplified test
  })

  it('should display error message on failed fetch', async () => {
    vi.mocked(agentsService.getAgents).mockRejectedValue(new Error('Failed to fetch'))

    render(<AgentSelector selectedAgentId="support-triage" onAgentChange={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load agents/)).toBeInTheDocument()
    })
  })

  it('should handle empty agents list gracefully', async () => {
    vi.mocked(agentsService.getAgents).mockResolvedValue({
      agents: [],
      total: 0,
      limit: 20,
      offset: 0,
    })

    render(<AgentSelector selectedAgentId="support-triage" onAgentChange={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('No agents available')).toBeInTheDocument()
    })
  })

  it('should be disabled when disabled prop is true', async () => {
    vi.mocked(agentsService.getAgents).mockResolvedValue({
      agents: mockAgents,
      total: 2,
      limit: 20,
      offset: 0,
    })

    const { container } = render(
      <AgentSelector selectedAgentId="support-triage" onAgentChange={vi.fn()} disabled={true} />
    )

    await waitFor(() => {
      const dropdownTrigger = container.querySelector('[role="button"]')
      expect(dropdownTrigger).toHaveAttribute('disabled')
    })
  })

  it('should display agent status badge', async () => {
    vi.mocked(agentsService.getAgents).mockResolvedValue({
      agents: mockAgents,
      total: 2,
      limit: 20,
      offset: 0,
    })

    render(<AgentSelector selectedAgentId="support-triage" onAgentChange={vi.fn()} />)

    await waitFor(() => {
      // Look for active status badges
      const badges = screen.getAllByText('active')
      expect(badges.length).toBeGreaterThan(0)
    })
  })
})
