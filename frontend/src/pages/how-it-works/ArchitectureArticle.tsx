import React from 'react';
import { ArticleLayout } from './ArticleLayout';

export const ArchitectureArticle: React.FC = () => {
  return (
    <ArticleLayout
      title="Architecture & Infrastructure"
      date="October 28, 2025"
      author="Engineering Team"
    >
      <h2>What is Agentarium?</h2>
      <p>
        <strong>Agentarium</strong> is a cloud-native platform for building, deploying, and managing AI agents that can
        work together to solve complex problems. Think of it as a control center where different AI assistants collaborate—one
        might handle customer support questions, another analyzes sales data, and a third manages technical documentation.
      </p>

      <p><strong>Example Use Case:</strong></p>
      <blockquote>
        <p>You ask: <em>"Show me Q3 sales performance and create a customer support plan based on the data."</em></p>
        <p>Behind the scenes:</p>
        <ul>
          <li>A <strong>Router Agent</strong> determines you need both data analysis and planning</li>
          <li>A <strong>Sales Agent</strong> queries your database and analyzes Q3 performance</li>
          <li>A <strong>Support Agent</strong> uses the sales data to create a tailored support plan</li>
          <li>You get a comprehensive response combining insights from both specialists</li>
        </ul>
      </blockquote>

      <h2>High-Level Architecture</h2>
      <p>
        Agentarium follows a <strong>three-tier cloud architecture</strong> deployed on Microsoft Azure:
      </p>

      <h3>1. Frontend Tier (React Application)</h3>
      <ul>
        <li><strong>Technology:</strong> React with TypeScript, Fluent UI design system</li>
        <li><strong>Hosting:</strong> Azure Container Apps with NGINX serving static files</li>
        <li><strong>Features:</strong> Chat interface, agent management, conversation history, tool configuration</li>
        <li><strong>Communication:</strong> REST API calls to backend over HTTPS</li>
      </ul>

      <h3>2. Backend Tier (FastAPI Application)</h3>
      <ul>
        <li><strong>Technology:</strong> Python FastAPI with Microsoft Agent Framework</li>
        <li><strong>Hosting:</strong> Azure Container Apps with managed identity authentication</li>
        <li><strong>Features:</strong> Agent orchestration, tool integration, conversation management, state persistence</li>
        <li><strong>Communication:</strong> Azure OpenAI API, Cosmos DB, Key Vault, external tool APIs</li>
      </ul>

      <h3>3. Data Tier (Azure Services)</h3>
      <ul>
        <li><strong>Cosmos DB:</strong> NoSQL database storing agents, threads, messages, runs, steps</li>
        <li><strong>Key Vault:</strong> Secure secret management for API keys and connection strings</li>
        <li><strong>Application Insights:</strong> Monitoring, logging, and distributed tracing</li>
        <li><strong>Container Registry:</strong> Docker image storage for deployments</li>
      </ul>

      <h2>Azure Infrastructure Components</h2>
      <p>
        All infrastructure is defined as code using <strong>Azure Bicep</strong>, enabling consistent deployments
        and version control for infrastructure changes.
      </p>

      <h3>Container Apps Environment</h3>
      <p>
        Azure Container Apps provides serverless container hosting with built-in scaling and HTTPS ingress.
      </p>
      <pre>{`resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: 'cae-\${environmentName}'
  properties: {
    vnetConfiguration: {
      internal: false
      infrastructureSubnetId: containerAppsSubnetResourceId
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}`}</pre>

      <h3>Cosmos DB SQL API</h3>
      <p>
        Cosmos DB provides globally distributed NoSQL storage with automatic scaling and low-latency access.
      </p>
      <p><strong>Collections:</strong></p>
      <ul>
        <li><code>agents</code> - Agent definitions, tools, configurations</li>
        <li><code>threads</code> - Conversation threads partitioned by agentId</li>
        <li><code>messages</code> - User and assistant messages partitioned by threadId</li>
        <li><code>runs</code> - Agent execution records with tool calls</li>
        <li><code>steps</code> - Detailed execution steps for observability</li>
      </ul>

      <pre>{`resource threadsContainer 'Microsoft.DocumentDB/.../containers@2023-11-15' = {
  name: 'threads'
  properties: {
    resource: {
      id: 'threads'
      partitionKey: {
        paths: ['/agentId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
      }
    }
  }
}`}</pre>

      <h3>Virtual Network & Security</h3>
      <p>
        Network isolation ensures secure communication between components.
      </p>
      <ul>
        <li><strong>VNet Address Space:</strong> 10.0.0.0/16</li>
        <li><strong>Container Apps Subnet:</strong> 10.0.0.0/23 (delegated to Container Apps)</li>
        <li><strong>Private Endpoints Subnet:</strong> 10.0.2.0/24</li>
        <li><strong>Cosmos DB Access:</strong> Public network disabled, private endpoints only</li>
        <li><strong>Key Vault Access:</strong> Managed identity authentication via RBAC</li>
      </ul>

      <h3>Application Insights & Log Analytics</h3>
      <p>
        Comprehensive observability for monitoring agent performance and debugging issues.
      </p>
      <pre>{`resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics'
  }
}`}</pre>

      <h2>Microsoft Agent Framework Integration</h2>
      <p>
        Agentarium is built on the <strong>Microsoft Agent Framework</strong>, providing standardized agent patterns
        and integration with Azure services.
      </p>

      <h3>ChatAgent Pattern</h3>
      <p>
        The framework's <code>ChatAgent</code> class provides the foundation for all agents:
      </p>
      <pre>{`from agent_framework import ChatAgent, AgentThread

# Create a specialist agent
agent = ChatAgent(
    name="Support Triage Agent",
    instructions="You are a helpful support assistant...",
    tools=[microsoft_learn_tool, support_api_tool],
    model="gpt-4o"
)

# Execute with conversation context
thread = agent.get_new_thread()
response = await agent.run("Help me troubleshoot Azure AD", thread=thread)`}</pre>

      <h3>DemoBaseAgent Wrapper</h3>
      <p>
        Agentarium extends <code>ChatAgent</code> with application-specific features:
      </p>
      <ul>
        <li><strong>Sliding Window Memory:</strong> Automatic context management (max 20 messages)</li>
        <li><strong>Token Counting:</strong> Budget enforcement and cost tracking</li>
        <li><strong>Azure Integration:</strong> Managed identity authentication with Azure OpenAI</li>
        <li><strong>Tool Registry:</strong> Centralized tool configuration and discovery</li>
      </ul>

      <h2>Deployment Pipeline</h2>
      <p>
        GitHub Actions provides continuous deployment with semantic commit triggers.
      </p>

      <h3>Commit Tags</h3>
      <ul>
        <li><code>[backend]</code> - Deploy only backend container</li>
        <li><code>[frontend]</code> - Deploy only frontend container</li>
        <li><code>[all]</code> - Deploy both frontend and backend</li>
      </ul>

      <h3>Build Process</h3>
      <pre>{`# Backend deployment workflow
1. Checkout code
2. Azure login with service principal
3. Get ACR login server
4. Build and push Docker image (versioned)
5. Update Container App with new image
6. Verify deployment health`}</pre>

      <p><strong>Image Versioning:</strong> Each build increments a version tag (e.g., <code>v1</code>, <code>v2</code>)
      stored in Azure Container Registry.</p>

      <h3>Container Configuration</h3>
      <p>Environment variables are injected from Bicep templates:</p>
      <pre>{`env: [
  {
    name: 'COSMOS_ENDPOINT'
    value: cosmosDbEndpoint
  }
  {
    name: 'COSMOS_DATABASE_NAME'
    value: cosmosDbDatabaseName
  }
  {
    name: 'FRONTEND_URL'
    value: frontendUrl
  }
  {
    name: 'APPINSIGHTS_INSTRUMENTATION_KEY'
    secretRef: 'appinsights-key'
  }
]`}</pre>

      <h2>Security & Authentication</h2>

      <h3>Managed Identity (System-Assigned)</h3>
      <p>
        Container Apps use Azure Managed Identity to access resources without storing credentials:
      </p>
      <ul>
        <li><strong>Cosmos DB RBAC:</strong> <code>DocumentDB Account Contributor</code> role</li>
        <li><strong>Key Vault Secrets:</strong> <code>Key Vault Secrets User</code> role</li>
        <li><strong>Azure OpenAI:</strong> <code>Cognitive Services OpenAI User</code> role</li>
      </ul>

      <pre>{`// Assign backend managed identity to Cosmos DB
resource cosmosRoleAssignment 'Microsoft.DocumentDB/.../sqlRoleAssignments@2023-11-15' = {
  name: guid(cosmosDbAccount.id, backendIdentityPrincipalId)
  properties: {
    roleDefinitionId: documentDbContributorRoleId
    principalId: backendIdentityPrincipalId
    scope: cosmosDbAccount.id
  }
}`}</pre>

      <h3>Secrets Management</h3>
      <p>Sensitive configuration is stored in Azure Key Vault:</p>
      <ul>
        <li><code>cosmosdb-primary-key</code> - Fallback for local development</li>
        <li><code>openai-api-key</code> - Azure OpenAI API key</li>
        <li><code>mssql-connection-string</code> - SQL database for tools</li>
      </ul>

      <h3>Network Security</h3>
      <ul>
        <li><strong>Cosmos DB:</strong> Public network access disabled, private endpoints required</li>
        <li><strong>Key Vault:</strong> Firewall enabled with VNet integration</li>
        <li><strong>Container Apps:</strong> HTTPS-only ingress, custom domains supported</li>
        <li><strong>CORS:</strong> Restricted to configured frontend URL</li>
      </ul>

      <h2>Scaling & Reliability</h2>

      <h3>Automatic Scaling</h3>
      <p>
        Container Apps scale automatically based on HTTP traffic and resource utilization:
      </p>
      <ul>
        <li><strong>Min Replicas:</strong> 0 (scale to zero when idle)</li>
        <li><strong>Max Replicas:</strong> 10 (configurable per environment)</li>
        <li><strong>Scaling Triggers:</strong> HTTP request rate, CPU, memory</li>
      </ul>

      <h3>Cosmos DB Throughput</h3>
      <p>
        Two throughput modes are supported:
      </p>
      <ul>
        <li><strong>Serverless:</strong> Pay-per-request, best for development and variable workloads</li>
        <li><strong>Autoscale:</strong> Automatic RU/s scaling (400-4000 RU/s default)</li>
      </ul>

      <h3>Backup & Disaster Recovery</h3>
      <ul>
        <li><strong>Cosmos DB Backups:</strong> Periodic backups every 4 hours, 8-hour retention</li>
        <li><strong>Container Images:</strong> Versioned in ACR with tag history</li>
        <li><strong>Infrastructure Code:</strong> Version controlled in Git</li>
      </ul>

      <h2>Monitoring & Observability</h2>

      <h3>Application Insights</h3>
      <p>Comprehensive telemetry for the entire platform:</p>
      <ul>
        <li><strong>Request Tracing:</strong> End-to-end request correlation</li>
        <li><strong>Dependency Tracking:</strong> Azure OpenAI, Cosmos DB, Key Vault calls</li>
        <li><strong>Exception Logging:</strong> Automatic error capture with stack traces</li>
        <li><strong>Custom Metrics:</strong> Token usage, agent execution time, tool calls</li>
      </ul>

      <h3>Log Analytics Queries</h3>
      <p>Example KQL queries for monitoring:</p>
      <pre>{`// Find slow agent executions
traces
| where message contains "Agent execution completed"
| extend duration = todouble(customDimensions.duration_seconds)
| where duration > 10
| project timestamp, duration, customDimensions.agent_name

// Track tool usage
dependencies
| where type == "HTTP"
| where target contains "api.microsoft.com"
| summarize count() by name, bin(timestamp, 1h)`}</pre>

      <h3>Health Checks</h3>
      <p>Each Container App exposes health endpoints:</p>
      <ul>
        <li><code>GET /health</code> - Basic liveness check</li>
        <li><code>GET /health/ready</code> - Readiness check (Cosmos DB, Key Vault connectivity)</li>
      </ul>

      <h2>Development Workflow</h2>

      <h3>Local Development</h3>
      <p>Developers can run the platform locally with:</p>
      <ul>
        <li><strong>Cosmos DB Emulator:</strong> Local database for testing</li>
        <li><strong>Environment Variables:</strong> <code>.env</code> file configuration</li>
        <li><strong>Azure CLI Authentication:</strong> Use personal credentials for Azure services</li>
      </ul>

      <pre>{`# Backend local setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Frontend local setup
cd frontend
npm install
npm run dev`}</pre>

      <h3>Infrastructure Changes</h3>
      <p>All infrastructure changes follow the IaC workflow:</p>
      <ol>
        <li>Modify Bicep templates in <code>infra/</code> directory</li>
        <li>Test locally with <code>az deployment group validate</code></li>
        <li>Deploy to Azure with <code>./infra/deploy.ps1</code></li>
        <li>Verify changes in Azure Portal or CLI</li>
      </ol>

      <h2>Cost Optimization</h2>
      <p>Agentarium is designed for cost-efficient cloud operation:</p>
      <ul>
        <li><strong>Container Apps:</strong> Scale to zero when idle (pay-per-use)</li>
        <li><strong>Cosmos DB:</strong> Serverless mode for development (pay-per-request)</li>
        <li><strong>App Insights:</strong> Daily data cap (10 GB default)</li>
        <li><strong>Log Retention:</strong> 30 days (configurable)</li>
        <li><strong>Network:</strong> No Azure Firewall or NAT Gateway charges in dev environment</li>
      </ul>

      <h2>Summary</h2>
      <p>Agentarium's architecture provides:</p>
      <ol>
        <li><strong>Cloud-Native Design:</strong> Serverless containers with automatic scaling</li>
        <li><strong>Secure by Default:</strong> Managed identities, private endpoints, Key Vault secrets</li>
        <li><strong>Observable:</strong> Comprehensive logging and monitoring with Application Insights</li>
        <li><strong>Infrastructure as Code:</strong> Bicep templates for consistent, repeatable deployments</li>
        <li><strong>Developer-Friendly:</strong> Local development support with Azure emulators</li>
        <li><strong>Cost-Optimized:</strong> Pay-per-use services with auto-scaling to zero</li>
        <li><strong>Framework-Powered:</strong> Built on Microsoft Agent Framework for best practices</li>
      </ol>

      <p>
        This architecture enables rapid development and deployment of sophisticated multi-agent systems
        while maintaining enterprise-grade security, observability, and reliability.
      </p>
    </ArticleLayout>
  );
};