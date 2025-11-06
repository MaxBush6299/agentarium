import React, { useState } from 'react';
import {
  Avatar,
  Text,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import { Bot24Regular, Person24Regular, ChevronDown20Regular, ChevronRight20Regular } from '@fluentui/react-icons';
import ReactMarkdown from 'react-markdown';
import { MessageRole, type MessageBubbleProps } from '../../types/message';
import { HumanGateActions } from './HumanGateActions';

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
  phaseContainer: {
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.margin(tokens.spacingVerticalS, 0),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.overflow('hidden'),
  },
  phaseHeader: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    cursor: 'pointer',
    backgroundColor: tokens.colorNeutralBackground3,
    ...shorthands.borderBottom('1px', 'solid', tokens.colorNeutralStroke2),
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground3Hover,
    },
  },
  phaseTitle: {
    flex: 1,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorBrandForeground1,
  },
  phaseContent: {
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    maxHeight: '400px',
    ...shorthands.overflow('auto'),
  },
  phaseContentCollapsed: {
    display: 'none',
  },
  approvalContainer: {
    ...shorthands.margin(tokens.spacingVerticalM, 0),
  },
  approvalDetails: {
    ...shorthands.margin(tokens.spacingVerticalS, 0, tokens.spacingVerticalM, 0),
  },
  detailsToggle: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalS),
    cursor: 'pointer',
    ...shorthands.padding(tokens.spacingVerticalS),
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground3,
    },
  },
  detailsLabel: {
    color: tokens.colorBrandForeground1,
    fontWeight: tokens.fontWeightSemibold,
  },
  detailsContent: {
    ...shorthands.margin(tokens.spacingVerticalS, 0),
    ...shorthands.padding(tokens.spacingVerticalM),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
  },
  vendorTable: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: tokens.spacingVerticalS,
  },
  tableHeader: {
    backgroundColor: tokens.colorNeutralBackground3,
    fontWeight: tokens.fontWeightSemibold,
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    textAlign: 'left',
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
  },
  tableCell: {
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
  },
});

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const styles = useStyles();
  const [isExpanded, setIsExpanded] = useState(true); // Start expanded by default

  const isUser = message.role === MessageRole.USER;
  const isAssistant = message.role === MessageRole.ASSISTANT;
  const isPhaseMessage = message.metadata?.isPhaseMessage === true;
  const metrics = message.metadata?.metrics;
  const subBlocks = message.metadata?.subBlocks || [];

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  const renderApprovalDetails = (approvalData: any) => {
    if (!approvalData) return null;
    
    const comparison = approvalData.comparison_report;
    const vendors = comparison?.vendors || [];
    
    return (
      <div>
        <Text weight="semibold" size={400}>Vendor Comparison Details:</Text>
        {vendors.length > 0 && (
          <table className={styles.vendorTable}>
            <thead>
              <tr>
                <th className={styles.tableHeader}>Vendor</th>
                <th className={styles.tableHeader}>Price</th>
                <th className={styles.tableHeader}>Rating</th>
                <th className={styles.tableHeader}>Delivery</th>
                <th className={styles.tableHeader}>Payment Terms</th>
              </tr>
            </thead>
            <tbody>
              {vendors.map((vendor: any, index: number) => (
                <tr key={index}>
                  <td className={styles.tableCell}>{vendor.vendor_name}</td>
                  <td className={styles.tableCell}>${vendor.quoted_unit_price?.toFixed(2) || 'N/A'}</td>
                  <td className={styles.tableCell}>{vendor.vendor_rating?.toFixed(1) || 'N/A'}</td>
                  <td className={styles.tableCell}>
                    {vendor.estimated_delivery_date ? 
                      new Date(vendor.estimated_delivery_date).toLocaleDateString() : 'TBD'}
                  </td>
                  <td className={styles.tableCell}>{vendor.payment_terms || 'Standard'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {approvalData.negotiation_recommendations && approvalData.negotiation_recommendations.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <Text weight="semibold" size={400}>Negotiation Recommendations:</Text>
            {approvalData.negotiation_recommendations.map((rec: any, index: number) => (
              <div key={index} style={{ margin: '8px 0', padding: '8px', backgroundColor: 'rgba(0, 120, 212, 0.1)', borderRadius: '4px' }}>
                <Text size={300}><strong>Strategy:</strong> {rec.negotiation_strategy}</Text>
                {rec.suggested_unit_price && (
                  <Text size={300}><br/><strong>Suggested Price:</strong> ${rec.suggested_unit_price.toFixed(2)}</Text>
                )}
                {rec.rationale && (
                  <Text size={300}><br/><strong>Rationale:</strong> {rec.rationale}</Text>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderAvatar = () => {
    if (isUser) {
      return (
        <Avatar
          className={styles.avatar}
          icon={<Person24Regular />}
          color="colorful"
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

  const renderHumanGateSection = () => {
    if (!message.humanGateActions || message.humanGateActions.length === 0) {
      return null;
    }
    return (
      <div className={styles.approvalContainer}>
        {message.humanGateData && (
          <div className={styles.approvalDetails}>
            <div
              className={styles.detailsToggle}
              onClick={() => setIsExpanded(!isExpanded)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  setIsExpanded(!isExpanded);
                }
              }}
            >
              {isExpanded ? <ChevronDown20Regular /> : <ChevronRight20Regular />}
              <Text className={styles.detailsLabel}>View Details</Text>
            </div>
            {isExpanded && (
              <div className={styles.detailsContent}>
                {renderApprovalDetails(message.humanGateData)}
              </div>
            )}
          </div>
        )}
        <HumanGateActions
          onAction={(action, result) => {
            console.log('HumanGate action:', action, result);
          }}
          disabled={message.isStreaming}
        />
      </div>
    );
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
        ) : isPhaseMessage && message.metadata?.phase ? (
          // Render phase message with collapsible UI
          <div className={styles.phaseContainer}>
            <div 
              className={styles.phaseHeader}
              onClick={() => setIsExpanded(!isExpanded)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  setIsExpanded(!isExpanded)
                }
              }}
            >
              {isExpanded ? <ChevronDown20Regular /> : <ChevronRight20Regular />}
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                <Text className={styles.phaseTitle}>
                  {message.metadata.title || message.metadata.phase}
                </Text>
                {metrics && (
                  <Text size={200} style={{ opacity: 0.75 }}>
                    {metrics.duration_ms} ms | tokens {metrics.prompt_tokens}/{metrics.completion_tokens}/{metrics.total_tokens}
                    {metrics.estimated ? ' (est)' : ''}
                  </Text>
                )}
              </div>
            </div>
            <div className={isExpanded ? styles.phaseContent : styles.phaseContentCollapsed}>
              <div className={styles.content}>
                {subBlocks.length > 1 && (
                  <div style={{ marginBottom: '8px' }}>
                    {subBlocks.map(sb => (
                      <a key={sb.id} href={`#${sb.id}`} style={{ marginRight: '12px', fontSize: '12px' }}>
                        {sb.title}
                      </a>
                    ))}
                  </div>
                )}
                <ReactMarkdown>
                  {typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}
                </ReactMarkdown>
                {renderHumanGateSection()}
              </div>
            </div>
          </div>
        ) : (
          <div className={styles.content}>
            {isAssistant ? (
              <>
                <ReactMarkdown>
                  {typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}
                </ReactMarkdown>
                {message.isStreaming && (
                  <span className={styles.streamingIndicator} />
                )}
                {renderHumanGateSection()}
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
