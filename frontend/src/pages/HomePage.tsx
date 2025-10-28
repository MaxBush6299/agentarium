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
  Book24Regular,
} from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '48px',
    background: 'linear-gradient(135deg, #0e1419 0%, #1a2530 100%)',
  },
  hero: {
    textAlign: 'center',
    marginBottom: '48px',
  },
  logo: {
    width: '300px',
    height: 'auto',
    marginBottom: '24px',
    marginTop: '24px',
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
    background: 'linear-gradient(135deg, #1a2530 0%, #243240 100%)',
    border: '1px solid #2d3e4a',
    boxShadow: '0 2px 8px rgba(27, 137, 187, 0.2)',
    transition: 'all 0.3s ease',
    ':hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 8px 16px rgba(59, 176, 221, 0.3)',
      border: '1px solid #3fb0dd',
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
        <img src="/logo.jpg" alt="Agentarium Logo" className={styles.logo} />
        <h1 className={styles.title}>Welcome to Agentarium</h1>
        <p className={styles.subtitle}>
          A curated space for agent experiments and demos. Explore intelligent multi-agent patterns 
          powered by Azure OpenAI, featuring real-time streaming, tracing, and agent-to-agent communication.
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

        <Card className={styles.card} onClick={() => navigate('/how-it-works')}>
          <div className={styles.cardContent}>
            <div className={styles.cardIcon}>
              <Book24Regular />
            </div>
            <CardHeader
              header={<div className={styles.cardTitle}>How It Works</div>}
              description={
                <div className={styles.cardDescription}>
                  Learn about thread management, agent architecture, and the
                  technology powering Agentarium.
                </div>
              }
            />
            <Button>Learn More</Button>
          </div>
        </Card>
      </div>
    </div>
  )
}
