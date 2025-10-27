/**
 * App Layout Component
 * Main navigation and outlet for pages
 */

import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Button,
  Tab,
  TabList,
  makeStyles,
  tokens,
} from '@fluentui/react-components'
import {
  Chat24Regular,
  PeopleTeam24Regular,
  Home24Regular,
} from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    backgroundColor: tokens.colorNeutralBackground1,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 24px',
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground2,
  },
  title: {
    fontSize: tokens.fontSizeBase500,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
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
    return 'home'
  }

  const handleTabSelect = (_: any, data: any) => {
    const value = data.value as string
    navigate(value === 'home' ? '/' : `/${value}`)
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.title}>🤖 Agentarium</div>
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
          </TabList>
        </nav>
      </header>
      <main className={styles.content}>
        <Outlet />
      </main>
    </div>
  )
}
