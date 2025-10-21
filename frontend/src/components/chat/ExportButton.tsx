/**
 * Export Button Component
 * Exports conversation and traces to CSV format
 */

import React, { useState } from 'react'
import {
  Button,
  Tooltip,
  makeStyles,
} from '@fluentui/react-components'
import { ArrowDownload24Regular } from '@fluentui/react-icons'
import { Message, MessageRole, TraceEvent } from '../../types/message'

interface ExportButtonProps {
  messages: Message[]
  traces?: TraceEvent[]
  agentId?: string
}

const useStyles = makeStyles({
  button: {
    minWidth: 'auto',
    padding: '8px 12px',
  },
})

/**
 * Convert messages and traces to CSV format
 */
const generateCSV = (messages: Message[], traces?: TraceEvent[]): string => {
  const rows: string[] = []
  
  // CSV Header
  rows.push(
    '"Timestamp","Role","Content","Type","Metadata"'
  )
  
  // Process messages
  for (const message of messages) {
    const timestamp = message.timestamp.toISOString()
    const role = message.role
    const content = escapeCSVField(message.content)
    const type = 'message'
    const metadata = escapeCSVField(
      JSON.stringify({
        agentId: message.agentId,
        agentName: message.agentName,
        isStreaming: message.isStreaming,
        error: message.error,
      })
    )
    
    rows.push(`"${timestamp}","${role}","${content}","${type}",${metadata}`)
    
    // Add traces that occurred after this user message
    if (
      traces &&
      traces.length > 0 &&
      role === MessageRole.USER
    ) {
      const traceRows = tracesToCSVRows(traces)
      rows.push(...traceRows)
    }
  }
  
  return rows.join('\n')
}

/**
 * Convert traces to CSV rows
 */
const tracesToCSVRows = (traces: TraceEvent[]): string[] => {
  const rows: string[] = []
  
  const processTrace = (trace: TraceEvent, depth: number = 0): void => {
    const indent = '  '.repeat(depth)
    const timestamp = new Date(trace.startTime).toISOString()
    const name = escapeCSVField(`${indent}${trace.name}`)
    const type = escapeCSVField(trace.type)
    
    const inputSummary = trace.input
      ? Object.keys(trace.input)
          .slice(0, 3)
          .map((k) => `${k}=...`)
          .join(', ')
      : ''
    
    const outputSummary = trace.output
      ? typeof trace.output === 'string'
        ? (trace.output as string).substring(0, 50)
        : JSON.stringify(trace.output).substring(0, 50)
      : ''
    
    const metadata = escapeCSVField(
      JSON.stringify({
        status: trace.status,
        latencyMs: trace.latencyMs,
        tokens: trace.tokens,
        toolType: trace.toolType,
        input: inputSummary,
        output: outputSummary,
        error: trace.error,
      })
    )
    
    rows.push(`"${timestamp}","tool","${name}","${type}",${metadata}`)
    
    // Add children traces
    if (trace.children && trace.children.length > 0) {
      for (const child of trace.children) {
        processTrace(child, depth + 1)
      }
    }
  }
  
  for (const trace of traces) {
    processTrace(trace)
  }
  
  return rows
}

/**
 * Escape CSV field values (handle quotes and commas)
 */
const escapeCSVField = (value: string): string => {
  if (typeof value !== 'string') {
    value = String(value)
  }
  // Escape double quotes and wrap in quotes if needed
  return value.replace(/"/g, '""')
}

/**
 * Generate filename for export
 */
const generateFilename = (agentId?: string): string => {
  const timestamp = new Date().toISOString().split('T')[0] // YYYY-MM-DD
  const time = new Date().toISOString().split('T')[1].split('.')[0].replace(/:/g, '-') // HH-MM-SS
  const agent = agentId ? `${agentId}-` : ''
  return `conversation-${agent}${timestamp}-${time}.csv`
}

/**
 * Trigger CSV file download
 */
const downloadCSV = (csv: string, filename: string): void => {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  
  link.click()
  
  // Cleanup
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * ExportButton Component
 */
export const ExportButton: React.FC<ExportButtonProps> = ({
  messages,
  traces = [],
  agentId,
}) => {
  const styles = useStyles()
  const [isExporting, setIsExporting] = useState(false)
  
  const handleExport = async () => {
    if (messages.length === 0) {
      alert('No messages to export. Start a conversation first.')
      return
    }
    
    try {
      setIsExporting(true)
      
      // Generate CSV
      const csv = generateCSV(messages, traces)
      
      // Generate filename
      const filename = generateFilename(agentId)
      
      // Trigger download
      downloadCSV(csv, filename)
      
      setIsExporting(false)
    } catch (error) {
      console.error('Export failed:', error)
      alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      setIsExporting(false)
    }
  }
  
  return (
    <Tooltip content="Export conversation and traces as CSV" relationship="label">
      <Button
        className={styles.button}
        appearance="subtle"
        icon={<ArrowDownload24Regular />}
        onClick={handleExport}
        disabled={isExporting || messages.length === 0}
        aria-label="Export conversation"
      >
        {isExporting ? 'Exporting...' : 'Export'}
      </Button>
    </Tooltip>
  )
}

export default ExportButton
