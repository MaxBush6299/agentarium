/**
 * TracePanel Component
 * Displays tool calls, API calls, and A2A orchestration traces with nested hierarchies
 * Supports collapsible sections and shows latency, token counts, and metadata
 */

import React, { useState } from 'react'
import {
  makeStyles,
  shorthands,
  tokens,
  Text,
  Tooltip,
  Badge,
} from '@fluentui/react-components'
import {
  ChevronRight24Regular,
  ChevronDown24Regular,
  CheckmarkCircle24Regular,
  ErrorCircle24Regular,
  Clock24Regular,
  Code24Regular,
} from '@fluentui/react-icons'

export interface TraceEvent {
  id: string
  type: 'tool_call' | 'a2a_call' | 'model_call'
  name: string
  toolType?: string // 'mcp', 'openapi', 'a2a'
  status: 'pending' | 'success' | 'error'
  startTime: number
  endTime?: number
  latencyMs?: number
  input?: Record<string, unknown>
  output?: Record<string, unknown>
  error?: string
  tokens?: {
    input?: number
    output?: number
    total?: number
  }
  metadata?: {
    mcpServer?: string
    openapEndpoint?: string
    a2aAgent?: string
  }
  children?: TraceEvent[]
}

interface TracePanelProps {
  traces: TraceEvent[]
  isStreaming?: boolean
}

interface TraceItemProps {
  trace: TraceEvent
  depth: number
  isStreaming?: boolean
}

const useStyles = makeStyles({
  container: {
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
  },
  title: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: tokens.spacingVerticalM,
    color: tokens.colorNeutralForeground1,
  },
  empty: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    fontStyle: 'italic',
  },
  tracesList: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  traceItem: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke3),
    borderRadius: tokens.borderRadiusSmall,
    backgroundColor: tokens.colorNeutralBackground1,
    overflow: 'hidden',
  },
  traceHeader: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalM),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    cursor: 'pointer',
    userSelect: 'none',
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground2,
    },
  },
  expandIcon: {
    display: 'flex',
    alignItems: 'center',
    color: tokens.colorNeutralForeground3,
    flexShrink: 0,
  },
  statusIcon: {
    display: 'flex',
    alignItems: 'center',
    flexShrink: 0,
  },
  statusSuccess: {
    color: tokens.colorPaletteGreenForeground1,
  },
  statusError: {
    color: tokens.colorPaletteRedForeground1,
  },
  statusPending: {
    color: tokens.colorBrandForeground1,
  },
  traceInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
  },
  traceName: {
    fontSize: tokens.fontSizeBase300,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  traceSubtitle: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    marginTop: tokens.spacingVerticalXS,
  },
  traceMeta: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalM),
    marginTop: tokens.spacingVerticalXS,
    flexWrap: 'wrap',
  },
  metaItem: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalXS),
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  badge: {
    marginLeft: tokens.spacingHorizontalS,
  },
  traceDetails: {
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    backgroundColor: tokens.colorNeutralBackground1,
    borderTop: `1px solid ${tokens.colorNeutralStroke3}`,
  },
  detailsSection: {
    marginBottom: tokens.spacingVerticalM,
    '&:last-child': {
      marginBottom: 0,
    },
  },
  detailsTitle: {
    fontSize: tokens.fontSizeBase200,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground2,
    marginBottom: tokens.spacingVerticalXS,
    textTransform: 'uppercase',
  },
  codeBlock: {
    backgroundColor: tokens.colorNeutralBackground3,
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    borderRadius: tokens.borderRadiusSmall,
    overflow: 'auto',
    fontSize: tokens.fontSizeBase100,
    fontFamily: '"Courier New", monospace',
    color: tokens.colorNeutralForeground1,
    maxHeight: '200px',
  },
  errorBlock: {
    backgroundColor: tokens.colorPaletteRedBackground3,
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    borderRadius: tokens.borderRadiusSmall,
    borderLeft: `3px solid ${tokens.colorPaletteRedForeground1}`,
    color: tokens.colorNeutralForeground1,
    fontSize: tokens.fontSizeBase200,
  },
  nestedTraces: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalS),
    marginTop: tokens.spacingVerticalM,
    paddingLeft: tokens.spacingHorizontalL,
    borderLeft: `2px solid ${tokens.colorNeutralStroke3}`,
  },
  toolTypeBadge: {
    textTransform: 'uppercase',
    fontSize: tokens.fontSizeBase100,
  },
})

/**
 * TraceItem Component
 * Renders individual trace with expandable details
 */
