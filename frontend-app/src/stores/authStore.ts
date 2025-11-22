import { createStore } from 'zustand/vanilla'
import { immer } from 'zustand/middleware/immer'
import { persist, devtools } from 'zustand/middleware'
import { createIndexedDBStorage, STORE_NAMES } from '../lib/indexedDBStorage'
import type { AuthStore } from '../types/stores'
import { api } from '../lib/api'
import { toast } from '../lib/toast'
import { generateUUID } from '../utils/uuid'

// Initial state
const initialState = {
  userId: null as string | null,
  email: null as string | null,
  name: null as string | null,
  shadowUserId: generateUUID(), // Generate shadow user ID for anonymous sessions
  accessToken: null as string | null,
  refreshToken: null as string | null,
  tokenExpiresAt: null as number | null,
  isAuthenticated: false,
}

// Create the vanilla store with devtools, persist, and immer middleware
export const createAuthStore = () => {
  const store = createStore<AuthStore>()(
    devtools(
      persist(
        immer((set, get) => ({
          ...initialState,

          // Authentication operations
          login: async (credentials: { email: string; password: string }) => {
            try {
              // Call backend API: POST /api/v1/auth/login
              const response = await api.post<{
                access_token: string
                refresh_token: string
                expires_in: number
                user: {
                  id: string
                  email: string
                  name: string
                }
              }>('/auth/login', credentials)

              // Calculate token expiration time
              const expiresAt = Date.now() + response.expires_in * 1000

              set((state) => {
                state.userId = response.user.id
                state.email = response.user.email
                state.name = response.user.name
                state.accessToken = response.access_token
                state.refreshToken = response.refresh_token
                state.tokenExpiresAt = expiresAt
                state.isAuthenticated = true
              })

              toast.success('Logged in successfully')
            } catch (error) {
              console.error('Login failed:', error)
              toast.error('Login failed', {
                description: error instanceof Error ? error.message : 'Invalid credentials',
              })
              throw error
            }
          },

          logout: async () => {
            try {
              const { refreshToken } = get()

              // Call backend API: POST /api/v1/auth/logout
              if (refreshToken) {
                await api.post('/auth/logout', { refresh_token: refreshToken })
              }

              set((state) => {
                state.userId = null
                state.email = null
                state.name = null
                state.accessToken = null
                state.refreshToken = null
                state.tokenExpiresAt = null
                state.isAuthenticated = false
                // Keep shadow user ID for anonymous session
              })

              toast.success('Logged out successfully')
            } catch (error) {
              console.error('Logout failed:', error)
              // Still clear local state even if backend call fails
              set((state) => {
                state.userId = null
                state.email = null
                state.name = null
                state.accessToken = null
                state.refreshToken = null
                state.tokenExpiresAt = null
                state.isAuthenticated = false
              })
            }
          },

          refreshAuthToken: async () => {
            try {
              const { refreshToken: currentRefreshToken } = get()

              if (!currentRefreshToken) {
                throw new Error('No refresh token available')
              }

              // Call backend API: POST /api/v1/auth/refresh
              const response = await api.post<{
                access_token: string
                refresh_token?: string
                expires_in: number
              }>('/auth/refresh', { refresh_token: currentRefreshToken })

              // Calculate token expiration time
              const expiresAt = Date.now() + response.expires_in * 1000

              set((state) => {
                state.accessToken = response.access_token
                if (response.refresh_token) {
                  state.refreshToken = response.refresh_token
                }
                state.tokenExpiresAt = expiresAt
                state.isAuthenticated = true
              })

              console.log('Token refreshed successfully')
            } catch (error) {
              console.error('Token refresh failed:', error)
              // Clear authentication on refresh failure
              set((state) => {
                state.userId = null
                state.email = null
                state.name = null
                state.accessToken = null
                state.refreshToken = null
                state.tokenExpiresAt = null
                state.isAuthenticated = false
              })
              throw error
            }
          },

          setShadowUser: (id: string) => {
            set((state) => {
              state.shadowUserId = id
            })
          },

          // Utility
          reset: () => {
            set({
              ...initialState,
              shadowUserId: generateUUID(), // Generate new shadow user ID on reset
            })
          },
        })),
        {
          name: 'auth-store',
          storage: createIndexedDBStorage(STORE_NAMES.AUTH) as any,
          // Custom serialization to avoid persisting sensitive data
          serialize: (state: any) => {
            return JSON.stringify({
              state: {
                userId: state.state.userId,
                email: state.state.email,
                name: state.state.name,
                shadowUserId: state.state.shadowUserId,
                // Don't persist tokens for security
              },
              version: state.version,
            })
          },
          deserialize: (str: string) => {
            const parsed = JSON.parse(str)
            return {
              state: {
                ...initialState,
                userId: parsed.state?.userId || null,
                email: parsed.state?.email || null,
                name: parsed.state?.name || null,
                shadowUserId: parsed.state?.shadowUserId || generateUUID(),
              },
              version: parsed.version,
            }
          },
        } as any
      ),
      { name: 'AuthStore' }
    )
  )

  // Check token expiration on store creation
  const checkTokenExpiration = () => {
    const state = store.getState()
    if (state.tokenExpiresAt && Date.now() >= state.tokenExpiresAt) {
      // Token expired, attempt refresh or logout
      if (state.refreshToken) {
        state.refreshAuthToken().catch(() => {
          // Refresh failed, user needs to log in again
          console.log('Session expired, please log in again')
        })
      } else {
        store.setState({
          ...state,
          isAuthenticated: false,
          accessToken: null,
        })
      }
    }
  }

  // Check expiration on creation
  checkTokenExpiration()

  // Set up periodic token expiration check (every minute)
  setInterval(checkTokenExpiration, 60000)

  return store
}

// Export type for the store instance
export type AuthStoreInstance = ReturnType<typeof createAuthStore>
