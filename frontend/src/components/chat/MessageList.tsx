import React, { useEffect, useRef } from 'react';
import {
  Spinner,
  Text,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import { MessageBubble } from './MessageBubble';
import { TracePanel } from './TracePanel';
import type { MessageListProps } from '../../types/message';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    ...shorthands.overflow('hidden'),
  },
  messageList: {
    flex: 1,
    ...shorthands.overflow('auto'),
    display: 'flex',
    flexDirection: 'column',
    scrollBehavior: 'smooth',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    ...shorthands.gap(tokens.spacingVerticalL),
    ...shorthands.padding(tokens.spacingVerticalXXXL),
    textAlign: 'center',
  },
  emptyTitle: {
    fontSize: tokens.fontSizeBase500,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground2,
  },
  emptySubtitle: {
    fontSize: tokens.fontSizeBase300,
    color: tokens.colorNeutralForeground3,
    maxWidth: '400px',
  },
  loadingContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...shorthands.padding(tokens.spacingVerticalL),
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  scrollAnchor: {
    height: '1px',
  },
});

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  traces = [],
  isLoading = false,
}) => {
  const styles = useStyles();
  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const messageListRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAnchorRef.current) {
      scrollAnchorRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, traces]);

  // Empty state
  if (messages.length === 0 && !isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyState}>
          <Text className={styles.emptyTitle}>Start a conversation</Text>
          <Text className={styles.emptySubtitle}>
            Send a message to begin chatting with the AI agent. The agent can help you with
            various tasks using its configured tools and capabilities.
          </Text>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.messageList} ref={messageListRef}>
        {messages.map((message, index) => {
          // Find the last user message in the conversation
          const lastUserMessageIndex = messages.map((msg, i) => msg.role === 'user' ? i : -1)
            .filter(i => i !== -1)
            .pop() ?? -1;
          
          const shouldShowTracesAfterThis = traces.length > 0 && index === lastUserMessageIndex;
          
          return (
            <React.Fragment key={message.id}>
              {(() => {
                if (message.role === 'assistant') {
                  console.log('🔍 Rendering message:', {
                    id: message.id,
                    contentPreview: message.content.substring(0, 50),
                    hasHumanGateActions: !!message.humanGateActions,
                    humanGateActions: message.humanGateActions,
                    metadata: message.metadata
                  })
                }
                return null
              })()}
              <MessageBubble message={message} />
              {/* Show trace panel after the last user message if traces exist */}
              {shouldShowTracesAfterThis && (
                <div style={{ padding: '12px' }}>
                  <TracePanel traces={traces} isStreaming={isLoading} />
                </div>
              )}
            </React.Fragment>
          );
        })}
        {isLoading && (
          <div className={styles.loadingContainer}>
            <Spinner size="small" />
            <Text>Agent is thinking...</Text>
          </div>
        )}
        <div ref={scrollAnchorRef} className={styles.scrollAnchor} />
      </div>
    </div>
  );
};
