/**
 * App Layout Component
 * Main navigation and outlet for pages
 */

import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Tab,
  TabList,
  makeStyles,
  tokens,
} from '@fluentui/react-components'
import {
  Chat24Regular,
  PeopleTeam24Regular,
  Home24Regular,
  Book24Regular,
} from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: 'linear-gradient(135deg, #0e1419 0%, #1a2530 100%)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 24px',
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    background: 'linear-gradient(90deg, #1a2530 0%, #243240 100%)',
    boxShadow: '0 2px 8px rgba(27, 137, 187, 0.2)',
  },
  title: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: tokens.fontSizeBase500,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
  },
  logo: {
    width: '48px',
    height: '48px',
    objectFit: 'contain',
  },
  nav: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  content: {
    flex: 1,
    overflow: 'hidden',
    position: 'relative',
  },
})

/**
 * AppLayout Component
 */
export const AppLayout = () => {
  const styles = useStyles()
  const navigate = useNavigate()
  const location = useLocation()

  const getSelectedTab = () => {
    if (location.pathname.startsWith('/chat')) return 'chat'
    if (location.pathname.startsWith('/agents')) return 'agents'
    if (location.pathname.startsWith('/how-it-works')) return 'how-it-works'
    return 'home'
  }

  const handleTabSelect = (_: any, data: any) => {
    const value = data.value as string
    navigate(value === 'home' ? '/' : `/${value}`)
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.title}>
          <img src="/favicon.png" alt="Agentarium" className={styles.logo} />
          Agentarium
        </div>
        <nav className={styles.nav}>
          <TabList
            selectedValue={getSelectedTab()}
            onTabSelect={handleTabSelect}
          >
            <Tab value="home" icon={<Home24Regular />}>
              Home
            </Tab>
            <Tab value="chat" icon={<Chat24Regular />}>
              Chat
            </Tab>
            <Tab value="agents" icon={<PeopleTeam24Regular />}>
              Agents
            </Tab>
            <Tab value="how-it-works" icon={<Book24Regular />}>
              How It Works
            </Tab>
          </TabList>
        </nav>
      </header>
      <main className={styles.content}>
        <Outlet />
      </main>
    </div>
  )
}
