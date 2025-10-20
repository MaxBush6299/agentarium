/**
 * Agent Card Management Service
 * 
 * TypeScript service for managing A2A Protocol agent cards via REST API.
 * Enables dynamic agent registration and discovery from the frontend.
 */

export interface AgentSkill {
  id: string;
  name: string;
  description: string;
  tags: string[];
  examples: string[];
}

export interface AgentCapabilities {
  streaming: boolean;
  pushNotifications: boolean;
  stateTransitionHistory: boolean;
}

export interface AgentCard {
  protocolVersion: string;
  name: string;
  description: string;
  url: string;
  preferredTransport: string;
  version: string;
  provider?: string;
  capabilities: AgentCapabilities;
  skills: AgentSkill[];
  metadata?: Record<string, any>;
}

export interface CreateAgentCardRequest {
  agent_id: string;
  name: string;
  description: string;
  base_url: string;
  skills: Array<{
    id: string;
    name: string;
    description: string;
    tags: string[];
    examples: string[];
  }>;
  provider?: string;
  version?: string;
}

export interface UpdateAgentCardRequest {
  name?: string;
  description?: string;
  skills?: Array<{
    id: string;
    name: string;
    description: string;
    tags: string[];
    examples: string[];
  }>;
  provider?: string;
  version?: string;
}

export interface AgentCardResponse {
  agent_id: string;
  card: AgentCard;
}

export interface AgentCardListResponse {
  agent_ids: string[];
  count: number;
}

/**
 * Service for managing agent cards via REST API
 */
