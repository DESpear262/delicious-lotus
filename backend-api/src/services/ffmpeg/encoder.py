"""
H.264 Encoding Configuration for FFmpeg.

This module provides utilities for configuring H.264 video encoding with
CRF-based quality control, presets, profiles, and optimization settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class H264Preset(str, Enum):
    """H.264 encoding presets (speed vs compression tradeoff)."""

    ULTRAFAST = "ultrafast"  # Fastest, largest files
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"  # Balanced (default)
    SLOW = "slow"
    SLOWER = "slower"
    VERYSLOW = "veryslow"  # Slowest, smallest files


class H264Profile(str, Enum):
    """H.264 encoding profiles."""

    BASELINE = "baseline"  # Maximum compatibility, limited features
    MAIN = "main"  # Good compatibility, B-frames allowed
    HIGH = "high"  # Best compression, all features (default)
    HIGH10 = "high10"  # 10-bit color
    HIGH422 = "high422"  # 4:2:2 chroma subsampling
    HIGH444 = "high444"  # 4:4:4 chroma subsampling


class H264Tune(str, Enum):
    """H.264 tuning options for specific content types."""

    FILM = "film"  # For high-quality film content
    ANIMATION = "animation"  # For animated content
    GRAIN = "grain"  # For grainy content (preserves grain)
    STILLIMAGE = "stillimage"  # For slideshow-like content
    FASTDECODE = "fastdecode"  # Optimize for fast decoding
    ZEROLATENCY = "zerolatency"  # For live streaming (no B-frames)


@dataclass
class H264EncoderSettings:
    """
    Configuration for H.264 video encoding.

    Attributes:
        crf: Constant Rate Factor (0-51, lower = better quality, 18-28 recommended)
        preset: Encoding preset (speed vs compression)
        profile: H.264 profile (compatibility vs features)
        tune: Tuning option for specific content types
        level: H.264 level (e.g., "4.0", "4.1")
        pixel_format: Pixel format (e.g., "yuv420p")
        keyframe_interval: GOP size in frames (0 = auto)
        b_frames: Number of B-frames (0-16, None = auto)
        ref_frames: Number of reference frames (1-16, None = auto)
        bitrate: Target bitrate in kbps (None = use CRF)
        max_bitrate: Maximum bitrate in kbps
        buffer_size: VBV buffer size in kbps
        two_pass: Enable two-pass encoding for better quality
    """

    crf: int = 21
    preset: H264Preset = H264Preset.MEDIUM
    profile: H264Profile = H264Profile.HIGH
    tune: H264Tune | None = None
    level: str | None = None
    pixel_format: str = "yuv420p"
    keyframe_interval: int = 0  # 0 = auto (typically 250 frames)
    b_frames: int | None = None  # None = auto
    ref_frames: int | None = None  # None = auto
    bitrate: int | None = None  # kbps
    max_bitrate: int | None = None  # kbps
    buffer_size: int | None = None  # kbps
    two_pass: bool = False

    def __post_init__(self) -> None:
        """Validate settings."""
        # Validate CRF range
        if self.crf < 0 or self.crf > 51:
            raise ValueError(f"CRF must be between 0 and 51, got {self.crf}")

        # If using bitrate, CRF should not be used
        if self.bitrate is not None and self.crf != 21:
            # Allow CRF to be set to default (21) when bitrate is specified
            pass


class H264EncoderBuilder:
    """
    Builder for H.264 encoding parameters.

    Provides utilities for generating FFmpeg arguments for H.264 encoding
    with various quality and optimization settings.

    Example:
        >>> builder = H264EncoderBuilder()
        >>> settings = H264EncoderSettings(crf=23, preset=H264Preset.SLOW)
        >>> args = builder.build_encoder_args(settings)
        >>> # args = ['-c:v', 'libx264', '-crf', '23', '-preset', 'slow', ...]
    """

    def __init__(self) -> None:
        """Initialize the encoder builder."""
        pass

    def build_encoder_args(
        self,
        settings: H264EncoderSettings,
        include_codec: bool = True,
    ) -> list[str]:
        """
        Build FFmpeg arguments for H.264 encoding.

        Args:
            settings: Encoder settings configuration
            include_codec: Whether to include "-c:v libx264" (default: True)

        Returns:
            List of FFmpeg arguments

        Example:
            >>> settings = H264EncoderSettings(crf=21, preset=H264Preset.MEDIUM)
            >>> args = builder.build_encoder_args(settings)
            >>> # ['-c:v', 'libx264', '-crf', '21', '-preset', 'medium', ...]
        """
        args: list[str] = []

        # Video codec
        if include_codec:
            args.extend(["-c:v", "libx264"])

        # Quality/bitrate settings
        if settings.bitrate is not None:
            # Bitrate mode
            args.extend(["-b:v", f"{settings.bitrate}k"])

            if settings.max_bitrate is not None:
                args.extend(["-maxrate", f"{settings.max_bitrate}k"])

            if settings.buffer_size is not None:
                args.extend(["-bufsize", f"{settings.buffer_size}k"])
        else:
            # CRF mode (constant quality)
            args.extend(["-crf", str(settings.crf)])

        # Preset
        args.extend(["-preset", settings.preset.value])

        # Profile
        args.extend(["-profile:v", settings.profile.value])

        # Tune (optional)
        if settings.tune is not None:
            args.extend(["-tune", settings.tune.value])

        # Level (optional)
        if settings.level is not None:
            args.extend(["-level", settings.level])

        # Pixel format
        args.extend(["-pix_fmt", settings.pixel_format])

        # GOP size (keyframe interval)
        if settings.keyframe_interval > 0:
            args.extend(["-g", str(settings.keyframe_interval)])

        # B-frames
        if settings.b_frames is not None:
            args.extend(["-bf", str(settings.b_frames)])

        # Reference frames
        if settings.ref_frames is not None:
            args.extend(["-refs", str(settings.ref_frames)])

        # Additional x264 options for optimization
        x264_params: list[str] = []

        # Fast start for web playback (move moov atom to beginning)
        # This is typically added as a global option, not x264-params

        if x264_params:
            args.extend(["-x264-params", ":".join(x264_params)])

        return args

    def calculate_bitrate_from_quality(
        self,
        width: int,
        height: int,
        fps: float = 30.0,
        quality: str = "medium",
    ) -> int:
        """
        Calculate target bitrate based on resolution and quality level.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            fps: Frame rate
            quality: Quality level ("low", "medium", "high", "ultra")

        Returns:
            Recommended bitrate in kbps

        Example:
            >>> builder.calculate_bitrate_from_quality(1920, 1080, 30.0, "high")
            8000  # 8 Mbps
        """
        # Base bitrate per megapixel
        megapixels = (width * height) / 1_000_000

        # Bitrate multipliers for quality levels
        multipliers = {
            "low": 1000,  # 1 Mbps per MP
            "medium": 2000,  # 2 Mbps per MP
            "high": 4000,  # 4 Mbps per MP
            "ultra": 8000,  # 8 Mbps per MP
        }

        base_bitrate = megapixels * multipliers.get(quality, 2000)

        # Adjust for frame rate (30fps is baseline)
        fps_multiplier = fps / 30.0
        bitrate = int(base_bitrate * fps_multiplier)

        return bitrate

    def create_web_optimized_settings(
        self,
        quality_level: int = 23,
        fast_start: bool = True,
    ) -> H264EncoderSettings:
        """
        Create settings optimized for web playback.

        Args:
            quality_level: CRF value (18-28, lower = better quality)
            fast_start: Enable fast start (movflags +faststart)

        Returns:
            H264EncoderSettings configured for web

        Example:
            >>> settings = builder.create_web_optimized_settings(quality_level=23)
        """
        return H264EncoderSettings(
            crf=quality_level,
            preset=H264Preset.MEDIUM,
            profile=H264Profile.HIGH,
            level="4.0",  # Widely supported
            pixel_format="yuv420p",  # Maximum compatibility
            keyframe_interval=60,  # Keyframe every 2 seconds at 30fps
            b_frames=2,  # Good compression with moderate complexity
        )

    def create_streaming_settings(
        self,
        bitrate: int,
        buffer_seconds: float = 2.0,
    ) -> H264EncoderSettings:
        """
        Create settings optimized for live streaming.

        Args:
            bitrate: Target bitrate in kbps
            buffer_seconds: Buffer size in seconds

        Returns:
            H264EncoderSettings configured for streaming

        Example:
            >>> settings = builder.create_streaming_settings(bitrate=2500)
        """
        max_bitrate = int(bitrate * 1.2)  # 20% headroom
        buffer_size = int(bitrate * buffer_seconds)

        return H264EncoderSettings(
            bitrate=bitrate,
            max_bitrate=max_bitrate,
            buffer_size=buffer_size,
            preset=H264Preset.VERYFAST,  # Speed important for live
            profile=H264Profile.MAIN,
            tune=H264Tune.ZEROLATENCY,  # No B-frames for low latency
            keyframe_interval=60,  # Frequent keyframes for seeking
            b_frames=0,  # No B-frames in zero latency mode
        )

    def create_archive_settings(
        self,
        quality_level: int = 18,
    ) -> H264EncoderSettings:
        """
        Create settings optimized for archival (best quality).

        Args:
            quality_level: CRF value (16-20 recommended for archival)

        Returns:
            H264EncoderSettings configured for archival

        Example:
            >>> settings = builder.create_archive_settings(quality_level=18)
        """
        return H264EncoderSettings(
            crf=quality_level,
            preset=H264Preset.SLOWER,  # Better compression
            profile=H264Profile.HIGH,
            pixel_format="yuv420p",
            ref_frames=5,  # More reference frames for better compression
            b_frames=3,  # More B-frames
        )


@dataclass
class AudioEncoderSettings:
    """
    Configuration for audio encoding (AAC).

    Attributes:
        codec: Audio codec (e.g., "aac", "mp3", "copy")
        bitrate: Audio bitrate in kbps
        sample_rate: Sample rate in Hz (e.g., 44100, 48000)
        channels: Number of audio channels (1=mono, 2=stereo)
    """

    codec: str = "aac"
    bitrate: int = 128  # kbps
    sample_rate: int = 48000  # Hz
    channels: int = 2  # Stereo

    def to_ffmpeg_args(self) -> list[str]:
        """Convert to FFmpeg arguments."""
        args: list[str] = []

        args.extend(["-c:a", self.codec])

        if self.codec != "copy":
            args.extend(["-b:a", f"{self.bitrate}k"])
            args.extend(["-ar", str(self.sample_rate)])
            args.extend(["-ac", str(self.channels)])

        return args
