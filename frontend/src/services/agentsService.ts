/**
 * Agents Service
 * API calls for agent management (CRUD operations)
 */

import { Agent, AgentCreateRequest, AgentUpdateRequest, AgentListResponse } from '@/types/agent'
import { apiGet, apiPost, apiPut, apiDelete } from './api'

const AGENTS_ENDPOINT = '/agents'

/**
 * Get list of agents
 */
export const getAgents = async (
  skip: number = 0,
  limit: number = 20
): Promise<AgentListResponse> => {
  return apiGet(`${AGENTS_ENDPOINT}?skip=${skip}&limit=${limit}`)
}

/**
 * Get agent by ID
 */
export const getAgent = async (agentId: string): Promise<Agent> => {
  return apiGet(`${AGENTS_ENDPOINT}/${agentId}`)
}

/**
 * Create new agent
 */
export const createAgent = async (request: AgentCreateRequest): Promise<Agent> => {
  return apiPost(AGENTS_ENDPOINT, request)
}

/**
 * Update existing agent
 */
export const updateAgent = async (agentId: string, request: AgentUpdateRequest): Promise<Agent> => {
  return apiPut(`${AGENTS_ENDPOINT}/${agentId}`, request)
}

/**
 * Delete agent
 */
export const deleteAgent = async (agentId: string): Promise<void> => {
  return apiDelete(`${AGENTS_ENDPOINT}/${agentId}`)
}

/**
 * Get agent by name
 */
export const getAgentByName = async (name: string): Promise<Agent> => {
  return apiGet(`${AGENTS_ENDPOINT}/by-name/${name}`)
}

/**
 * Search agents by query
 */
export const searchAgents = async (query: string): Promise<Agent[]> => {
  return apiGet(`${AGENTS_ENDPOINT}/search?q=${encodeURIComponent(query)}`)
}
