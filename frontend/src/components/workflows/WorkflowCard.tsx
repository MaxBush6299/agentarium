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
  Tooltip,
} from '@fluentui/react-components';
import {
  Play24Regular,
  Settings24Regular,
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
  onWorkflowDeleted?: (workflowId: string) => void;
}

/**
 * WorkflowCard Component
 */
export const WorkflowCard = ({ workflow, onWorkflowDeleted }: WorkflowCardProps) => {
  const styles = useStyles();
  const navigate = useNavigate();

  const handleViewDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/workflows/${workflow.id}`);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/workflows/${workflow.id}/edit`);
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
            onClick={handleViewDetails}
          >
            View Details
          </Button>
          <Button
            appearance="subtle"
            icon={<Settings24Regular />}
            onClick={handleEdit}
          >
            Edit
          </Button>
          {onWorkflowDeleted && (
            <Button
              appearance="subtle"
              onClick={() => onWorkflowDeleted(workflow.id)}
            >
              Delete
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};