import React from 'react';
import {
  Avatar,
  Text,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import { Bot24Regular, Person24Regular } from '@fluentui/react-icons';
import ReactMarkdown from 'react-markdown';
import { MessageRole, type MessageBubbleProps } from '../../types/message';

const useStyles = makeStyles({
  messageContainer: {
    display: 'flex',
    ...shorthands.gap(tokens.spacingHorizontalM),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    width: '100%',
    boxSizing: 'border-box',
  },
  userMessage: {
    backgroundColor: tokens.colorNeutralBackground3,
  },
  assistantMessage: {
    backgroundColor: tokens.colorNeutralBackground1,
  },
  avatar: {
    flexShrink: 0,
  },
  contentWrapper: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalXS),
    minWidth: 0, // Allow text to wrap
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  name: {
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
  },
  timestamp: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  content: {
    color: tokens.colorNeutralForeground1,
    lineHeight: tokens.lineHeightBase400,
    wordBreak: 'break-word',
    '& p': {
      marginTop: 0,
      marginBottom: tokens.spacingVerticalS,
      '&:last-child': {
        marginBottom: 0,
      },
    },
    '& code': {
      backgroundColor: tokens.colorNeutralBackground5,
      ...shorthands.padding('2px', '4px'),
      ...shorthands.borderRadius(tokens.borderRadiusSmall),
      fontFamily: tokens.fontFamilyMonospace,
      fontSize: tokens.fontSizeBase200,
    },
    '& pre': {
      backgroundColor: tokens.colorNeutralBackground5,
      ...shorthands.padding(tokens.spacingVerticalM),
      ...shorthands.borderRadius(tokens.borderRadiusMedium),
      ...shorthands.overflow('auto'),
      '& code': {
        backgroundColor: 'transparent',
        padding: 0,
      },
    },
    '& ul, & ol': {
      marginTop: tokens.spacingVerticalS,
      marginBottom: tokens.spacingVerticalS,
      paddingLeft: tokens.spacingHorizontalXL,
    },
    '& li': {
      marginBottom: tokens.spacingVerticalXS,
    },
    '& table': {
      borderCollapse: 'collapse',
      width: '100%',
      marginTop: tokens.spacingVerticalS,
      marginBottom: tokens.spacingVerticalS,
      border: `1px solid ${tokens.colorNeutralStroke2}`,
    },
    '& th': {
      backgroundColor: tokens.colorNeutralBackground3,
      color: tokens.colorNeutralForeground1,
      fontWeight: tokens.fontWeightSemibold,
      ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
      textAlign: 'left',
      border: `1px solid ${tokens.colorNeutralStroke2}`,
    },
    '& td': {
      ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
      border: `1px solid ${tokens.colorNeutralStroke2}`,
    },
    '& tr:nth-child(even)': {
      backgroundColor: tokens.colorNeutralBackground2,
    },
    '& tr:hover': {
      backgroundColor: tokens.colorNeutralBackground3,
    },
  },
  errorContent: {
    color: tokens.colorPaletteRedForeground1,
    fontStyle: 'italic',
  },
  streamingIndicator: {
    display: 'inline-block',
    width: '8px',
    height: '16px',
    backgroundColor: tokens.colorBrandBackground,
    marginLeft: '4px',
    animationName: {
      '0%, 100%': { opacity: 1 },
      '50%': { opacity: 0.3 },
    },
    animationDuration: '1s',
    animationIterationCount: 'infinite',
  },
});

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const styles = useStyles();

  const isUser = message.role === MessageRole.USER;
  const isAssistant = message.role === MessageRole.ASSISTANT;

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  const renderAvatar = () => {
    if (isUser) {
      return (
        <Avatar
          className={styles.avatar}
          icon={<Person24Regular />}
          color="brand"
          aria-label="User"
        />
      );
    }
    return (
      <Avatar
        className={styles.avatar}
        icon={<Bot24Regular />}
        color="colorful"
        aria-label={message.agentName || 'Assistant'}
      />
    );
  };

  const renderName = () => {
    if (isUser) {
      return 'You';
    }
    return message.agentName || 'Assistant';
  };

  return (
    <div
      className={`${styles.messageContainer} ${
        isUser ? styles.userMessage : styles.assistantMessage
      }`}
    >
      {renderAvatar()}
      <div className={styles.contentWrapper}>
        <div className={styles.header}>
          <Text className={styles.name}>{renderName()}</Text>
          <Text className={styles.timestamp}>
            {formatTime(message.timestamp)}
          </Text>
        </div>
        {message.error ? (
          <Text className={styles.errorContent}>
            ❌ Error: {message.error}
          </Text>
        ) : (
          <div className={styles.content}>
            {isAssistant ? (
              <>
                <ReactMarkdown>{message.content}</ReactMarkdown>
                {message.isStreaming && (
                  <span className={styles.streamingIndicator} />
                )}
              </>
            ) : (
              <Text>{message.content}</Text>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
