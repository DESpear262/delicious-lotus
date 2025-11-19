import { useRef } from 'react';
import { useVideoPlayer } from '../../../hooks/ad-generator/useVideoPlayer';
import { VideoControls } from './VideoControls';
import { downloadVideo } from '../../../utils/ad-generator/video';
import { Spinner } from '../ui/Spinner';
import { Button } from '../ui/Button';
import styles from './VideoPlayer.module.css';

export interface VideoPlayerProps {
  src: string;                    // Video URL
  poster?: string;                // Thumbnail/poster image
  title?: string;                 // Video title
  autoPlay?: boolean;             // Auto-play on mount
  muted?: boolean;                // Start muted
  loop?: boolean;                 // Loop playback
  className?: string;
  onEnded?: () => void;          // Callback when video ends
  onError?: (error: Error) => void;
  showDownload?: boolean;         // Show download button
  downloadFileName?: string;      // Custom download filename
}

export function VideoPlayer({
  src,
  poster,
  title,
  autoPlay = false,
  muted = false,
  loop = false,
  className = '',
  onEnded,
  onError,
  showDownload = true,
  downloadFileName,
}: VideoPlayerProps) {
  // Video element ref
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Player state from custom hook
  const {
    isPlaying,
    currentTime,
    duration,
    volume,
    isMuted,
    isFullscreen,
    playbackRate,
    buffered,
    isLoading,
    error,
    play,
    pause,
    seek,
    setVolume,
    toggleMute,
    toggleFullscreen,
    setPlaybackRate,
  } = useVideoPlayer(videoRef);

  const handleError = () => {
    const videoError = videoRef.current?.error;
    const errorMessage = videoError
      ? `Video error: ${videoError.message}`
      : 'Failed to load video';
    const err = new Error(errorMessage);

    if (onError) {
      onError(err);
    }
  };

  const handleDownload = async () => {
    try {
      await downloadVideo(src, downloadFileName || title || 'video.mp4');
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  return (
    <div className={`${styles.videoPlayer} ${className}`}>
      {/* Video element */}
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className={styles.videoPlayer__video}
        onEnded={onEnded}
        onError={handleError}
        autoPlay={autoPlay}
        muted={muted}
        loop={loop}
        preload="metadata"
      />

      {/* Loading overlay */}
      {isLoading && (
        <div className={styles.videoPlayer__loading}>
          <Spinner size="lg" variant="white" label="Loading video..." />
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div className={styles.videoPlayer__error}>
          <p className={styles.videoPlayer__errorMessage}>Failed to load video</p>
          <Button onClick={() => videoRef.current?.load()} variant="primary">
            Retry
          </Button>
        </div>
      )}

      {/* Custom controls */}
      <VideoControls
        isPlaying={isPlaying}
        currentTime={currentTime}
        duration={duration}
        volume={volume}
        isMuted={isMuted}
        isFullscreen={isFullscreen}
        playbackRate={playbackRate}
        buffered={buffered}
        onPlayPause={() => (isPlaying ? pause() : play())}
        onSeek={seek}
        onVolumeChange={setVolume}
        onToggleMute={toggleMute}
        onToggleFullscreen={toggleFullscreen}
        onPlaybackRateChange={setPlaybackRate}
        showDownload={showDownload}
        onDownload={handleDownload}
      />
    </div>
  );
}
