import React from 'react';
import { useNavigate } from 'react-router-dom';
import { makeStyles, shorthands, Card } from '@fluentui/react-components';
import { Chat24Regular, Bot24Regular, Book24Regular, BuildingMultiple24Regular, ShoppingBag24Regular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: 'linear-gradient(135deg, #0e1419 0%, #1a2530 100%)',
    overflowY: 'auto',
    ...shorthands.padding('2rem'),
  },
  header: {
    marginBottom: '2rem',
    textAlign: 'center',
  },
  title: {
    fontSize: '2.5rem',
    fontWeight: '700',
    color: '#f0fcff',
    marginBottom: '0.5rem',
  },
  subtitle: {
    fontSize: '1.125rem',
    color: '#7ad4f0',
  },
  content: {
    maxWidth: '1200px',
    width: '100%',
    marginLeft: 'auto',
    marginRight: 'auto',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
    ...shorthands.gap('2rem'),
    marginTop: '2rem',
  },
  card: {
    background: 'linear-gradient(135deg, #1a2530 0%, #243240 100%)',
    ...shorthands.borderRadius('12px'),
    ...shorthands.padding('2rem'),
    ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    ':hover': {
      ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.5)'),
      boxShadow: '0 12px 48px rgba(63, 176, 221, 0.15)',
      transform: 'translateY(-4px)',
    },
  },
  cardIcon: {
    fontSize: '3rem',
    color: '#3fb0dd',
    marginBottom: '1rem',
  },
  cardTitle: {
    fontSize: '1.5rem',
    fontWeight: '600',
    color: '#f0fcff',
    marginBottom: '0.75rem',
  },
  cardDescription: {
    fontSize: '1rem',
    color: '#bdeffc',
    lineHeight: '1.6',
  },
  cardMeta: {
    fontSize: '0.875rem',
    color: '#7ad4f0',
    marginTop: '1rem',
    fontStyle: 'italic',
  },
});

interface ArticleCard {
  id: string;
  title: string;
  description: string;
  icon: React.ReactElement;
  date: string;
  readTime: string;
}

export const HowItWorksLanding: React.FC = () => {
  const styles = useStyles();
  const navigate = useNavigate();

  const articles: ArticleCard[] = [
    {
        id: 'architecture',
        title: 'Architecture & Infrastructure',
        description:
            'Explore the cloud-native architecture powering Agentarium, from Azure Container Apps to Cosmos DB, built with infrastructure-as-code and Microsoft Agent Framework.',
        icon: <BuildingMultiple24Regular />,
        date: 'October 28, 2025',
        readTime: '12 min read',
    },
    {
      id: 'rfq-workflow',
      title: 'RFQ Procurement Workflow',
      description:
        'Discover how the RFQ workflow automates vendor selection with 7 sequential phases, parallel evaluation tracks, and human-in-the-loop approval—reducing procurement time from hours to seconds.',
      icon: <ShoppingBag24Regular />,
      date: 'October 31, 2025',
      readTime: '18 min read',
    },
    {
      id: 'thread-management',
      title: 'Thread Management',
      description:
        'Learn how Agentarium manages conversations with dual-layer architecture, combining in-memory execution with durable storage for seamless multi-turn conversations.',
      icon: <Chat24Regular />,
      date: 'October 28, 2025',
      readTime: '8 min read',
    },
    {
      id: 'agent-definitions',
      title: 'Agent Definitions',
      description:
        'Discover how agents are defined in Agentarium using the Microsoft Agent Framework, with configuration-driven design and flexible tool integration.',
      icon: <Bot24Regular />,
      date: 'October 28, 2025',
      readTime: '10 min read',
    },
  ];

  const handleCardClick = (articleId: string) => {
    navigate(`/how-it-works/${articleId}`);
  };

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <div className={styles.header}>
          <h1 className={styles.title}>
            <Book24Regular style={{ marginRight: '1rem', verticalAlign: 'middle' }} />
            How It Works
          </h1>
          <p className={styles.subtitle}>
            Learn about the architecture and features powering Agentarium
          </p>
        </div>

        <div className={styles.grid}>
          {articles.map((article) => (
            <Card
              key={article.id}
              className={styles.card}
              onClick={() => handleCardClick(article.id)}
            >
              <div className={styles.cardIcon}>{article.icon}</div>
              <h2 className={styles.cardTitle}>{article.title}</h2>
              <p className={styles.cardDescription}>{article.description}</p>
              <div className={styles.cardMeta}>
                {article.date} • {article.readTime}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
