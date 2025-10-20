/**
 * Agent-related TypeScript types
 */

export interface Agent {
  id: string
  name: string
  description: string
  systemPrompt: string
  model: string
  temperature: number
  maxTokens: number
  tools: string[]
  createdAt: string
  updatedAt: string
}

export interface AgentCreateRequest {
  name: string
  description: string
  systemPrompt: string
  model: string
  temperature: number
  maxTokens: number
  tools: string[]
}

export interface AgentUpdateRequest extends Partial<AgentCreateRequest> {
  id: string
}

export interface AgentListResponse {
  agents: Agent[]
  total: number
}
