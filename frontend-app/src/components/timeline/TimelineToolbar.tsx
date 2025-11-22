import { useState } from 'react'
import { Scissors, Copy, Trash2, Save, Download, Settings as SettingsIcon, Menu } from 'lucide-react'
import { Button } from '../ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'
import { ZoomControls } from './ZoomControls'
import { SettingsDialog } from '../SettingsDialog'

interface TimelineToolbarProps {
  hasSelection: boolean
  zoom: number
  onZoomChange: (zoom: number) => void
  onSplitAtPlayhead: () => void
  onDuplicateClips: () => void
  onDeleteClips: () => void
  onSave?: () => void
  onExport?: () => void
}

export function TimelineToolbar({
  hasSelection,
  zoom,
  onZoomChange,
  onSplitAtPlayhead,
  onDuplicateClips,
  onDeleteClips,
  onSave,
  onExport,
}: TimelineToolbarProps) {
  const [settingsOpen, setSettingsOpen] = useState(false)

  const handleSave = () => {
    if (onSave) {
      onSave()
    } else {
      console.log('Save project')
      // TODO: Implement save functionality
    }
  }

  const handleExport = () => {
    if (onExport) {
      onExport()
    } else {
      console.log('Export project')
      // TODO: Implement export functionality
    }
  }

  return (
    <div className="flex items-center justify-between gap-2 px-2 py-1 bg-zinc-900 border-b border-zinc-700">
      {/* Desktop: Full toolbar */}
      <div className="hidden md:flex items-center gap-1 flex-1">
        {/* Zoom Controls */}
        <ZoomControls zoom={zoom} onZoomChange={onZoomChange} />

        {/* Separator */}
        <div className="w-px h-6 bg-zinc-700 mx-2" />

        {/* Clip Actions */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={onSplitAtPlayhead}
                disabled={!hasSelection}
                className="h-8 px-2"
              >
                <Scissors className="w-4 h-4" />
                <span className="ml-1.5 text-xs">Split</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Split clip at playhead (S)</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={onDuplicateClips}
                disabled={!hasSelection}
                className="h-8 px-2"
              >
                <Copy className="w-4 h-4" />
                <span className="ml-1.5 text-xs">Duplicate</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Duplicate selected clips (Ctrl+D)</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={onDeleteClips}
                disabled={!hasSelection}
                className="h-8 px-2 text-red-400 hover:text-red-300 hover:bg-red-950/30"
              >
                <Trash2 className="w-4 h-4" />
                <span className="ml-1.5 text-xs">Delete</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Delete selected clips (Delete)</p>
            </TooltipContent>
          </Tooltip>

          {/* Separator */}
          <div className="w-px h-6 bg-zinc-700 mx-2" />

          {/* Project Actions */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSave}
                className="h-8 px-2"
              >
                <Save className="w-4 h-4" />
                <span className="ml-1.5 text-xs">Save</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Save project (Ctrl+S)</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleExport}
                className="h-8 px-2"
              >
                <Download className="w-4 h-4" />
                <span className="ml-1.5 text-xs">Export</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Export video (Ctrl+E)</p>
            </TooltipContent>
          </Tooltip>

          {/* Separator */}
          <div className="w-px h-6 bg-zinc-700 mx-2" />

          {/* Settings */}
          <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => setSettingsOpen(true)}
                >
                  <SettingsIcon className="w-4 h-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Editor settings</p>
              </TooltipContent>
            </Tooltip>
          </SettingsDialog>
        </TooltipProvider>
      </div>

      {/* Mobile: Dropdown menu */}
      <div className="flex md:hidden items-center gap-2 w-full">
        <ZoomControls zoom={zoom} onZoomChange={onZoomChange} />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 px-2 ml-auto">
              <Menu className="w-4 h-4" />
              <span className="ml-1.5 text-xs">Actions</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={onSplitAtPlayhead} disabled={!hasSelection}>
              <Scissors className="w-4 h-4 mr-2" />
              Split
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onDuplicateClips} disabled={!hasSelection}>
              <Copy className="w-4 h-4 mr-2" />
              Duplicate
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={onDeleteClips}
              disabled={!hasSelection}
              className="text-red-400 focus:text-red-300 focus:bg-red-950/30"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSave}>
              <Save className="w-4 h-4 mr-2" />
              Save
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setSettingsOpen(true)}>
              <SettingsIcon className="w-4 h-4 mr-2" />
              Settings
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Settings Dialog for mobile */}
        <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
      </div>
    </div>
  )
}
