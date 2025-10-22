import { z } from 'zod';

/**
 * Validation schema for agent configuration form
 * Used with react-hook-form + zod for type-safe form validation
 */

export const ToolSchema = z.object({
  type: z.enum(['mcp', 'openapi', 'a2a']),
  name: z.string().min(1, 'Tool name is required'),
  enabled: z.boolean().default(true),
});

export const AgentFormSchema = z.object({
  id: z.string(),
  name: z.string()
    .min(1, 'Agent name is required')
    .min(3, 'Agent name must be at least 3 characters')
    .max(100, 'Agent name must be less than 100 characters'),
  description: z.string()
    .min(10, 'Description must be at least 10 characters')
    .max(500, 'Description must be less than 500 characters'),
  system_prompt: z.string()
    .min(50, 'System prompt must be at least 50 characters')
    .max(4000, 'System prompt must be less than 4000 characters'),
  model: z.string()
    .min(1, 'Model selection is required'),
  temperature: z.number()
    .min(0, 'Temperature must be between 0 and 2')
    .max(2, 'Temperature must be between 0 and 2')
    .default(0.7),
  max_tokens: z.number()
    .min(100, 'Max tokens must be at least 100')
    .max(8000, 'Max tokens must be less than 8000')
    .default(4000),
  max_messages: z.number()
    .min(5, 'Max messages must be at least 5')
    .max(100, 'Max messages must be less than 100')
    .default(20),
  capabilities: z.array(z.string())
    .default([])
    .describe('Agent capabilities for discovery and filtering'),
  status: z.enum(['active', 'inactive', 'maintenance']).default('active'),
  tools: z.array(ToolSchema)
    .min(1, 'At least one tool must be selected'),
});

export type AgentFormData = z.infer<typeof AgentFormSchema>;
export type ToolData = z.infer<typeof ToolSchema>;

/**
 * Available models for deployment
 * Can be fetched from backend config in future
 */
export const AVAILABLE_MODELS = [
  { id: 'gpt-4o', label: 'GPT-4o (Latest)' },
  { id: 'gpt-4.1', label: 'GPT-4.1' },
  { id: 'gpt-4', label: 'GPT-4' },
  { id: 'gpt-35-turbo', label: 'GPT-3.5 Turbo' },
] as const;

/**
 * Tool categories for organization in ToolConfigurator
 */
export const TOOL_CATEGORIES = {
  MCP: {
    label: 'MCP Tools',
    tools: [
      { type: 'mcp' as const, name: 'microsoft-learn', label: 'Microsoft Learn Documentation' },
      { type: 'mcp' as const, name: 'azure-mcp', label: 'Azure Management' },
    ],
  },
  OPENAPI: {
    label: 'OpenAPI APIs',
    tools: [
      { type: 'openapi' as const, name: 'support-triage-api', label: 'Support Triage API' },
      { type: 'openapi' as const, name: 'ops-assistant-api', label: 'Operations Assistant API' },
    ],
  },
  A2A: {
    label: 'A2A Agents',
    tools: [
      // These would be dynamically fetched from backend in production
      // { type: 'a2a' as const, name: 'news-agent', label: 'News Agent' },
      // { type: 'a2a' as const, name: 'sql-agent', label: 'SQL Agent' },
    ],
  },
} as const;
