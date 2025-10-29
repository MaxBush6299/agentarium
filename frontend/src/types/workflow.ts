/**
 * Workflow Type Definition
 */

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: string;
  associatedAgents: string[];
}