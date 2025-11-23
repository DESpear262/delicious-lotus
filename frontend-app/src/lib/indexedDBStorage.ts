import type { StateStorage } from 'zustand/middleware'

/**
 * IndexedDB storage adapter for Zustand persist middleware
 * Provides persistent storage for store state using IndexedDB
 */

const DB_NAME = 'chronos-editor-storage'
const DB_VERSION = 3 // Incremented for auth and ui stores

// Store names in IndexedDB
export const STORE_NAMES = {
  PROJECT: 'project-store',
  MEDIA: 'media-store',
  TIMELINE: 'timeline-store',
  EDITOR: 'editor-store',
  AI_GENERATION: 'ai-generation-store',
  AUTH: 'auth-store',
  UI: 'ui-store',
} as const

let dbInstance: IDBDatabase | null = null

/**
 * Initialize IndexedDB database
 */
async function initDB(): Promise<IDBDatabase> {
  if (dbInstance) {
    // Check if connection is closed or closing
    // There isn't a direct 'state' property on IDBDatabase in standard TS lib, 
    // but we can handle the error downstream or try to catch it here.
    // Best practice is to handle onversionchange to close it.
    return dbInstance
  }

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => {
      console.error('IndexedDB open error:', request.error)
      reject(request.error)
    }

    request.onsuccess = () => {
      dbInstance = request.result
      
      // Handle database version changes (e.g. open in another tab)
      dbInstance.onversionchange = () => {
        dbInstance?.close()
        dbInstance = null
      }
      
      dbInstance.onclose = () => {
        dbInstance = null
      }

      resolve(dbInstance)
    }

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result

      // Create object stores if they don't exist
      Object.values(STORE_NAMES).forEach((storeName) => {
        if (!db.objectStoreNames.contains(storeName)) {
          db.createObjectStore(storeName)
        }
      })
    }
  })
}

/**
 * Create IndexedDB storage adapter for a specific store
 */
export function createIndexedDBStorage(storeName: string): StateStorage {
  return {
    getItem: async (key: string): Promise<string | null> => {
      try {
        const db = await initDB()
        return new Promise((resolve, reject) => {
          const transaction = db.transaction(storeName, 'readonly')
          const store = transaction.objectStore(storeName)
          const request = store.get(key)

          request.onsuccess = () => resolve(request.result ?? null)
          request.onerror = () => reject(request.error)
        })
      } catch (error) {
        console.error(`Error reading from IndexedDB (${storeName}):`, error)
        return null
      }
    },

    setItem: async (key: string, value: string): Promise<void> => {
      try {
        let db = await initDB()
        
        // Retry once if transaction fails due to closed connection
        try {
          return await new Promise((resolve, reject) => {
            const transaction = db.transaction(storeName, 'readwrite')
            const store = transaction.objectStore(storeName)
            const request = store.put(value, key)
  
            request.onsuccess = () => resolve()
            request.onerror = () => reject(request.error)
          })
        } catch (error) {
          if ((error as DOMException).name === 'InvalidStateError') {
             dbInstance = null // Force reconnect
             db = await initDB()
             return new Promise((resolve, reject) => {
                const transaction = db.transaction(storeName, 'readwrite')
                const store = transaction.objectStore(storeName)
                const request = store.put(value, key)
      
                request.onsuccess = () => resolve()
                request.onerror = () => reject(request.error)
              })
          }
          throw error;
        }
      } catch (error) {
        console.error(`Error writing to IndexedDB (${storeName}):`, error)
      }
    },

    removeItem: async (key: string): Promise<void> => {
      try {
        const db = await initDB()
        return new Promise((resolve, reject) => {
          const transaction = db.transaction(storeName, 'readwrite')
          const store = transaction.objectStore(storeName)
          const request = store.delete(key)

          request.onsuccess = () => resolve()
          request.onerror = () => reject(request.error)
        })
      } catch (error) {
        console.error(`Error deleting from IndexedDB (${storeName}):`, error)
      }
    },
  }
}

/**
 * Clear all data from a specific store
 */
export async function clearStore(storeName: string): Promise<void> {
  try {
    const db = await initDB()
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.clear()

      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  } catch (error) {
    console.error(`Error clearing IndexedDB store (${storeName}):`, error)
  }
}

/**
 * Clear all data from all stores
 */
export async function clearAllStores(): Promise<void> {
  const promises = Object.values(STORE_NAMES).map((storeName) => clearStore(storeName))
  await Promise.all(promises)
}
