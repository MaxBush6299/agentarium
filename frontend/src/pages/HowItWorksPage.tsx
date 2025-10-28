import React from 'react';
import { makeStyles, shorthands } from '@fluentui/react-components';
import { Book24Regular, Chat24Regular, Bot24Regular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    height: '100vh',
    background: 'linear-gradient(135deg, #0e1419 0%, #1a2530 100%)',
    overflow: 'hidden',
  },
  sidebar: {
    width: '280px',
    background: 'linear-gradient(180deg, #1a2530 0%, #0e1419 100%)',
    ...shorthands.borderRight('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
    ...shorthands.padding('2rem', '1.5rem'),
    overflowY: 'auto',
    flexShrink: 0,
  },
  sidebarTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#f0fcff',
    marginBottom: '1.5rem',
  },
  tocList: {
    listStyle: 'none',
    ...shorthands.padding('0'),
    ...shorthands.margin('0'),
  },
  tocItem: {
    marginBottom: '0.75rem',
  },
  tocLink: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('0.5rem'),
    ...shorthands.padding('0.75rem', '1rem'),
    ...shorthands.borderRadius('8px'),
    color: '#7ad4f0',
    textDecoration: 'none',
    fontSize: '0.9rem',
    transition: 'all 0.2s ease',
    cursor: 'pointer',
    background: 'transparent',
    ...shorthands.border('1px', 'solid', 'transparent'),
    ':hover': {
      background: 'rgba(63, 176, 221, 0.1)',
      color: '#f0fcff',
      ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.3)'),
    },
  },
  tocLinkActive: {
    background: 'rgba(63, 176, 221, 0.15)',
    color: '#f0fcff',
    ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.5)'),
  },
  tocIcon: {
    fontSize: '1.25rem',
  },
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    ...shorthands.padding('2rem', '2rem', '1rem', '2rem'),
    flexShrink: 0,
  },
  title: {
    fontSize: '2.5rem',
    fontWeight: '700',
    color: '#f0fcff',
    marginBottom: '0.5rem',
  },
  subtitle: {
    fontSize: '1.125rem',
    color: '#7ad4f0',
    marginBottom: '0',
  },
  scrollableContent: {
    flex: 1,
    overflowY: 'auto',
    ...shorthands.padding('0', '2rem', '2rem', '2rem'),
  },
  content: {
    maxWidth: '900px',
    width: '100%',
  },
  articleList: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('2rem'),
  },
  articleCard: {
    background: 'linear-gradient(135deg, #1a2530 0%, #243240 100%)',
    ...shorthands.borderRadius('12px'),
    ...shorthands.padding('2rem'),
    ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    transition: 'all 0.3s ease',
    scrollMarginTop: '2rem',
    ':hover': {
      ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.5)'),
      boxShadow: '0 12px 48px rgba(63, 176, 221, 0.15)',
    },
  },
  articleHeader: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('1rem'),
    marginBottom: '1rem',
  },
  articleIcon: {
    fontSize: '2rem',
    color: '#3fb0dd',
  },
  articleTitle: {
    fontSize: '1.75rem',
    fontWeight: '600',
    color: '#f0fcff',
    marginBottom: '0.5rem',
  },
  articleMeta: {
    fontSize: '0.875rem',
    color: '#7ad4f0',
    marginBottom: '1rem',
  },
  articleContent: {
    color: '#bdeffc',
    lineHeight: '1.8',
    fontSize: '1rem',
    '& h2': {
      fontSize: '1.5rem',
      fontWeight: '600',
      color: '#f0fcff',
      marginTop: '2rem',
      marginBottom: '1rem',
    },
    '& h3': {
      fontSize: '1.25rem',
      fontWeight: '600',
      color: '#f0fcff',
      marginTop: '1.5rem',
      marginBottom: '0.75rem',
    },
    '& p': {
      marginBottom: '1rem',
    },
    '& ul, & ol': {
      marginLeft: '1.5rem',
      marginBottom: '1rem',
    },
    '& li': {
      marginBottom: '0.5rem',
    },
    '& code': {
      background: 'rgba(63, 176, 221, 0.1)',
      ...shorthands.padding('0.125rem', '0.5rem'),
      ...shorthands.borderRadius('4px'),
      color: '#7ad4f0',
      fontFamily: 'Consolas, Monaco, "Courier New", monospace',
      fontSize: '0.9em',
    },
    '& pre': {
      background: '#0e1419',
      ...shorthands.padding('1rem'),
      ...shorthands.borderRadius('8px'),
      ...shorthands.overflow('auto', 'auto'),
      marginBottom: '1rem',
      ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
      '& code': {
        background: 'transparent',
        padding: '0',
        color: '#bdeffc',
      },
    },
    '& table': {
      width: '100%',
      borderCollapse: 'collapse',
      marginBottom: '1rem',
      fontSize: '0.9rem',
    },
    '& th': {
      background: 'rgba(63, 176, 221, 0.1)',
      ...shorthands.padding('0.75rem'),
      textAlign: 'left',
      ...shorthands.borderBottom('2px', 'solid', '#3fb0dd'),
      color: '#f0fcff',
      fontWeight: '600',
    },
    '& td': {
      ...shorthands.padding('0.75rem'),
      ...shorthands.borderBottom('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
    },
    '& blockquote': {
      ...shorthands.borderLeft('4px', 'solid', '#3fb0dd'),
      ...shorthands.padding('0.5rem', '1rem'),
      marginLeft: '0',
      marginRight: '0',
      marginBottom: '1rem',
      background: 'rgba(63, 176, 221, 0.05)',
      color: '#7ad4f0',
      fontStyle: 'italic',
    },
  },
});

