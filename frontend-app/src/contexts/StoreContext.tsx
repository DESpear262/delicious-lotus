import { createContext, useContext, useRef, type ReactNode } from 'react'
import { useStore } from 'zustand'
import {
  createTimelineStore,
  type TimelineStoreInstance,
} from '../stores/timelineStore'
import {
  createMediaStore,
  type MediaStoreInstance,
} from '../stores/mediaStore'
import {
  createProjectStore,
  type ProjectStoreInstance,
} from '../stores/projectStore'
import {
  createEditorStore,
  type EditorStoreInstance,
} from '../stores/editorStore'
import { createWebSocketStore } from '../stores/webSocketStore'
import {
  createAIGenerationStore,
  type AIGenerationStoreInstance,
} from '../stores/aiGenerationStore'
import {
  createAuthStore,
  type AuthStoreInstance,
} from '../stores/authStore'
import {
  createUiStore,
  type UiStoreInstance,
} from '../stores/uiStore'
import type { TimelineStore, MediaStore, ProjectStore, EditorStore, WebSocketStore, AIGenerationStore, AuthStore, UiStore } from '../types/stores'
import type { StoreApi } from 'zustand/vanilla'

// Type for WebSocket store instance
type WebSocketStoreInstance = StoreApi<WebSocketStore>

// Create contexts for each store
const TimelineStoreContext = createContext<TimelineStoreInstance | null>(null)
const MediaStoreContext = createContext<MediaStoreInstance | null>(null)
const ProjectStoreContext = createContext<ProjectStoreInstance | null>(null)
const EditorStoreContext = createContext<EditorStoreInstance | null>(null)
const WebSocketStoreContext = createContext<WebSocketStoreInstance | null>(null)
const AIGenerationStoreContext = createContext<AIGenerationStoreInstance | null>(null)
const AuthStoreContext = createContext<AuthStoreInstance | null>(null)
const UiStoreContext = createContext<UiStoreInstance | null>(null)

// Provider props
interface StoreProviderProps {
  children: ReactNode
}

// Combined store provider component
export function StoreProvider({ children }: StoreProviderProps) {
  // Create store instances only once using refs
  const timelineStore = useRef<TimelineStoreInstance>()
  const mediaStore = useRef<MediaStoreInstance>()
  const projectStore = useRef<ProjectStoreInstance>()
  const editorStore = useRef<EditorStoreInstance>()
  const webSocketStore = useRef<WebSocketStoreInstance>()
  const aiGenerationStore = useRef<AIGenerationStoreInstance>()
  const authStore = useRef<AuthStoreInstance>()
  const uiStore = useRef<UiStoreInstance>()

  if (!timelineStore.current) {
    timelineStore.current = (createTimelineStore as any)()
  }
  if (!mediaStore.current) {
    mediaStore.current = (createMediaStore as any)()
  }
  if (!projectStore.current) {
    projectStore.current = (createProjectStore as any)()
  }
  if (!editorStore.current) {
    editorStore.current = (createEditorStore as any)()
  }
  if (!webSocketStore.current) {
    webSocketStore.current = (createWebSocketStore as any)()
  }
  if (!aiGenerationStore.current) {
    aiGenerationStore.current = (createAIGenerationStore as any)()
  }
  if (!authStore.current) {
    authStore.current = (createAuthStore as any)()
  }
  if (!uiStore.current) {
    uiStore.current = (createUiStore as any)()
  }

  return (
    <AuthStoreContext.Provider value={authStore.current}>
      <UiStoreContext.Provider value={uiStore.current}>
        <TimelineStoreContext.Provider value={timelineStore.current}>
          <MediaStoreContext.Provider value={mediaStore.current}>
            <ProjectStoreContext.Provider value={projectStore.current}>
              <EditorStoreContext.Provider value={editorStore.current}>
                <WebSocketStoreContext.Provider value={webSocketStore.current}>
                  <AIGenerationStoreContext.Provider value={aiGenerationStore.current}>
                    {children}
                  </AIGenerationStoreContext.Provider>
                </WebSocketStoreContext.Provider>
              </EditorStoreContext.Provider>
            </ProjectStoreContext.Provider>
          </MediaStoreContext.Provider>
        </TimelineStoreContext.Provider>
      </UiStoreContext.Provider>
    </AuthStoreContext.Provider>
  )
}

// Custom hooks for accessing stores

/**
 * Hook to access the Timeline store
 * @param selector - Optional selector function to pick specific state
 * @returns Selected state or entire store
 * @example
 * // Get entire store
 * const timelineStore = useTimelineStore()
 *
 * // Get specific state with selector
 * const playhead = useTimelineStore((state) => state.playhead)
 */
