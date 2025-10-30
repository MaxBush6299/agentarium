/**
 * Workflows Service
 * API calls for workflow management
 */

import { Workflow } from '@/types/workflow'
import { apiGet, apiPost, apiPut, apiDelete } from './api'

const WORKFLOWS_ENDPOINT = '/workflows'

/**
 * Get list of all workflows
 */
export const listWorkflows = async (): Promise<Record<string, Workflow>> => {
  return apiGet<Record<string, Workflow>>(WORKFLOWS_ENDPOINT)
}

/**
 * Get a specific workflow by ID
 */
export const getWorkflow = async (workflowId: string): Promise<Workflow> => {
  return apiGet<Workflow>(`${WORKFLOWS_ENDPOINT}/${workflowId}`)
}

/**
 * Create a new workflow
 */
export const createWorkflow = async (workflow: Workflow): Promise<Workflow> => {
  return apiPost<Workflow>(WORKFLOWS_ENDPOINT, workflow)
}

/**
 * Update an existing workflow
 */
export const updateWorkflow = async (workflowId: string, workflow: Partial<Workflow>): Promise<Workflow> => {
  return apiPut<Workflow>(`${WORKFLOWS_ENDPOINT}/${workflowId}`, workflow)
}

/**
 * Delete a workflow
 */
export const deleteWorkflow = async (workflowId: string): Promise<void> => {
  return apiDelete<void>(`${WORKFLOWS_ENDPOINT}/${workflowId}`)
}
