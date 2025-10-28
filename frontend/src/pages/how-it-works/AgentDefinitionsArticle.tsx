import React from 'react';
import { ArticleLayout } from './ArticleLayout';

export const AgentDefinitionsArticle: React.FC = () => {
  return (
    <ArticleLayout
      title="Agent Definitions in Agentarium"
      date="October 28, 2025"
      author="Engineering Team"
    >
      <h2>What is an Agent?</h2>
      <p>
        An <strong>agent</strong> is an AI-powered assistant with a specific purpose, personality, and set of tools.
        Think of it like hiring a specialist—a sales expert, a warehouse manager, or a technical support specialist—who
        can access specific systems and provide expert assistance.
      </p>

      <p><strong>Example Agents in Agentarium:</strong></p>
      <ul>
        <li><strong>Support Triage Agent:</strong> Analyzes customer issues and routes them appropriately</li>
        <li><strong>Azure Operations Agent:</strong> Helps manage Azure resources and troubleshoot problems</li>
        <li><strong>Sales Agent:</strong> Answers questions about customers, products, and sales data</li>
        <li><strong>Warehouse Agent:</strong> Manages inventory, orders, and shipping information</li>
      </ul>

      <h2>How Are Agents Defined?</h2>
      <p>
        Each agent in Agentarium is defined by a configuration stored in <strong>Cosmos DB</strong>. This configuration
        acts like a "job description" that tells the system:
      </p>
      <ul>
        <li>📝 <strong>What the agent should do</strong> (system prompt/instructions)</li>
        <li>🤖 <strong>Which AI model to use</strong> (GPT-4o, GPT-4.1, etc.)</li>
        <li>🛠️ <strong>What tools it can access</strong> (databases, APIs, documentation)</li>
        <li>⚙️ <strong>How it should behave</strong> (temperature, response length)</li>
        <li>📊 <strong>Usage statistics</strong> (how many times it's been used, performance metrics)</li>
      </ul>

      <h2>Agent Configuration Structure</h2>
      <p>Each agent is defined using a structured schema:</p>

      <table>
        <thead>
          <tr>
            <th>Field</th>
            <th>Description</th>
            <th>Example</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>id</code></td>
            <td>Unique identifier</td>
            <td>"sales-agent"</td>
          </tr>
          <tr>
            <td><code>name</code></td>
            <td>Display name</td>
            <td>"Sales Intelligence Agent"</td>
          </tr>
          <tr>
            <td><code>system_prompt</code></td>
            <td>Instructions that define behavior</td>
            <td>"You are a sales analyst who helps..."</td>
          </tr>
          <tr>
            <td><code>model</code></td>
            <td>AI model to use</td>
            <td>"gpt-4o"</td>
          </tr>
          <tr>
            <td><code>temperature</code></td>
            <td>Creativity level (0.0-1.0)</td>
            <td>0.7</td>
          </tr>
          <tr>
            <td><code>tools</code></td>
            <td>Available tools/capabilities</td>
            <td>[microsoft-docs, sales-database]</td>
          </tr>
          <tr>
            <td><code>max_messages</code></td>
            <td>Conversation memory window</td>
            <td>20</td>
          </tr>
        </tbody>
      </table>

      <h2>The Microsoft Agent Framework</h2>
      <p>
        Under the hood, Agentarium uses Microsoft's <strong>Agent Framework</strong> to power all agents.
        This framework provides:
      </p>
      <ul>
        <li><strong>ChatAgent Class:</strong> The core agent implementation with built-in conversation management</li>
        <li><strong>Tool Calling:</strong> Ability to invoke external tools (APIs, databases, search engines)</li>
        <li><strong>Streaming Responses:</strong> Real-time text generation for responsive UX</li>
        <li><strong>Azure Integration:</strong> Native support for Azure OpenAI with managed identity authentication</li>
      </ul>

      <h2>Agent Lifecycle</h2>

      <h3>1. Agent Registration</h3>
      <p>When an agent is created, its configuration is stored in Cosmos DB:</p>
      <blockquote>
        <strong>POST</strong> /api/agents
        <br />
        Creates a new agent with specified tools, model, and instructions
      </blockquote>

      <h3>2. Agent Initialization</h3>
      <p>When a user starts chatting with an agent:</p>
      <ol>
        <li>The system loads the agent configuration from Cosmos DB</li>
        <li>Creates a <code>DemoBaseAgent</code> instance wrapping Microsoft's <code>ChatAgent</code></li>
        <li>Registers all configured tools (MCP servers, OpenAPI specs, A2A connections)</li>
        <li>Authenticates to Azure OpenAI using managed identity</li>
      </ol>

      <h3>3. Agent Execution</h3>
      <p>When processing a message:</p>
      <ol>
        <li>Loads conversation thread from Cosmos DB</li>
        <li>Applies sliding window memory management (keeps last N messages)</li>
        <li>Invokes the <code>ChatAgent.run()</code> method with user message and thread context</li>
        <li>Agent decides whether to call tools or respond directly</li>
        <li>Streams response back to the user</li>
        <li>Saves conversation to Cosmos DB for persistence</li>
      </ol>

      <h2>Tool Types</h2>
      <p>Agents can access different types of tools:</p>

      <h3>🔌 MCP Tools (Model Context Protocol)</h3>
      <p>
        Connect to external servers that provide specialized capabilities:
      </p>
      <ul>
        <li><strong>microsoft-docs:</strong> Search Microsoft documentation</li>
        <li><strong>azure-mcp:</strong> Manage Azure resources</li>
        <li><strong>mssql-mcp:</strong> Query SQL databases</li>
      </ul>

      <h3>🌐 OpenAPI Tools</h3>
      <p>
        Invoke REST APIs defined by OpenAPI specifications:
      </p>
      <ul>
        <li><strong>support-triage-api:</strong> Support ticket management</li>
        <li><strong>ops-assistant-api:</strong> Operations automation</li>
      </ul>

      <h3>🤝 A2A Tools (Agent-to-Agent)</h3>
      <p>
        Enable one agent to delegate work to another specialist agent:
      </p>
      <ul>
        <li>Router Agent → Sales Agent (for customer queries)</li>
        <li>Router Agent → Warehouse Agent (for inventory questions)</li>
      </ul>

      <h2>Why This Architecture Matters</h2>
      <ul>
        <li>✅ <strong>Flexibility:</strong> Add new agents without code changes—just update configuration</li>
        <li>✅ <strong>Reusability:</strong> Share tools across multiple agents</li>
        <li>✅ <strong>Observability:</strong> Track agent performance, token usage, and success rates</li>
        <li>✅ <strong>Security:</strong> Role-based access control, managed identity authentication</li>
        <li>✅ <strong>Scalability:</strong> Agents run independently, can be scaled horizontally</li>
      </ul>

      <h2>Summary</h2>
      <p>Agentarium's agent architecture combines:</p>
      <ol>
        <li><strong>Configuration-Driven Design</strong> - Agents defined in Cosmos DB, not hardcoded</li>
        <li><strong>Microsoft Agent Framework</strong> - Production-ready agent runtime with tool calling</li>
        <li><strong>Flexible Tool System</strong> - MCP, OpenAPI, and A2A integrations</li>
        <li><strong>Azure-Native</strong> - Managed identity, Azure OpenAI, secure by default</li>
      </ol>
      <p>
        This design makes it easy to experiment with different agent configurations, tools, and behaviors
        without writing any code.
      </p>
    </ArticleLayout>
  );
};
