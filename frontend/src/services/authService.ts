/**
 * MSAL Authentication Service
 * Handles Entra ID authentication and token management
 */

import { PublicClientApplication, IPublicClientApplication } from '@azure/msal-browser'
import { config } from '@/config'

let msalInstance: IPublicClientApplication | null = null

/**
 * Initialize MSAL client
 */
export const initializeMsal = async (): Promise<IPublicClientApplication> => {
  if (msalInstance) {
    return msalInstance
  }

  const msalConfig = {
    auth: {
      clientId: config.auth.clientId,
      authority: config.auth.authority,
      redirectUri: config.auth.redirectUri,
    },
    cache: {
      cacheLocation: 'localStorage',
      storeAuthStateInCookie: false,
    },
  }

  msalInstance = new PublicClientApplication(msalConfig)
  await msalInstance.initialize()
  return msalInstance
}

/**
 * Get MSAL instance
 */
export const getMsalInstance = (): IPublicClientApplication | null => {
  return msalInstance
}

/**
 * Login user
 */
export const login = async (): Promise<void> => {
  const instance = msalInstance || (await initializeMsal())
  try {
    await instance.loginPopup({
      scopes: config.auth.scopes,
      redirectUri: config.auth.redirectUri,
    })
  } catch (error) {
    console.error('Login error:', error)
    throw error
  }
}

/**
 * Logout user
 */
export const logout = async (): Promise<void> => {
  const instance = msalInstance || (await initializeMsal())
  try {
    await instance.logoutPopup()
  } catch (error) {
    console.error('Logout error:', error)
    throw error
  }
}

/**
 * Get access token
 */
export const getAccessToken = async (): Promise<string | null> => {
  const instance = msalInstance || (await initializeMsal())

  try {
    const accounts = instance.getAllAccounts()
    if (accounts.length === 0) {
      return null
    }

    const response = await instance.acquireTokenSilent({
      account: accounts[0],
      scopes: config.auth.scopes,
    })

    return response.accessToken
  } catch (error) {
    console.error('Token acquisition error:', error)
    return null
  }
}

/**
 * Get user info
 */
export const getUserInfo = () => {
  const instance = msalInstance || (initializeMsal().catch(() => null))
  if (!instance) return null

  const accounts = instance.getAllAccounts()
  if (accounts.length === 0) return null

  return {
    id: accounts[0].homeAccountId,
    name: accounts[0].name,
    username: accounts[0].username,
  }
}

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  const instance = msalInstance
  if (!instance) return false

  const accounts = instance.getAllAccounts()
  return accounts.length > 0
}
