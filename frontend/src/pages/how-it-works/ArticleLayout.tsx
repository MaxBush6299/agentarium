import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { makeStyles, shorthands, Button } from '@fluentui/react-components';
import { ArrowLeft24Regular, Chat24Regular, Bot24Regular, BuildingMultiple24Regular, ShoppingBag24Regular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    height: '100vh',
    background: 'linear-gradient(135deg, #0e1419 0%, #1a2530 100%)',
    overflow: 'hidden',
  },
  sidebar: {
    width: '280px',
    background: 'linear-gradient(180deg, #1a2530 0%, #0e1419 100%)',
    ...shorthands.borderRight('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
    ...shorthands.padding('2rem', '1.5rem'),
    overflowY: 'auto',
    flexShrink: 0,
  },
  backButton: {
    marginBottom: '1.5rem',
    width: '100%',
    justifyContent: 'flex-start',
  },
  sidebarTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#f0fcff',
    marginBottom: '1.5rem',
  },
  tocList: {
    listStyle: 'none',
    ...shorthands.padding('0'),
    ...shorthands.margin('0'),
  },
  tocItem: {
    marginBottom: '0.75rem',
  },
  tocLink: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('0.5rem'),
    ...shorthands.padding('0.75rem', '1rem'),
    ...shorthands.borderRadius('8px'),
    color: '#7ad4f0',
    textDecoration: 'none',
    fontSize: '0.9rem',
    transition: 'all 0.2s ease',
    cursor: 'pointer',
    background: 'transparent',
    ...shorthands.border('1px', 'solid', 'transparent'),
    ':hover': {
      background: 'rgba(63, 176, 221, 0.1)',
      color: '#f0fcff',
      ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.3)'),
    },
  },
  tocLinkActive: {
    background: 'rgba(63, 176, 221, 0.15)',
    color: '#f0fcff',
    ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.5)'),
  },
  tocIcon: {
    fontSize: '1.25rem',
  },
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    ...shorthands.padding('2rem', '2rem', '1rem', '2rem'),
    flexShrink: 0,
    ...shorthands.borderBottom('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
    background: 'linear-gradient(180deg, #1a2530 0%, transparent 100%)',
  },
  articleTitle: {
    fontSize: '2.5rem',
    fontWeight: '700',
    color: '#f0fcff',
    marginBottom: '0.5rem',
  },
  articleMeta: {
    fontSize: '0.9rem',
    color: '#7ad4f0',
  },
  scrollableContent: {
    flex: 1,
    overflowY: 'auto',
    ...shorthands.padding('2rem'),
  },
  content: {
    maxWidth: '900px',
    color: '#bdeffc',
    lineHeight: '1.8',
    fontSize: '1rem',
    '& h2': {
      fontSize: '1.75rem',
      fontWeight: '600',
      color: '#f0fcff',
      marginTop: '2rem',
      marginBottom: '1rem',
    },
    '& h3': {
      fontSize: '1.35rem',
      fontWeight: '600',
      color: '#f0fcff',
      marginTop: '1.5rem',
      marginBottom: '0.75rem',
    },
    '& p': {
      marginBottom: '1rem',
    },
    '& ul, & ol': {
      marginLeft: '1.5rem',
      marginBottom: '1rem',
    },
    '& li': {
      marginBottom: '0.5rem',
    },
    '& code': {
      background: 'rgba(63, 176, 221, 0.1)',
      ...shorthands.padding('0.125rem', '0.5rem'),
      ...shorthands.borderRadius('4px'),
      color: '#7ad4f0',
      fontFamily: 'Consolas, Monaco, "Courier New", monospace',
      fontSize: '0.9em',
    },
    '& pre': {
      background: '#0e1419',
      ...shorthands.padding('1rem'),
      ...shorthands.borderRadius('8px'),
      ...shorthands.overflow('auto', 'auto'),
      marginBottom: '1rem',
      ...shorthands.border('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
      '& code': {
        background: 'transparent',
        padding: '0',
        color: '#bdeffc',
      },
    },
    '& table': {
      width: '100%',
      borderCollapse: 'collapse',
      marginBottom: '1rem',
      fontSize: '0.9rem',
    },
    '& th': {
      background: 'rgba(63, 176, 221, 0.1)',
      ...shorthands.padding('0.75rem'),
      textAlign: 'left',
      ...shorthands.borderBottom('2px', 'solid', '#3fb0dd'),
      color: '#f0fcff',
      fontWeight: '600',
    },
    '& td': {
      ...shorthands.padding('0.75rem'),
      ...shorthands.borderBottom('1px', 'solid', 'rgba(63, 176, 221, 0.2)'),
    },
    '& blockquote': {
      ...shorthands.borderLeft('4px', 'solid', '#3fb0dd'),
      ...shorthands.padding('0.5rem', '1rem'),
      marginLeft: '0',
      marginRight: '0',
      marginBottom: '1rem',
      background: 'rgba(63, 176, 221, 0.05)',
      color: '#7ad4f0',
      '& p': {
        margin: '0.5rem 0',
      },
      '& strong': {
        color: '#f0fcff',
      },
    },
  },
});

interface ArticleInfo {
  id: string;
  title: string;
  icon: React.ReactElement;
  date: string;
  author: string;
}

interface ArticleLayoutProps {
  children: React.ReactNode;
  title: string;
  date: string;
  author: string;
}

  const articles: ArticleInfo[] = [
    {
      id: 'thread-management',
      title: 'Thread Management',
      icon: <Chat24Regular />,
      date: 'October 28, 2025',
      author: 'Engineering Team',
    },
    {
      id: 'agent-definitions',
      title: 'Agent Definitions',
      icon: <Bot24Regular />,
      date: 'October 28, 2025',
      author: 'Engineering Team',
    },
    {
      id: 'architecture',
      title: 'Architecture & Infrastructure',
      icon: <BuildingMultiple24Regular />,
      date: 'October 28, 2025',
      author: 'Engineering Team',
    },
    {
      id: 'rfq-workflow',
      title: 'RFQ Procurement Workflow',
      icon: <ShoppingBag24Regular />,
      date: 'January 8, 2025',
      author: 'Engineering Team',
    },
  ];export const ArticleLayout: React.FC<ArticleLayoutProps> = ({ children, title, date, author }) => {
  const styles = useStyles();
  const navigate = useNavigate();
  const { articleId } = useParams<{ articleId: string }>();

  const handleArticleClick = (id: string) => {
    navigate(`/how-it-works/${id}`);
  };

  return (
    <div className={styles.container}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <Button
          appearance="subtle"
          icon={<ArrowLeft24Regular />}
          className={styles.backButton}
          onClick={() => navigate('/how-it-works')}
        >
          Back to Articles
        </Button>
        
        <h2 className={styles.sidebarTitle}>Articles</h2>
        <ul className={styles.tocList}>
          {articles.map((article) => (
            <li key={article.id} className={styles.tocItem}>
              <div
                className={`${styles.tocLink} ${articleId === article.id ? styles.tocLinkActive : ''}`}
                onClick={() => handleArticleClick(article.id)}
              >
                <span className={styles.tocIcon}>{article.icon}</span>
                <span>{article.title}</span>
              </div>
            </li>
          ))}
        </ul>
      </aside>

      {/* Main Content */}
      <div className={styles.mainContent}>
        <div className={styles.header}>
          <h1 className={styles.articleTitle}>{title}</h1>
          <div className={styles.articleMeta}>
            {date} • By {author}
          </div>
        </div>

        <div className={styles.scrollableContent}>
          <div className={styles.content}>{children}</div>
        </div>
      </div>
    </div>
  );
};
