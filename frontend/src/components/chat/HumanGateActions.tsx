import React from 'react'
import { Button, makeStyles } from '@fluentui/react-components'
import { apiPost } from '../../services/api'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    gap: '16px',
    marginTop: '16px',
    justifyContent: 'center',
  },
})

export interface HumanGateActionsProps {
  onAction?: (action: 'approve' | 'edit' | 'reject', result?: any) => void
  disabled?: boolean
}

export const HumanGateActions: React.FC<HumanGateActionsProps> = ({ onAction, disabled }) => {
  const styles = useStyles()

  const handleClick = async (action: 'approve' | 'edit' | 'reject') => {
    try {
      const response = await apiPost('/api/human-gate/action', { action })
      if (onAction) {
        const res = response as { result?: any }
        onAction(action, res.result)
      }
    } catch (error) {
      // Optionally handle error
      if (onAction) {
        onAction(action, { error })
      }
    }
  }

  return (
    <div className={styles.container}>
      <Button appearance="primary" disabled={disabled} onClick={() => handleClick('approve')}>
        Approve
      </Button>
      <Button appearance="secondary" disabled={disabled} onClick={() => handleClick('edit')}>
        Edit
      </Button>
      <Button appearance="outline" disabled={disabled} onClick={() => handleClick('reject')}>
        Reject
      </Button>
    </div>
  )
}