export function useTimelineStore<T = TimelineStore>(
  selector?: (state: TimelineStore) => T
): T {
  const store = useContext(TimelineStoreContext)
  if (!store) {
    throw new Error('useTimelineStore must be used within StoreProvider')
  }
  return useStore(store, selector || ((state) => state as T))
}

/**
 * Hook to access the Media store
 * @param selector - Optional selector function to pick specific state
 * @returns Selected state or entire store
 * @example
 * // Get entire store
 * const mediaStore = useMediaStore()
 *
 * // Get specific state with selector
 * const assets = useMediaStore((state) => Array.from(state.assets.values()))
 */
export function useMediaStore<T = MediaStore>(
  selector?: (state: MediaStore) => T
): T {
  const store = useContext(MediaStoreContext)
  if (!store) {
    throw new Error('useMediaStore must be used within StoreProvider')
  }
  return useStore(store, selector || ((state) => state as T))
}

/**
 * Hook to access the Project store
 * @param selector - Optional selector function to pick specific state
 * @returns Selected state or entire store
 * @example
 * // Get entire store
 * const projectStore = useProjectStore()
 *
 * // Get specific state with selector
 * const projectName = useProjectStore((state) => state.metadata.name)
 */
export function useProjectStore<T = ProjectStore>(
  selector?: (state: ProjectStore) => T
): T {
  const store = useContext(ProjectStoreContext)
  if (!store) {
    throw new Error('useProjectStore must be used within StoreProvider')
  }
  return useStore(store, selector || ((state) => state as T))
}

/**
 * Hook to access the Editor store
 * @param selector - Optional selector function to pick specific state
 * @returns Selected state or entire store
 * @example
 * // Get entire store
 * const editorStore = useEditorStore()
 *
 * // Get specific state with selector
 * const isPlaying = useEditorStore((state) => state.isPlaying)
 */
export function useEditorStore<T = EditorStore>(
  selector?: (state: EditorStore) => T
): T {
  const store = useContext(EditorStoreContext)
  if (!store) {
    throw new Error('useEditorStore must be used within StoreProvider')
  }
  return useStore(store, selector || ((state) => state as T))
}

/**
 * Hook to access the WebSocket store
 * @param selector - Optional selector function to pick specific state
 * @returns Selected state or entire store
 * @example
 * // Get entire store
 * const webSocketStore = useWebSocketStore()
 *
 * // Get specific state with selector
 * const connectionStatus = useWebSocketStore((state) => state.connectionStatus)
 */
export function useWebSocketStore<T = WebSocketStore>(
  selector?: (state: WebSocketStore) => T
): T {
  const store = useContext(WebSocketStoreContext)
  if (!store) {
    throw new Error('useWebSocketStore must be used within StoreProvider')
  }
  return useStore(store, selector || ((state) => state as T))
}

/**
 * Hook to access the AI Generation store
 * @param selector - Optional selector function to pick specific state
 * @returns Selected state or entire store
 * @example
 * // Get entire store
 * const aiGenerationStore = useAIGenerationStore()
 *
 * // Get specific state with selector
 * const activeGenerations = useAIGenerationStore((state) => Array.from(state.activeGenerations.values()))
 */
export function useAIGenerationStore<T = AIGenerationStore>(
  selector?: (state: AIGenerationStore) => T
): T {
  const store = useContext(AIGenerationStoreContext)
  if (!store) {
    throw new Error('useAIGenerationStore must be used within StoreProvider')
  }
  return useStore(store, selector || ((state) => state as T))
}

/**
 * Hook to access the Auth store
 * @param selector - Optional selector function to pick specific state
 * @returns Selected state or entire store
 * @example
 * // Get entire store
 * const authStore = useAuthStore()
 *
 * // Get specific state with selector
 * const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
 */
export function useAuthStore<T = AuthStore>(
  selector?: (state: AuthStore) => T
): T {
  const store = useContext(AuthStoreContext)
  if (!store) {
    throw new Error('useAuthStore must be used within StoreProvider')
  }
  return useStore(store, selector || ((state) => state as T))
}

/**
 * Hook to access the UI store
 * @param selector - Optional selector function to pick specific state
 * @returns Selected state or entire store
 * @example
 * // Get entire store
 * const uiStore = useUiStore()
 *
 * // Get specific state with selector
 * const toastQueue = useUiStore((state) => state.toastQueue)
 */
export function useUiStore<T = UiStore>(
  selector?: (state: UiStore) => T
): T {
  const store = useContext(UiStoreContext)
  if (!store) {
    throw new Error('useUiStore must be used within StoreProvider')
  }
  return useStore(store, selector || ((state) => state as T))
}

// Export context for advanced use cases
export {
  TimelineStoreContext,
  MediaStoreContext,
  ProjectStoreContext,
  EditorStoreContext,
  WebSocketStoreContext,
  AIGenerationStoreContext,
  AuthStoreContext,
  UiStoreContext,
}
