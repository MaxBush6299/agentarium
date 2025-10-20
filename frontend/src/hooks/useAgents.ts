/**
 * useAgents Hook
 * Custom hook for managing agents list
 */

import { useState, useCallback } from 'react'
import { Agent, AgentCreateRequest, AgentUpdateRequest } from '@/types/agent'
import {
  getAgents as fetchAgents,
  getAgent as fetchAgent,
  createAgent as createNewAgent,
  updateAgent as updateExistingAgent,
  deleteAgent as deleteExistingAgent,
  searchAgents as performSearch,
} from '@/services/agentsService'

export interface UseAgentsState {
  agents: Agent[]
  selectedAgent: Agent | null
  isLoading: boolean
  error: string | null
  totalCount: number
  skip: number
  limit: number
}

export const useAgents = () => {
  const [state, setState] = useState<UseAgentsState>({
    agents: [],
    selectedAgent: null,
    isLoading: false,
    error: null,
    totalCount: 0,
    skip: 0,
    limit: 20,
  })

  // Get agents list
  const getAgentsList = useCallback(async (skip = 0, limit = 20) => {
    try {
      setState((prev: any) => ({ ...prev, isLoading: true, error: null }))
      const response = await fetchAgents(skip, limit)
      setState((prev: any) => ({
        ...prev,
        agents: response.items,
        totalCount: response.total,
        skip,
        limit,
        isLoading: false,
      }))
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch agents'
      setState((prev: any) => ({
        ...prev,
        error: message,
        isLoading: false,
      }))
    }
  }, [])

  // Get single agent
  const getAgent = useCallback(async (agentId: string) => {
    try {
      setState((prev: any) => ({ ...prev, isLoading: true, error: null }))
      const agent = await fetchAgent(agentId)
      setState((prev: any) => ({
        ...prev,
        selectedAgent: agent,
        isLoading: false,
      }))
      return agent
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch agent'
      setState((prev: any) => ({
        ...prev,
        error: message,
        isLoading: false,
      }))
      throw error
    }
  }, [])

  // Create new agent
  const create = useCallback(async (request: AgentCreateRequest) => {
    try {
      setState((prev: any) => ({ ...prev, isLoading: true, error: null }))
      const agent = await createNewAgent(request)
      setState((prev: any) => ({
        ...prev,
        agents: [agent, ...prev.agents],
        totalCount: prev.totalCount + 1,
        isLoading: false,
      }))
      return agent
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create agent'
      setState((prev: any) => ({
        ...prev,
        error: message,
        isLoading: false,
      }))
      throw error
    }
  }, [])

  // Update agent
  const update = useCallback(async (agentId: string, request: AgentUpdateRequest) => {
    try {
      setState((prev: any) => ({ ...prev, isLoading: true, error: null }))
      const agent = await updateExistingAgent(agentId, request)
      setState((prev: any) => ({
        ...prev,
        agents: prev.agents.map((a: Agent) => (a.id === agentId ? agent : a)),
        selectedAgent: prev.selectedAgent?.id === agentId ? agent : prev.selectedAgent,
        isLoading: false,
      }))
      return agent
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update agent'
      setState((prev: any) => ({
        ...prev,
        error: message,
        isLoading: false,
      }))
      throw error
    }
  }, [])

  // Delete agent
  const deleteAgent = useCallback(async (agentId: string) => {
    try {
      setState((prev: any) => ({ ...prev, isLoading: true, error: null }))
      await deleteExistingAgent(agentId)
      setState((prev: any) => ({
        ...prev,
        agents: prev.agents.filter((a: Agent) => a.id !== agentId),
        selectedAgent: prev.selectedAgent?.id === agentId ? null : prev.selectedAgent,
        totalCount: prev.totalCount - 1,
        isLoading: false,
      }))
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete agent'
      setState((prev: any) => ({
        ...prev,
        error: message,
        isLoading: false,
      }))
      throw error
    }
  }, [])

  // Search agents
  const search = useCallback(async (query: string) => {
    try {
      setState((prev: any) => ({ ...prev, isLoading: true, error: null }))
      const agents = await performSearch(query)
      setState((prev: any) => ({
        ...prev,
        agents,
        isLoading: false,
      }))
      return agents
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to search agents'
      setState((prev: any) => ({
        ...prev,
        error: message,
        isLoading: false,
      }))
      throw error
    }
  }, [])

  return {
    ...state,
    getAgentsList,
    getAgent,
    create,
    update,
    deleteAgent,
    search,
  }
}