const TraceItem: React.FC<TraceItemProps> = ({ trace, depth, isStreaming }) => {
  const styles = useStyles()
  const [expanded, setExpanded] = useState(false)
  const [expandedRequest, setExpandedRequest] = useState(true)
  const [expandedResult, setExpandedResult] = useState(true)

  const getStatusIcon = () => {
    switch (trace.status) {
      case 'success':
        return <CheckmarkCircle24Regular className={styles.statusSuccess} />
      case 'error':
        return <ErrorCircle24Regular className={styles.statusError} />
      case 'pending':
        return <Clock24Regular className={styles.statusPending} />
    }
  }

  const getToolTypeLabel = () => {
    switch (trace.toolType) {
      case 'mcp':
        return 'MCP'
      case 'openapi':
        return 'OpenAPI'
      case 'a2a':
        return 'A2A'
      default:
        return trace.toolType?.toUpperCase() || 'TOOL'
    }
  }

  const getToolTypeColor = (): 'success' | 'warning' | 'brand' | 'danger' => {
    switch (trace.toolType) {
      case 'mcp':
        return 'brand' // Blue
      case 'openapi':
        return 'danger' // Teal/Red alternative
      case 'a2a':
        return 'warning' // Orange
      default:
        return 'brand'
    }
  }

  // Extract request and result from input
  const getRequestData = () => {
    if (trace.input && typeof trace.input === 'object' && 'request' in trace.input) {
      return (trace.input as Record<string, unknown>).request as Record<string, unknown>
    }
    return null
  }

  const getResultData = () => {
    if (trace.input && typeof trace.input === 'object') {
      const input = trace.input as Record<string, unknown>
      return {
        call_id: input.call_id,
        result: input.result,
        type: input.type,
        exception: input.exception,
      } as Record<string, unknown>
    }
    return null
  }

  const requestData = getRequestData()
  const resultData = getResultData()
  const hasDetails = expanded && (requestData || resultData || trace.output || trace.error)
  const hasChildren = trace.children && trace.children.length > 0

  return (
    <div className={styles.traceItem}>
      <div
        className={styles.traceHeader}
        onClick={() => setExpanded(!expanded)}
      >
        <div className={styles.expandIcon}>
          {hasDetails || hasChildren ? (
            expanded ? (
              <ChevronDown24Regular />
            ) : (
              <ChevronRight24Regular />
            )
          ) : null}
        </div>

        <div className={styles.statusIcon}>{getStatusIcon()}</div>

        <div className={styles.traceInfo}>
          <div className={styles.traceName}>
            {trace.name}
            {trace.toolType && (
              <Badge
                className={styles.toolTypeBadge}
                color={getToolTypeColor()}
                size="small"
              >
                {getToolTypeLabel()}
              </Badge>
            )}
          </div>

          <div className={styles.traceSubtitle}>
            {trace.metadata?.mcpServer && `MCP Server: ${trace.metadata.mcpServer}`}
            {trace.metadata?.a2aAgent && `Agent: ${trace.metadata.a2aAgent}`}
            {trace.metadata?.openapEndpoint && `Endpoint: ${trace.metadata.openapEndpoint}`}
          </div>

          <div className={styles.traceMeta}>
            {trace.latencyMs !== undefined && (
              <Tooltip content={`${trace.latencyMs}ms execution time`} relationship="label">
                <div className={styles.metaItem}>
                  <Clock24Regular />
                  <span>{trace.latencyMs}ms</span>
                </div>
              </Tooltip>
            )}

            {trace.tokens && trace.tokens.total !== undefined && (
              <Tooltip
                content={`${trace.tokens.input || 0} in / ${trace.tokens.output || 0} out`}
                relationship="label"
              >
                <div className={styles.metaItem}>
                  <Code24Regular />
                  <span>{trace.tokens.total} tokens</span>
                </div>
              </Tooltip>
            )}

            {trace.status === 'error' && trace.error && (
              <div className={styles.metaItem} style={{ color: tokens.colorPaletteRedForeground1 }}>
                Error: {trace.error.substring(0, 50)}
                {trace.error.length > 50 ? '...' : ''}
              </div>
            )}
          </div>
        </div>
      </div>

      {hasDetails && (
        <div className={styles.traceDetails}>
          {requestData && (
            <div className={styles.detailsSection}>
              <div
                className={styles.detailsTitle}
                style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                onClick={(e) => {
                  e.stopPropagation()
                  setExpandedRequest(!expandedRequest)
                }}
              >
                {expandedRequest ? <ChevronDown24Regular /> : <ChevronRight24Regular />}
                Tool Call
              </div>
              {expandedRequest && (
                <div className={styles.codeBlock}>
                  {JSON.stringify(requestData, null, 2)}
                </div>
              )}
            </div>
          )}

          {resultData && (
            <div className={styles.detailsSection}>
              <div
                className={styles.detailsTitle}
                style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                onClick={(e) => {
                  e.stopPropagation()
                  setExpandedResult(!expandedResult)
                }}
              >
                {expandedResult ? <ChevronDown24Regular /> : <ChevronRight24Regular />}
                Tool Result
              </div>
              {expandedResult && (
                <div className={styles.codeBlock}>
                  {JSON.stringify(resultData, null, 2)}
                </div>
              )}
            </div>
          )}

          {trace.output && (
            <div className={styles.detailsSection}>
              <div className={styles.detailsTitle}>Output</div>
              <div className={styles.codeBlock}>
                {JSON.stringify(trace.output, null, 2)}
              </div>
            </div>
          )}

          {trace.error && (
            <div className={styles.detailsSection}>
              <div className={styles.detailsTitle}>Error</div>
              <div className={styles.errorBlock}>{trace.error}</div>
            </div>
          )}
        </div>
      )}

      {hasChildren && expanded && (
        <div className={styles.nestedTraces}>
          {trace.children!.map((childTrace) => (
            <TraceItem
              key={childTrace.id}
              trace={childTrace}
              depth={depth + 1}
              isStreaming={isStreaming}
            />
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * TracePanel Component
 * Root component for displaying trace hierarchy
 */
export const TracePanel: React.FC<TracePanelProps> = ({ traces, isStreaming = false }) => {
  const styles = useStyles()

  if (!traces || traces.length === 0) {
    return (
      <div className={styles.container}>
        <Text className={styles.title}>Tool Calls & Traces</Text>
        <Text className={styles.empty}>
          {isStreaming ? 'Waiting for tool calls...' : 'No tool calls in this response'}
        </Text>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <Text className={styles.title}>Tool Calls & Traces ({traces.length})</Text>
      <div className={styles.tracesList}>
        {traces.map((trace) => (
          <TraceItem
            key={trace.id}
            trace={trace}
            depth={0}
            isStreaming={isStreaming}
          />
        ))}
      </div>
    </div>
  )
}

export default TracePanel
