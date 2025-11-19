import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog'
import { Button } from './ui/button'
import { Label } from './ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'

interface SettingsDialogProps {
  children?: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

/**
 * Settings dialog for video editor configuration
 */
export function SettingsDialog({ children, open, onOpenChange }: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {children && <DialogTrigger asChild>{children}</DialogTrigger>}
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Editor Settings</DialogTitle>
          <DialogDescription>
            Configure your video editor preferences
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          {/* Timeline Settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-100">Timeline</h3>

            <div className="grid gap-2">
              <Label htmlFor="fps">Frame Rate (FPS)</Label>
              <Select defaultValue="30">
                <SelectTrigger id="fps">
                  <SelectValue placeholder="Select FPS" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24">24 FPS</SelectItem>
                  <SelectItem value="30">30 FPS</SelectItem>
                  <SelectItem value="60">60 FPS</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="snap">Snap to Grid</Label>
              <Select defaultValue="on">
                <SelectTrigger id="snap">
                  <SelectValue placeholder="Select option" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="on">Enabled</SelectItem>
                  <SelectItem value="off">Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Playback Settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-100">Playback</h3>

            <div className="grid gap-2">
              <Label htmlFor="quality">Preview Quality</Label>
              <Select defaultValue="auto">
                <SelectTrigger id="quality">
                  <SelectValue placeholder="Select quality" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto</SelectItem>
                  <SelectItem value="full">Full Quality</SelectItem>
                  <SelectItem value="half">Half Quality</SelectItem>
                  <SelectItem value="quarter">Quarter Quality</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Export Settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-100">Export</h3>

            <div className="grid gap-2">
              <Label htmlFor="format">Default Format</Label>
              <Select defaultValue="mp4">
                <SelectTrigger id="format">
                  <SelectValue placeholder="Select format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mp4">MP4</SelectItem>
                  <SelectItem value="mov">MOV</SelectItem>
                  <SelectItem value="webm">WebM</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange?.(false)}
          >
            Cancel
          </Button>
          <Button onClick={() => onOpenChange?.(false)}>
            Save Changes
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
