"""FFmpeg service package for command building and video processing."""

from services.ffmpeg.audio_mixer import AudioMixerBuilder, AudioTrack
from services.ffmpeg.command_builder import FFmpegCommandBuilder, InputFile, OutputFile
from services.ffmpeg.concat_builder import ConcatDemuxerBuilder, ConcatSegment
from services.ffmpeg.encoder import (
    AudioEncoderSettings,
    H264EncoderBuilder,
    H264EncoderSettings,
    H264Preset,
    H264Profile,
    H264Tune,
)
from services.ffmpeg.filter_builder import (
    Clip,
    FilterComplexBuilder,
    Transition,
    TransitionType,
)
from services.ffmpeg.input_manager import InputFileManager, MediaFileInfo, StreamInfo
from services.ffmpeg.security import FFmpegCommandValidator, FFmpegSecurityError
from services.ffmpeg.text_overlay import (
    TextAnimation,
    TextOverlayBuilder,
    TextPosition,
    TextStyle,
)
from services.ffmpeg.validator import FilterChainValidator, ValidationResult

__all__ = [
    # Core command builder
    "FFmpegCommandBuilder",
    "InputFile",
    "OutputFile",
    # Input management
    "InputFileManager",
    "MediaFileInfo",
    "StreamInfo",
    # Filter builder
    "FilterComplexBuilder",
    "Clip",
    "Transition",
    "TransitionType",
    # Text overlay
    "TextOverlayBuilder",
    "TextPosition",
    "TextStyle",
    "TextAnimation",
    # Audio mixer
    "AudioMixerBuilder",
    "AudioTrack",
    # Concat builder
    "ConcatDemuxerBuilder",
    "ConcatSegment",
    # Encoder
    "H264EncoderBuilder",
    "H264EncoderSettings",
    "AudioEncoderSettings",
    "H264Preset",
    "H264Profile",
    "H264Tune",
    # Security
    "FFmpegCommandValidator",
    "FFmpegSecurityError",
    # Validator
    "FilterChainValidator",
    "ValidationResult",
]
