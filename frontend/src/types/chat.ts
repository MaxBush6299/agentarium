/**
 * Chat and conversation-related TypeScript types
 */

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  traces?: Trace[]
}

export interface ChatThread {
  id: string
  agentId: string
  title: string
  createdAt: string
  updatedAt: string
  messages: Message[]
}

export interface ChatRequest {
  threadId?: string
  agentId: string
  message: string
}

export interface ToolCall {
  id: string
  name: string
  input: Record<string, unknown>
  output?: Record<string, unknown>
  duration: number
  status: 'pending' | 'success' | 'error'
  error?: string
}

export interface Trace {
  id: string
  type: 'tool_call' | 'a2a_call' | 'model_call'
  name: string
  input?: Record<string, unknown>
  output?: Record<string, unknown>
  duration: number
  status: 'pending' | 'success' | 'error'
  error?: string
  children?: Trace[]
  metadata?: Record<string, unknown>
}

export interface StreamEvent {
  type: 'token' | 'trace_start' | 'trace_update' | 'trace_end' | 'done' | 'error'
  data: unknown
  timestamp: string
}
