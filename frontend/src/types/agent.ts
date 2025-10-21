/**
 * Agent-related TypeScript types
 * Matches backend models from Phase 2.12
 */

export enum AgentStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  MAINTENANCE = 'maintenance',
}

export enum ToolType {
  MCP = 'mcp',
  OPENAPI = 'openapi',
  A2A = 'a2a',
  BUILTIN = 'builtin',
}

export interface ToolConfig {
  type: ToolType
  name: string
  mcpServerName?: string
  openapiSpecPath?: string
  a2aAgentId?: string
  config?: Record<string, any>
  enabled: boolean
}

export interface AgentMetadata {
  id: string
  name: string
  description: string
  systemPrompt: string
  
  // Model configuration
  model: string
  temperature: number
  maxTokens?: number
  maxMessages: number
  
  // Tools and capabilities
  tools: ToolConfig[]
  capabilities: string[]
  
  // Status and visibility
  status: AgentStatus
  isPublic: boolean
  
  // Metadata
  createdBy: string
  createdAt: string
  updatedAt: string
  version: string
  
  // Statistics (optional, from backend stats tracking)
  totalRuns?: number
  totalTokens?: number
  avgLatencyMs?: number
}

// Alias for backward compatibility
export type Agent = AgentMetadata

export interface AgentCreateRequest {
  id: string
  name: string
  description: string
  systemPrompt: string
  model?: string
  temperature?: number
  maxTokens?: number
  maxMessages?: number
  tools?: ToolConfig[]
  capabilities?: string[]
  status?: AgentStatus
  isPublic?: boolean
  version?: string
}

export interface AgentUpdateRequest {
  name?: string
  description?: string
  systemPrompt?: string
  model?: string
  temperature?: number
  maxTokens?: number
  maxMessages?: number
  tools?: ToolConfig[]
  capabilities?: string[]
  status?: AgentStatus
  isPublic?: boolean
  version?: string
}

export interface AgentListResponse {
  agents: Agent[]
  total: number
  limit: number
  offset: number
}
