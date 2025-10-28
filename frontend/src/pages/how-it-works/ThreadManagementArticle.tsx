import React from 'react';
import { ArticleLayout } from './ArticleLayout';

export const ThreadManagementArticle: React.FC = () => {
  return (
    <ArticleLayout
      title="Thread Management in Agentarium"
      date="October 28, 2025"
      author="Engineering Team"
    >
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

      <h2>Architecture Overview</h2>
      <p>
        Agentarium uses a <strong>dual-layer thread architecture</strong> combining the Microsoft Agent Framework's{' '}
        <code>AgentThread</code> for conversation state with Cosmos DB persistence for durable storage.
      </p>

      <h3>1. Agent Framework Thread (AgentThread)</h3>
      <p>
        The <code>AgentThread</code> class provides the in-memory conversation context that agents use during execution.
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
        automatically trim old messages while the agent retains recent context, keeping conversations efficient without
        losing important information.
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
    </ArticleLayout>
  );
};
