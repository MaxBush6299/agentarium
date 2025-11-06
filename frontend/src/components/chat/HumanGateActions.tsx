import React, { useState } from 'react'
import { Button, makeStyles, Text } from '@fluentui/react-components'
import { apiPost } from '../../services/api'
import { useParams } from 'react-router-dom'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    gap: '16px',
    marginTop: '16px',
    justifyContent: 'center',
  },
  statusMessage: {
    marginTop: '8px',
    textAlign: 'center',
    fontStyle: 'italic',
  },
})

export interface HumanGateActionsProps {
  onAction?: (action: 'approve' | 'edit' | 'reject', result?: any) => void
  disabled?: boolean
}

export const HumanGateActions: React.FC<HumanGateActionsProps> = ({ onAction, disabled }) => {
  const styles = useStyles()
  const { threadId } = useParams<{ threadId: string }>()
  const [isProcessing, setIsProcessing] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string>('')

  const handleClick = async (action: 'approve' | 'edit' | 'reject') => {
    try {
      setIsProcessing(true)
      setStatusMessage('Processing approval...')
      
      // Base URL already includes /api, so omit leading /api here
      const response = await apiPost('human-gate/action', { 
        action,
        thread_id: threadId 
      })
      
      const res = response as { result?: any; status?: string; approval_response?: any; message?: string }
      
      if (res.status === 'approved_continue_workflow') {
        setStatusMessage(`✅ Approved! ${res.message || 'Continuing workflow...'}`)
        if (onAction) {
          onAction(action, res.result)
        }
        // Call resume endpoint to generate Phase 7 block
        try {
          const resumeRes = await apiPost<any>('human-gate/resume', { thread_id: threadId })
          console.log('Resume response:', resumeRes)
          setStatusMessage('✅ Purchase order generated.')
          // Dispatch custom event so ChatPage can add a new phase message
          const phaseEvent = new CustomEvent('rfq-phase', {
            detail: {
              type: 'agent_section',
              phase: 'phase7_complete',
              title: 'Phase 7: Purchase Order',
              markdown: resumeRes.markdown,
              metrics: {
                duration_ms: 0,
                prompt_tokens: 0,
                completion_tokens: 0,
                total_tokens: 0,
                estimated: true,
              },
              data: {
                purchase_order: resumeRes.purchase_order,
              },
              subBlocks: [],
              isPhaseMessage: true,
            }
          })
          window.dispatchEvent(phaseEvent)
        } catch (resumeErr) {
          console.error('Failed to resume workflow:', resumeErr)
          setStatusMessage('⚠️ Approved but failed to resume workflow (see console).')
        }
      } else if (res.status === 'workflow_terminated') {
        setStatusMessage(`✅ ${action === 'reject' ? 'Rejected' : 'Completed'}. ${res.message || ''}`)
        if (onAction) {
          onAction(action, res.result)
        }
      } else {
        setStatusMessage('✅ Action completed')
        if (onAction) {
          onAction(action, res.result)
        }
      }
    } catch (error) {
      console.error('Approval action failed:', error)
      setStatusMessage('❌ Failed to process approval')
      if (onAction) {
        onAction(action, { error })
      }
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div>
      <div className={styles.container}>
        <Button 
          appearance="primary" 
          disabled={disabled || isProcessing} 
          onClick={() => handleClick('approve')}
        >
          {isProcessing ? 'Processing...' : 'Approve'}
        </Button>
        <Button 
          appearance="outline" 
          disabled={disabled || isProcessing} 
          onClick={() => handleClick('reject')}
        >
          {isProcessing ? 'Processing...' : 'Reject'}
        </Button>
      </div>
      {statusMessage && (
        <Text className={styles.statusMessage}>
          {statusMessage}
        </Text>
      )}
    </div>
  )
}
