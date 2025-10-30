/**
 * Workflow Card Component
 * Displays workflow information in a card format
 */

import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  Button,
  Badge,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import {
  Play24Regular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  card: {
    height: '300px',
    cursor: 'pointer',
    background: 'linear-gradient(135deg, #1a2530 0%, #243240 100%)',
    border: '1px solid #2d3e4a',
    boxShadow: '0 2px 8px rgba(27, 137, 187, 0.2)',
    transition: 'all 0.3s ease',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 8px 16px rgba(59, 176, 221, 0.3)',
      border: '1px solid #3fb0dd',
    },
  },
  content: {
    padding: '24px',
  },
  title: {
    fontSize: '20px',
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: '12px',
    color: '#f0fcff',
  },
  description: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: '#bdeffc',
    marginBottom: '20px',
    minHeight: '80px',
  },
  badges: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginBottom: '16px',
  },
  actions: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
});

interface WorkflowCardProps {
  workflow: {
    id: string;
    name: string;
    description: string;
    status: string;
    associatedAgents: string[];
  };
}

/**
 * WorkflowCard Component
 */
export const WorkflowCard = ({ workflow }: WorkflowCardProps) => {
  const styles = useStyles();
  const navigate = useNavigate();

  const handleStartChat = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Navigate to chat page with workflow ID as query parameter
    navigate(`/chat?workflow=${workflow.id}`);
  };

  return (
    <Card className={styles.card}>
      <div className={styles.content}>
        <CardHeader
          header={<div className={styles.title}>{workflow.name}</div>}
          description={
            <div className={styles.badges}>
              <Badge appearance="filled" color="success">
                {(workflow.status || 'unknown').toUpperCase()}
              </Badge>
              <Badge appearance="outline">
                {(workflow.associatedAgents || []).length} Agents
              </Badge>
            </div>
          }
        />

        <p className={styles.description}>{workflow.description}</p>

        <div className={styles.actions}>
          <Button
            appearance="primary"
            icon={<Play24Regular />}
            onClick={handleStartChat}
          >
            Start Chat
          </Button>
        </div>
      </div>
    </Card>
  );
};