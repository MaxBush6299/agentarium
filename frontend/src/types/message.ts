/**
 * Chat message types for the messaging interface
 */

export enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SYSTEM = "system"
}

export interface TraceEvent {
  id: string;
  type: 'tool_call' | 'a2a_call' | 'model_call';
  name: string;
  toolType?: string;
  status: 'pending' | 'success' | 'error';
  startTime: number;
  endTime?: number;
  latencyMs?: number;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
  tokens?: {
    input?: number;
    output?: number;
    total?: number;
  };
  metadata?: {
    mcpServer?: string;
    openapEndpoint?: string;
    a2aAgent?: string;
  };
  children?: TraceEvent[];
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  agentId?: string;
  agentName?: string;
  isStreaming?: boolean;
  error?: string;
  humanGateActions?: Array<'approve' | 'edit' | 'reject'>;
  humanGateData?: any;
  metadata?: {
    phase?: string;
    isPhaseMessage?: boolean;
    data?: Record<string, unknown>;
    [key: string]: any;
  };
}

export interface MessageBubbleProps {
  message: Message;
}

export interface MessageListProps {
  messages: Message[];
  traces?: TraceEvent[];
  isLoading?: boolean;
  onRetry?: (messageId: string) => void;
}

export interface InputBoxProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}
