/**
 * useAuth Hook
 * Custom hook for authentication operations
 */

import { useEffect, useState } from 'react'
import { login, logout, getAccessToken, getUserInfo, isAuthenticated } from '@/services/authService'

export interface User {
  name?: string
  email?: string
  upn?: string
  oid?: string
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const initAuth = async () => {
      try {
        setIsLoading(true)
        const authenticated = isAuthenticated()
        setIsLoggedIn(authenticated)

        if (authenticated) {
          const userInfo = getUserInfo()
          setUser(userInfo as User)
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to initialize auth'
        setError(message)
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  const handleLogin = async () => {
    try {
      setError(null)
      await login()
      setIsLoggedIn(true)
      const userInfo = getUserInfo()
      setUser(userInfo as User)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      setError(message)
    }
  }

  const handleLogout = async () => {
    try {
      setError(null)
      await logout()
      setIsLoggedIn(false)
      setUser(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Logout failed'
      setError(message)
    }
  }

  const getToken = async (): Promise<string | null> => {
    try {
      return await getAccessToken()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get access token'
      setError(message)
      return null
    }
  }

  return {
    user,
    isLoggedIn,
    isLoading,
    error,
    login: handleLogin,
    logout: handleLogout,
    getToken,
  }
}
