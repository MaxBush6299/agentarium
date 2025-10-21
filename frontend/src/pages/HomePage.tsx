/**
 * Home Page
 * Landing page with welcome message and quick actions
 */

import { useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  CardHeader,
  makeStyles,
  tokens,
} from '@fluentui/react-components'
import {
  Chat24Regular,
  PeopleTeam24Regular,
  Lightbulb24Regular,
} from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '48px',
    backgroundColor: tokens.colorNeutralBackground1,
  },
  hero: {
    textAlign: 'center',
    marginBottom: '48px',
  },
  title: {
    fontSize: '48px',
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: '16px',
    color: tokens.colorNeutralForeground1,
  },
  subtitle: {
    fontSize: '18px',
    color: tokens.colorNeutralForeground3,
    maxWidth: '600px',
  },
  cards: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '24px',
    maxWidth: '1200px',
    width: '100%',
  },
  card: {
    cursor: 'pointer',
    transition: 'transform 0.2s',
    ':hover': {
      transform: 'translateY(-4px)',
    },
  },
  cardContent: {
    padding: '24px',
  },
  cardIcon: {
    fontSize: '48px',
    marginBottom: '16px',
    color: tokens.colorBrandForeground1,
  },
  cardTitle: {
    fontSize: '20px',
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: '8px',
  },
  cardDescription: {
    fontSize: '14px',
    color: tokens.colorNeutralForeground3,
    marginBottom: '16px',
  },
})

/**
 * HomePage Component
 */
export const HomePage = () => {
  const styles = useStyles()
  const navigate = useNavigate()

  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <h1 className={styles.title}>Welcome to Agent Framework</h1>
        <p className={styles.subtitle}>
          An intelligent multi-agent system powered by Azure OpenAI, featuring
          real-time streaming, tracing, and agent-to-agent communication.
        </p>
      </div>

      <div className={styles.cards}>
        <Card className={styles.card} onClick={() => navigate('/chat')}>
          <div className={styles.cardContent}>
            <div className={styles.cardIcon}>
              <Chat24Regular />
            </div>
            <CardHeader
              header={<div className={styles.cardTitle}>Start Chatting</div>}
              description={
                <div className={styles.cardDescription}>
                  Begin a conversation with our AI agents. Choose from support
                  triage, Azure operations, and more.
                </div>
              }
            />
            <Button appearance="primary">Go to Chat</Button>
          </div>
        </Card>

        <Card className={styles.card} onClick={() => navigate('/agents')}>
          <div className={styles.cardContent}>
            <div className={styles.cardIcon}>
              <PeopleTeam24Regular />
            </div>
            <CardHeader
              header={<div className={styles.cardTitle}>Browse Agents</div>}
              description={
                <div className={styles.cardDescription}>
                  Explore available AI agents, their capabilities, and
                  specializations.
                </div>
              }
            />
            <Button>View Agents</Button>
          </div>
        </Card>

        <Card className={styles.card}>
          <div className={styles.cardContent}>
            <div className={styles.cardIcon}>
              <Lightbulb24Regular />
            </div>
            <CardHeader
              header={<div className={styles.cardTitle}>Features</div>}
              description={
                <div className={styles.cardDescription}>
                  • Real-time SSE streaming<br />
                  • Tool execution tracing<br />
                  • Agent-to-agent communication<br />
                  • Persistent conversation threads
                </div>
              }
            />
          </div>
        </Card>
      </div>
    </div>
  )
}
