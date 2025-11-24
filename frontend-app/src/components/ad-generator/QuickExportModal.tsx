import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Music } from 'lucide-react';

interface QuickExportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (audioUrl?: string) => void;
  isExporting: boolean;
}

export const QuickExportModal: React.FC<QuickExportModalProps> = ({
  open,
  onOpenChange,
  onConfirm,
  isExporting,
}) => {
  const [audioUrl, setAudioUrl] = useState('');

  const handleConfirm = () => {
    onConfirm(audioUrl.trim() || undefined);
    // Reset after confirm (or keep it? usually reset is better)
    // Actually, we should wait for export to start. 
    // But the modal usually closes or stays open with loading.
    // The parent controls 'open'.
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px] bg-zinc-950 border-zinc-800">
        <DialogHeader>
          <DialogTitle className="text-zinc-100">Quick Export Options</DialogTitle>
          <DialogDescription className="text-zinc-400">
            Customize your video export. You can optionally add an audio track.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="audio-url" className="text-zinc-200">Audio URL (Optional)</Label>
            <div className="relative">
              <Music className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
              <Input
                id="audio-url"
                placeholder="https://example.com/music.mp3"
                className="pl-9 bg-zinc-900 border-zinc-800 text-zinc-100 focus:ring-blue-500"
                value={audioUrl}
                onChange={(e) => setAudioUrl(e.target.value)}
              />
            </div>
            <p className="text-xs text-zinc-500">
              If provided, this audio will replace any existing audio. 
              It will be trimmed to match the video length.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isExporting}>
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={isExporting} className="bg-blue-600 hover:bg-blue-700">
            {isExporting ? 'Exporting...' : 'Export Video'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