interface Article {
  id: string;
  title: string;
  icon: React.ReactElement;
  date: string;
  author: string;
  content: React.ReactNode;
}

export const HowItWorksPage: React.FC = () => {
  const styles = useStyles();
  const [activeArticle, setActiveArticle] = React.useState<string>('thread-management');

  const scrollToArticle = (articleId: string) => {
    setActiveArticle(articleId);
    const element = document.getElementById(articleId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const articles: Article[] = [
    {
      id: 'thread-management',
      title: 'Thread Management in Agentarium',
      icon: <Chat24Regular />,
      date: 'October 28, 2025',
      author: 'Engineering Team',
      content: (
        <>
          <h2>What is a Thread?</h2>
          <p>
            Think of a <strong>thread</strong> as a conversation between you and an AI agent. Just like texting
            with a friend, each thread keeps track of everything you've said and everything the agent has
            responded with. This means the agent can remember earlier parts of your conversation and give you
            more helpful, contextual answers.
          </p>

          <p><strong>Example:</strong></p>
          <blockquote>
            <p><strong>You:</strong> "What were my top 3 customers last quarter?"</p>
            <p><strong>Agent:</strong> "Your top 3 customers were Contoso ($45K), Fabrikam ($38K), and Tailspin ($32K)."</p>
            <p><strong>You:</strong> "Show me their purchase history" <em>(the agent remembers which customers you're asking about!)</em></p>
            <p><strong>Agent:</strong> "Here's the detailed purchase history for Contoso, Fabrikam, and Tailspin..."</p>
          </blockquote>

          <h2>What is Thread Management?</h2>
          <p>
            <strong>Thread management</strong> is how Agentarium keeps your conversations organized and accessible:
          </p>
          <ul>
            <li><strong>Saves Your Conversations:</strong> When you close the app and come back later, your conversations are still there</li>
            <li><strong>Organizes by Topic:</strong> Each agent can have multiple threads for different topics (sales questions, inventory questions, etc.)</li>
            <li><strong>Manages Memory:</strong> Automatically keeps only the most relevant parts of long conversations so the agent stays focused</li>
            <li><strong>Enables Handoffs:</strong> Lets multiple specialist agents work together on complex requests</li>
          </ul>

          <h2>Why Does Thread Management Matter?</h2>
          <p>
            Without thread management, every question to an agent would be like starting from scratch—the agent
            wouldn't remember anything you talked about before. With thread management:
          </p>
          <ul>
            <li>✅ <strong>Faster conversations:</strong> No need to repeat context or explain what you meant earlier</li>
            <li>✅ <strong>Better answers:</strong> Agents understand follow-up questions and can build on previous responses</li>
            <li>✅ <strong>Pick up where you left off:</strong> Return to conversations days later and the agent still remembers</li>
            <li>✅ <strong>Team collaboration:</strong> Multiple agents can work together seamlessly on your request</li>
          </ul>

          <h2>Overview</h2>
          <p>
            Agentarium uses a <strong>dual-layer thread architecture</strong> combining the Microsoft Agent Framework's{' '}
            <code>AgentThread</code> for conversation state with Cosmos DB persistence for durable storage. This approach
            enables multi-turn conversations with context preservation across sessions while maintaining observability and
            audit trails.
          </p>

          <h2>Architecture</h2>

          <h3>1. Agent Framework Thread (AgentThread)</h3>
          <p>
            The <code>AgentThread</code> class from Microsoft's Agent Framework provides the in-memory conversation context
            that agents use during execution.
          </p>

          <p><strong>Key Features:</strong></p>
          <ul>
            <li><strong>Message Store:</strong> Maintains conversation history with user/assistant/tool messages</li>
            <li><strong>Context Preservation:</strong> Allows multi-turn conversations where agents remember previous exchanges</li>
            <li><strong>Stateful Execution:</strong> Enables agents to reference earlier messages and tool results</li>
            <li><strong>Sliding Window Memory:</strong> Can be managed to keep only recent messages (prevents context overflow)</li>
          </ul>

          <h3>2. Cosmos DB Thread (Durable Persistence)</h3>
          <p>
            The Thread model provides durable storage for conversations, enabling:
          </p>
          <ul>
            <li><strong>Session Persistence:</strong> Conversations survive across server restarts</li>
            <li><strong>Cross-Request Continuity:</strong> Users can resume conversations later</li>
            <li><strong>Audit Trail:</strong> Complete history of messages, runs, and metadata</li>
            <li><strong>Multi-User Support:</strong> Isolate conversations by user and agent</li>
          </ul>

          <h2>How Threads Are Used</h2>

          <h3>Flow 1: Direct Agent Chat</h3>
          <p>This is the standard flow for single-agent conversations.</p>
          <ol>
            <li><strong>HTTP Request Received</strong> - User sends message to <code>/api/agents/&#123;agent_id&#125;/chat</code></li>
            <li><strong>Get or Create Cosmos DB Thread</strong> - Resume existing conversation or start new one</li>
            <li><strong>Add User Message to Thread</strong> - Store user's message in Cosmos DB</li>
            <li><strong>Create Agent Framework Thread</strong> - Create in-memory <code>AgentThread</code> for execution</li>
            <li><strong>Execute Agent with Thread</strong> - Agent processes message with conversation context</li>
            <li><strong>Add Assistant Response</strong> - Store agent's response in Cosmos DB</li>
          </ol>

          <blockquote>
            <strong>Key Point:</strong> The <code>AgentThread</code> is ephemeral (exists only during request execution),
            while the Cosmos DB Thread is durable (persists across requests).
          </blockquote>

          <h3>Flow 2: Multi-Agent Handoff</h3>
          <p>The Router Agent uses a special flow that coordinates multiple specialist agents.</p>
          <ol>
            <li><strong>Router Receives Query</strong> - Initial request to <code>/api/agents/router/chat</code></li>
            <li><strong>Intent Classification</strong> - Determines which specialist agent to use</li>
            <li><strong>Specialist Execution</strong> - Target agent processes the request</li>
            <li><strong>Hybrid Handoff Detection</strong> - Checks if additional agents are needed</li>
            <li><strong>Multi-Agent Synthesis</strong> - Combines responses from multiple agents if needed</li>
          </ol>

          <blockquote>
            <strong>Key Point:</strong> All specialist agents share the same <code>AgentThread</code> instance,
            allowing them to see each other's context in handoff scenarios.
          </blockquote>

          <h2>Sliding Window Memory Management</h2>
          <p>
            Agentarium implements automatic conversation context management to prevent token overflow. Long conversations
            automatically trim old messages while the agent retains recent context.
          </p>

          <h2>Best Practices</h2>
          <p><strong>✅ Do:</strong></p>
          <ul>
            <li>Always pass the same <code>AgentThread</code> instance for multi-turn conversations</li>
            <li>Use Cosmos DB thread IDs for durable session management</li>
            <li>Let sliding window manage context automatically</li>
            <li>Create new Cosmos DB threads for new conversation topics</li>
          </ul>

          <p><strong>❌ Don't:</strong></p>
          <ul>
            <li>Don't create a new <code>AgentThread</code> for every message (breaks context)</li>
            <li>Don't exceed max messages without sliding window management</li>
            <li>Don't store sensitive data in thread metadata without encryption</li>
            <li>Don't share <code>AgentThread</code> instances across concurrent requests</li>
          </ul>

          <h2>Summary</h2>
          <p>Agentarium's thread system combines:</p>
          <ol>
            <li><strong>Microsoft Agent Framework AgentThread</strong> - Stateful in-memory execution context</li>
            <li><strong>Cosmos DB Thread</strong> - Durable conversation persistence</li>
            <li><strong>Sliding Window Memory</strong> - Automatic context management</li>
            <li><strong>Handoff Coordination</strong> - Shared threads across specialist agents</li>
          </ol>
          <p>
            This architecture enables sophisticated multi-turn, multi-agent conversations with full observability
            and session persistence.
          </p>
        </>
      ),
    },
    {
      id: 'agent-definitions',
      title: 'Agent Definitions and Architecture',
      icon: <Bot24Regular />,
      date: 'October 28, 2025',
      author: 'Engineering Team',
      content: (
        <>
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
        </>
      ),
    },
  ];

  return (
    <div className={styles.container}>
      {/* Sidebar with Table of Contents */}
      <aside className={styles.sidebar}>
        <h2 className={styles.sidebarTitle}>Table of Contents</h2>
        <ul className={styles.tocList}>
          {articles.map((article) => (
            <li key={article.id} className={styles.tocItem}>
              <div
                className={`${styles.tocLink} ${activeArticle === article.id ? styles.tocLinkActive : ''}`}
                onClick={() => scrollToArticle(article.id)}
              >
                <span className={styles.tocIcon}>{article.icon}</span>
                <span>{article.title}</span>
              </div>
            </li>
          ))}
        </ul>
      </aside>

      {/* Main Content Area */}
      <div className={styles.mainContent}>
        <div className={styles.header}>
          <h1 className={styles.title}>
            <Book24Regular style={{ marginRight: '1rem', verticalAlign: 'middle' }} />
            How It Works
          </h1>
          <p className={styles.subtitle}>
            Learn about the architecture and features powering Agentarium
          </p>
        </div>

        <div className={styles.scrollableContent}>
          <div className={styles.content}>
            <div className={styles.articleList}>
              {articles.map((article) => (
                <article key={article.id} id={article.id} className={styles.articleCard}>
                  <div className={styles.articleHeader}>
                    <div className={styles.articleIcon}>{article.icon}</div>
                    <div>
                      <h2 className={styles.articleTitle}>{article.title}</h2>
                      <div className={styles.articleMeta}>
                        {article.date} • By {article.author}
                      </div>
                    </div>
                  </div>
                  <div className={styles.articleContent}>{article.content}</div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