export class AgentCardService {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * List all registered agent cards
   */
  async listAgentCards(): Promise<AgentCardListResponse> {
    const response = await fetch(`${this.baseUrl}/api/agent-cards/`);
    
    if (!response.ok) {
      throw new Error(`Failed to list agent cards: ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Get a specific agent card by ID
   */
  async getAgentCard(agentId: string): Promise<AgentCardResponse> {
    const response = await fetch(`${this.baseUrl}/api/agent-cards/${agentId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Agent card not found: ${agentId}`);
      }
      throw new Error(`Failed to get agent card: ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Create a new agent card
   */
  async createAgentCard(request: CreateAgentCardRequest): Promise<AgentCardResponse> {
    const response = await fetch(`${this.baseUrl}/api/agent-cards/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      if (response.status === 409) {
        throw new Error(`Agent card already exists: ${request.agent_id}`);
      }
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(`Failed to create agent card: ${error.detail || response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Update an existing agent card
   */
  async updateAgentCard(
    agentId: string,
    request: UpdateAgentCardRequest
  ): Promise<AgentCardResponse> {
    const response = await fetch(`${this.baseUrl}/api/agent-cards/${agentId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Agent card not found: ${agentId}`);
      }
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(`Failed to update agent card: ${error.detail || response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Delete an agent card
   */
  async deleteAgentCard(agentId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/agent-cards/${agentId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Agent card not found: ${agentId}`);
      }
      throw new Error(`Failed to delete agent card: ${response.statusText}`);
    }
  }

  /**
   * Get combined agent card showing all registered agents
   */
  async getCombinedAgentCard(baseUrl?: string): Promise<AgentCard> {
    const url = new URL(`${this.baseUrl}/api/agent-cards/.well-known/combined`);
    if (baseUrl) {
      url.searchParams.set('base_url', baseUrl);
    }
    
    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error(`Failed to get combined agent card: ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Discover agent via A2A protocol well-known endpoint
   */
  async discoverAgent(): Promise<AgentCard> {
    const response = await fetch(`${this.baseUrl}/.well-known/agent.json`);
    
    if (!response.ok) {
      throw new Error(`Failed to discover agent: ${response.statusText}`);
    }
    
    return response.json();
  }
}

// Example usage:

/**
 * Example 1: List all agents
 */
export async function exampleListAgents() {
  const service = new AgentCardService();
  
  try {
    const { agent_ids, count } = await service.listAgentCards();
    console.log(`Found ${count} agents:`, agent_ids);
  } catch (error) {
    console.error('Error listing agents:', error);
  }
}

/**
 * Example 2: Create a new agent
 */
export async function exampleCreateAgent() {
  const service = new AgentCardService();
  
  try {
    const newAgent = await service.createAgentCard({
      agent_id: 'custom-agent',
      name: 'Custom Agent',
      description: 'An agent created from the frontend',
      base_url: 'http://localhost:8000',
      skills: [
        {
          id: 'custom-skill',
          name: 'Custom Skill',
          description: 'A custom skill for demonstration',
          tags: ['custom', 'demo', 'frontend'],
          examples: [
            'How do I use this custom agent?',
            'What can this agent do?',
          ],
        },
      ],
      provider: 'My Organization',
      version: '1.0.0',
    });
    
    console.log('Agent created:', newAgent);
  } catch (error) {
    console.error('Error creating agent:', error);
  }
}

/**
 * Example 3: Update an agent
 */
export async function exampleUpdateAgent() {
  const service = new AgentCardService();
  
  try {
    const updated = await service.updateAgentCard('custom-agent', {
      description: 'Updated description for the custom agent',
      version: '1.1.0',
    });
    
    console.log('Agent updated:', updated);
  } catch (error) {
    console.error('Error updating agent:', error);
  }
}

/**
 * Example 4: Get combined agent card
 */
export async function exampleGetCombinedCard() {
  const service = new AgentCardService();
  
  try {
    const combined = await service.getCombinedAgentCard();
    console.log('Combined agent card:');
    console.log(`  Name: ${combined.name}`);
    console.log(`  Skills: ${combined.skills.length}`);
    console.log(`  Agents: ${combined.metadata?.agent_ids?.join(', ')}`);
  } catch (error) {
    console.error('Error getting combined card:', error);
  }
}

/**
 * Example 5: Discover agent via A2A protocol
 */
export async function exampleDiscoverAgent() {
  const service = new AgentCardService();
  
  try {
    const agentCard = await service.discoverAgent();
    console.log('Agent discovered via A2A protocol:');
    console.log(`  Name: ${agentCard.name}`);
    console.log(`  Version: ${agentCard.version}`);
    console.log(`  Protocol Version: ${agentCard.protocolVersion}`);
    console.log(`  Skills available: ${agentCard.skills.length}`);
  } catch (error) {
    console.error('Error discovering agent:', error);
  }
}

/**
 * Example 6: Delete an agent
 */
export async function exampleDeleteAgent() {
  const service = new AgentCardService();
  
  try {
    await service.deleteAgentCard('custom-agent');
    console.log('Agent deleted successfully');
  } catch (error) {
    console.error('Error deleting agent:', error);
  }
}

/**
 * Complete workflow example
 */
export async function exampleCompleteWorkflow() {
  const service = new AgentCardService();
  
  console.log('=== Complete Agent Card Management Workflow ===\n');
  
  // 1. List existing agents
  console.log('1. Listing existing agents...');
  const { agent_ids: initialAgents } = await service.listAgentCards();
  console.log(`   Found: ${initialAgents.join(', ')}\n`);
  
  // 2. Create a new agent
  console.log('2. Creating new agent...');
  const newAgent = await service.createAgentCard({
    agent_id: 'workflow-demo',
    name: 'Workflow Demo Agent',
    description: 'Agent for demonstrating complete workflow',
    base_url: 'http://localhost:8000',
    skills: [
      {
        id: 'demo-skill',
        name: 'Demo Skill',
        description: 'Demonstrates workflow',
        tags: ['demo', 'workflow'],
        examples: ['Show me a demo'],
      },
    ],
    version: '1.0.0',
  });
  console.log(`   Created: ${newAgent.agent_id}\n`);
  
  // 3. Get the created agent
  console.log('3. Retrieving created agent...');
  const retrieved = await service.getAgentCard('workflow-demo');
  console.log(`   Name: ${retrieved.card.name}`);
  console.log(`   Version: ${retrieved.card.version}\n`);
  
  // 4. Update the agent
  console.log('4. Updating agent...');
  const updated = await service.updateAgentCard('workflow-demo', {
    description: 'Updated workflow demo agent',
    version: '1.1.0',
  });
  console.log(`   New version: ${updated.card.version}\n`);
  
  // 5. Get combined agent card
  console.log('5. Getting combined agent card...');
  const combined = await service.getCombinedAgentCard();
  console.log(`   Total agents: ${combined.metadata?.agent_count}`);
  console.log(`   Total skills: ${combined.skills.length}\n`);
  
  // 6. Discover via A2A protocol
  console.log('6. Discovering via A2A protocol...');
  const discovered = await service.discoverAgent();
  console.log(`   Protocol version: ${discovered.protocolVersion}`);
  console.log(`   Transport: ${discovered.preferredTransport}\n`);
  
  // 7. Clean up - delete the demo agent
  console.log('7. Cleaning up...');
  await service.deleteAgentCard('workflow-demo');
  console.log('   Demo agent deleted\n');
  
  // 8. Verify deletion
  console.log('8. Verifying deletion...');
  const { agent_ids: finalAgents } = await service.listAgentCards();
  console.log(`   Remaining agents: ${finalAgents.join(', ')}`);
  
  console.log('\n=== Workflow complete! ===');
}
