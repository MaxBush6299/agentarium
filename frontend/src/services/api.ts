/**
 * API Client Service
 * Axios instance with interceptors for authentication and error handling
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import { config } from '@/config'
import { getAccessToken } from './authService'

let apiClient: AxiosInstance | null = null

/**
 * Initialize API client with interceptors
 */
export const initializeApiClient = (): AxiosInstance => {
  if (apiClient) {
    return apiClient
  }

  apiClient = axios.create({
    baseURL: config.apiBaseUrl,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor: Add authorization header
  apiClient.interceptors.request.use(
    async (requestConfig) => {
      const token = await getAccessToken()
      if (token) {
        requestConfig.headers.Authorization = `Bearer ${token}`
      }
      return requestConfig
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor: Handle errors
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Redirect to login on 401
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )

  return apiClient
}

/**
 * Get API client instance
 */
export const getApiClient = (): AxiosInstance => {
  return apiClient || initializeApiClient()
}

/**
 * Make GET request
 */
export const apiGet = async <T>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> => {
  const client = getApiClient()
  const response = await client.get<T>(url, config)
  return response.data
}

/**
 * Make POST request
 */
export const apiPost = async <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> => {
  const client = getApiClient()
  const response = await client.post<T>(url, data, config)
  return response.data
}

/**
 * Make PUT request
 */
export const apiPut = async <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> => {
  const client = getApiClient()
  const response = await client.put<T>(url, data, config)
  return response.data
}

/**
 * Make DELETE request
 */
export const apiDelete = async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  const client = getApiClient()
  const response = await client.delete<T>(url, config)
  return response.data
}
