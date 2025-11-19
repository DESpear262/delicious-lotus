import { createStore } from 'zustand/vanilla'
import { immer } from 'zustand/middleware/immer'
import { devtools } from 'zustand/middleware'
import type { EditorStore, PreviewSettings, WorkspaceLayout, KeyboardShortcut } from '../types/stores'

// Default preview settings
const defaultPreviewSettings: PreviewSettings = {
  quality: 'half',
  resolution: { width: 960, height: 540 },
  isFullscreen: false,
  showSafeZones: false,
}

// Default workspace layout
const defaultWorkspace: WorkspaceLayout = {
  leftPanelWidth: 300,
  rightPanelWidth: 350,
  timelineHeight: 300,
  showMediaLibrary: true,
  showProperties: true,
  showEffects: false,
}

// Default keyboard shortcuts
const defaultShortcuts: KeyboardShortcut[] = [
  { key: ' ', modifiers: [], action: 'togglePlayback' },
  { key: 's', modifiers: [], action: 'split' },
  { key: 'd', modifiers: ['ctrl'], action: 'duplicate' },
  { key: 'Delete', modifiers: [], action: 'delete' },
  { key: 'Backspace', modifiers: [], action: 'delete' },
  { key: 'z', modifiers: ['ctrl'], action: 'undo' },
  { key: 'z', modifiers: ['ctrl', 'shift'], action: 'redo' },
  { key: '+', modifiers: ['ctrl'], action: 'zoomIn' },
  { key: '-', modifiers: ['ctrl'], action: 'zoomOut' },
  { key: '0', modifiers: ['ctrl'], action: 'zoomFit' },
  { key: 'ArrowLeft', modifiers: [], action: 'frameBack' },
  { key: 'ArrowRight', modifiers: [], action: 'frameForward' },
  { key: 'i', modifiers: [], action: 'setInPoint' },
  { key: 'o', modifiers: [], action: 'setOutPoint' },
]

// Initial state
const initialState = {
  selectedTool: 'select' as const,
  previewSettings: { ...defaultPreviewSettings },
  workspace: { ...defaultWorkspace },
  shortcuts: [...defaultShortcuts],
  isPlaying: false,
  playbackRate: 1,
  volume: 0.8,
}

// Create the vanilla store with devtools and immer middleware
export const createEditorStore = () => {
  return createStore<EditorStore>()(
    devtools(
      immer((set) => ({
      ...initialState,

      // Tool selection
      selectTool: (tool) =>
        set((state) => {
          state.selectedTool = tool
        }),

      // Preview settings
      setPreviewQuality: (quality) =>
        set((state) => {
          state.previewSettings.quality = quality

          // Auto-adjust resolution based on quality
          switch (quality) {
            case 'draft':
              state.previewSettings.resolution = { width: 640, height: 360 }
              break
            case 'half':
              state.previewSettings.resolution = { width: 960, height: 540 }
              break
            case 'full':
              state.previewSettings.resolution = { width: 1920, height: 1080 }
              break
          }
        }),

      setPreviewResolution: (resolution) =>
        set((state) => {
          state.previewSettings.resolution = resolution
        }),

      toggleFullscreen: () =>
        set((state) => {
          state.previewSettings.isFullscreen = !state.previewSettings.isFullscreen
        }),

      toggleSafeZones: () =>
        set((state) => {
          state.previewSettings.showSafeZones = !state.previewSettings.showSafeZones
        }),

      // Workspace layout
      updateWorkspace: (updates) =>
        set((state) => {
          state.workspace = {
            ...state.workspace,
            ...updates,
          }
        }),

      togglePanel: (panel) =>
        set((state) => {
          state.workspace[panel] = !state.workspace[panel]
        }),

      // Playback controls
      play: () =>
        set((state) => {
          state.isPlaying = true
        }),

      pause: () =>
        set((state) => {
          state.isPlaying = false
        }),

      togglePlayback: () =>
        set((state) => {
          state.isPlaying = !state.isPlaying
        }),

      setPlaybackRate: (rate) =>
        set((state) => {
          state.playbackRate = Math.max(0.25, Math.min(2, rate))
        }),

      setVolume: (volume) =>
        set((state) => {
          state.volume = Math.max(0, Math.min(1, volume))
        }),

      // Shortcuts
      registerShortcut: (shortcut) =>
        set((state) => {
          // Remove existing shortcut with same key combination
          const key = shortcut.key
          const modifiers = shortcut.modifiers.sort().join('+')
          state.shortcuts = state.shortcuts.filter((s) => {
            const existingModifiers = s.modifiers.sort().join('+')
            return !(s.key === key && existingModifiers === modifiers)
          })

          // Add new shortcut
          state.shortcuts.push(shortcut)
        }),

      removeShortcut: (key) =>
        set((state) => {
          state.shortcuts = state.shortcuts.filter((s) => s.key !== key)
        }),

      // Utility
      reset: () => set(initialState),
      })),
      { name: 'EditorStore' }
    )
  )
}

// Export type for the store instance
export type EditorStoreInstance = ReturnType<typeof createEditorStore>
