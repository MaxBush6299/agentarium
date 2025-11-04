/**
 * useTraces Hook
 * Manages trace events from SSE streaming and maintains hierarchical trace structure
 */

import { useState, useCallback, useRef } from 'react'
import { TraceEvent } from '@/components/chat/TracePanel'

interface TraceEventData {
  type: 'token' | 'trace_start' | 'trace_update' | 'trace_end' | 'done' | 'error'
  timestamp: string
  [key: string]: unknown
}

export interface UseTracesReturn {
  traces: TraceEvent[]
  addTraceEvent: (event: TraceEventData) => void
  clearTraces: () => void
  getTraceById: (id: string) => TraceEvent | undefined
}

/**
 * useTraces Hook
 * Parses SSE trace events and maintains a hierarchical structure
 */
export const useTraces = (): UseTracesReturn => {
  const [traces, setTraces] = useState<TraceEvent[]>([])
  const traceMapRef = useRef<Map<string, TraceEvent>>(new Map())
  const parentStackRef = useRef<string[]>([]) // Stack of parent trace IDs

  const getTraceById = useCallback(
    (id: string): TraceEvent | undefined => {
      return traceMapRef.current.get(id)
    },
    []
  )

  const addTraceEvent = useCallback((event: TraceEventData) => {
    const eventType = event.type as string

    if (eventType === 'trace_start') {
      // New trace started
      const stepId = (event.step_id as string) || `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const newTrace: TraceEvent = {
        id: stepId,
        type: 'tool_call',
        name: (event.tool_name as string) || 'Unknown Tool',
        toolType: (event.tool_type as string) || 'tool',
        status: 'pending',
        startTime: Date.now(),
        input: (event.input as Record<string, unknown>) || {},
        metadata: {
          mcpServer: event.mcp_server as string | undefined,
          openapEndpoint: event.openapi_endpoint as string | undefined,
          a2aAgent: event.a2a_agent as string | undefined,
        },
      }

      traceMapRef.current.set(stepId, newTrace)

      // Add to parent if there's a parent in stack
      const parentId = parentStackRef.current[parentStackRef.current.length - 1]
      if (parentId) {
        const parent = traceMapRef.current.get(parentId)
        if (parent) {
          if (!parent.children) {
            parent.children = []
          }
          parent.children.push(newTrace)
        }
      } else {
        // Root level trace
        setTraces((prev) => [...prev, newTrace])
      }

      // Push to parent stack for nested traces
      parentStackRef.current.push(stepId)
    } else if (eventType === 'trace_update') {
      // Update trace status
      const stepId = event.step_id as string
      const trace = traceMapRef.current.get(stepId)
      if (trace) {
        trace.status = (event.status as 'pending' | 'success' | 'error') || 'pending'
      }
      setTraces((prev) => [...prev]) // Trigger re-render
    } else if (eventType === 'trace_end') {
      // Trace completed
      const stepId = event.step_id as string
      const trace = traceMapRef.current.get(stepId)

      console.log('🔧 trace_end processing:', {
        stepId,
        traceFound: !!trace,
        hasEventOutput: !!event.output,
        eventOutput: event.output,
        eventOutputKeys: event.output ? Object.keys(event.output as any) : [],
        hasAgentInteractions: !!(event.output as any)?.agent_interactions,
        eventKeys: Object.keys(event)
      });

      if (trace) {
        trace.status = (event.status as 'success' | 'error') || 'success'
        trace.endTime = Date.now()
        trace.latencyMs = (event.latency_ms as number) || (trace.endTime - trace.startTime)
        trace.output = (event.output as Record<string, unknown>) || undefined
        trace.error = (event.error as string) || undefined
        
        console.log('🔧 trace updated with output:', {
          traceId: trace.id,
          hasOutput: !!trace.output,
          outputKeys: trace.output ? Object.keys(trace.output) : [],
          hasAgentInteractions: !!trace.output?.agent_interactions,
          agentInteractionsValue: trace.output?.agent_interactions
        });

        // Add token info if present
        if (event.tokens_input || event.tokens_output || event.tokens_total) {
          trace.tokens = {
            input: event.tokens_input as number | undefined,
            output: event.tokens_output as number | undefined,
            total: event.tokens_total as number | undefined,
          }
        }
      }

      // Pop from parent stack
      if (parentStackRef.current[parentStackRef.current.length - 1] === stepId) {
        parentStackRef.current.pop()
      }

      setTraces((prev) => [...prev]) // Trigger re-render
    }
  }, [])

  const clearTraces = useCallback(() => {
    setTraces([])
    traceMapRef.current.clear()
    parentStackRef.current = []
  }, [])

  return {
    traces,
    addTraceEvent,
    clearTraces,
    getTraceById,
  }
}
