"""
Tests for H.264 Encoder module.

Tests H.264 encoding configuration, FFmpeg argument generation,
preset/profile/tune options, and optimization settings.
"""

from __future__ import annotations

import pytest
from services.ffmpeg.encoder import (
    AudioEncoderSettings,
    H264EncoderBuilder,
    H264EncoderSettings,
    H264Preset,
    H264Profile,
    H264Tune,
)


class TestH264EncoderSettings:
    """Tests for H264EncoderSettings configuration."""

    def test_default_settings(self):
        """Test default encoder settings."""
        settings = H264EncoderSettings()

        assert settings.crf == 21
        assert settings.preset == H264Preset.MEDIUM
        assert settings.profile == H264Profile.HIGH
        assert settings.tune is None
        assert settings.pixel_format == "yuv420p"
        assert settings.keyframe_interval == 0
        assert settings.two_pass is False

    def test_custom_settings(self):
        """Test creating custom encoder settings."""
        settings = H264EncoderSettings(
            crf=23,
            preset=H264Preset.SLOW,
            profile=H264Profile.MAIN,
            tune=H264Tune.FILM,
            keyframe_interval=60,
            two_pass=True,
        )

        assert settings.crf == 23
        assert settings.preset == H264Preset.SLOW
        assert settings.profile == H264Profile.MAIN
        assert settings.tune == H264Tune.FILM
        assert settings.keyframe_interval == 60
        assert settings.two_pass is True

    def test_crf_validation_too_low(self):
        """Test CRF validation rejects values below 0."""
        with pytest.raises(ValueError, match="CRF must be between 0 and 51"):
            H264EncoderSettings(crf=-1)

    def test_crf_validation_too_high(self):
        """Test CRF validation rejects values above 51."""
        with pytest.raises(ValueError, match="CRF must be between 0 and 51"):
            H264EncoderSettings(crf=52)

    def test_crf_validation_boundary_values(self):
        """Test CRF validation accepts boundary values."""
        # Should not raise
        settings_min = H264EncoderSettings(crf=0)
        settings_max = H264EncoderSettings(crf=51)

        assert settings_min.crf == 0
        assert settings_max.crf == 51

    def test_bitrate_mode_settings(self):
        """Test settings with bitrate mode instead of CRF."""
        settings = H264EncoderSettings(
            bitrate=5000,
            max_bitrate=6000,
            buffer_size=10000,
        )

        assert settings.bitrate == 5000
        assert settings.max_bitrate == 6000
        assert settings.buffer_size == 10000

    def test_b_frames_and_ref_frames(self):
        """Test B-frame and reference frame settings."""
        settings = H264EncoderSettings(
            b_frames=3,
            ref_frames=5,
        )

        assert settings.b_frames == 3
        assert settings.ref_frames == 5


class TestH264EncoderBuilder:
    """Tests for H264EncoderBuilder."""

    @pytest.fixture
    def builder(self) -> H264EncoderBuilder:
        """Create encoder builder instance."""
        return H264EncoderBuilder()

    def test_build_encoder_args_default(self, builder):
        """Test building encoder args with default settings."""
        settings = H264EncoderSettings()
        args = builder.build_encoder_args(settings)

        assert "-c:v" in args
        assert "libx264" in args
        assert "-crf" in args
        assert "21" in args
        assert "-preset" in args
        assert "medium" in args
        assert "-profile:v" in args
        assert "high" in args
        assert "-pix_fmt" in args
        assert "yuv420p" in args

    def test_build_encoder_args_without_codec(self, builder):
        """Test building encoder args without codec specification."""
        settings = H264EncoderSettings()
        args = builder.build_encoder_args(settings, include_codec=False)

        assert "-c:v" not in args
        assert "libx264" not in args
        assert "-crf" in args  # Should still have other params

    def test_build_encoder_args_with_crf(self, builder):
        """Test CRF mode encoding arguments."""
        settings = H264EncoderSettings(crf=23)
        args = builder.build_encoder_args(settings)

        assert "-crf" in args
        assert "23" in args
        assert "-b:v" not in args  # No bitrate in CRF mode

    def test_build_encoder_args_with_bitrate(self, builder):
        """Test bitrate mode encoding arguments."""
        settings = H264EncoderSettings(
            bitrate=5000,
            max_bitrate=6000,
            buffer_size=10000,
        )
        args = builder.build_encoder_args(settings)

        assert "-b:v" in args
        assert "5000k" in args
        assert "-maxrate" in args
        assert "6000k" in args
        assert "-bufsize" in args
        assert "10000k" in args
        assert "-crf" not in args  # No CRF in bitrate mode

    def test_build_encoder_args_with_preset(self, builder):
        """Test preset encoding arguments."""
        settings = H264EncoderSettings(preset=H264Preset.SLOW)
        args = builder.build_encoder_args(settings)

        assert "-preset" in args
        assert "slow" in args

    def test_build_encoder_args_with_profile(self, builder):
        """Test profile encoding arguments."""
        settings = H264EncoderSettings(profile=H264Profile.BASELINE)
        args = builder.build_encoder_args(settings)

        assert "-profile:v" in args
        assert "baseline" in args

    def test_build_encoder_args_with_tune(self, builder):
        """Test tune encoding arguments."""
        settings = H264EncoderSettings(tune=H264Tune.FILM)
        args = builder.build_encoder_args(settings)

        assert "-tune" in args
        assert "film" in args

    def test_build_encoder_args_without_tune(self, builder):
        """Test encoding arguments without tune option."""
        settings = H264EncoderSettings(tune=None)
        args = builder.build_encoder_args(settings)

        assert "-tune" not in args

    def test_build_encoder_args_with_level(self, builder):
        """Test level encoding arguments."""
        settings = H264EncoderSettings(level="4.1")
        args = builder.build_encoder_args(settings)

        assert "-level" in args
        assert "4.1" in args

    def test_build_encoder_args_with_keyframe_interval(self, builder):
        """Test keyframe interval encoding arguments."""
        settings = H264EncoderSettings(keyframe_interval=60)
        args = builder.build_encoder_args(settings)

        assert "-g" in args
        assert "60" in args

    def test_build_encoder_args_without_keyframe_interval(self, builder):
        """Test encoding arguments with auto keyframe interval."""
        settings = H264EncoderSettings(keyframe_interval=0)
        args = builder.build_encoder_args(settings)

        assert "-g" not in args  # 0 means auto

    def test_build_encoder_args_with_b_frames(self, builder):
        """Test B-frame encoding arguments."""
        settings = H264EncoderSettings(b_frames=3)
        args = builder.build_encoder_args(settings)

        assert "-bf" in args
        assert "3" in args

    def test_build_encoder_args_with_ref_frames(self, builder):
        """Test reference frame encoding arguments."""
        settings = H264EncoderSettings(ref_frames=5)
        args = builder.build_encoder_args(settings)

        assert "-refs" in args
        assert "5" in args

    def test_build_encoder_args_all_options(self, builder):
        """Test encoding arguments with all options enabled."""
        settings = H264EncoderSettings(
            crf=23,
            preset=H264Preset.SLOW,
            profile=H264Profile.HIGH,
            tune=H264Tune.FILM,
            level="4.1",
            pixel_format="yuv420p",
            keyframe_interval=60,
            b_frames=3,
            ref_frames=5,
        )
        args = builder.build_encoder_args(settings)

        # Verify all options present
        assert "-c:v" in args
        assert "libx264" in args
        assert "-crf" in args
        assert "23" in args
        assert "-preset" in args
        assert "slow" in args
        assert "-profile:v" in args
        assert "high" in args
        assert "-tune" in args
        assert "film" in args
        assert "-level" in args
        assert "4.1" in args
        assert "-pix_fmt" in args
        assert "yuv420p" in args
        assert "-g" in args
        assert "60" in args
        assert "-bf" in args
        assert "3" in args
        assert "-refs" in args
        assert "5" in args

    def test_calculate_bitrate_from_quality_720p(self, builder):
        """Test bitrate calculation for 720p video."""
        # 1280x720 = 0.92 megapixels
        bitrate = builder.calculate_bitrate_from_quality(1280, 720, 30.0, "medium")

        # Should be around 0.92 * 2000 = 1840 kbps
        assert 1700 < bitrate < 2000

    def test_calculate_bitrate_from_quality_1080p(self, builder):
        """Test bitrate calculation for 1080p video."""
        # 1920x1080 = 2.07 megapixels
        bitrate = builder.calculate_bitrate_from_quality(1920, 1080, 30.0, "medium")

        # Should be around 2.07 * 2000 = 4140 kbps
        assert 4000 < bitrate < 4500

    def test_calculate_bitrate_from_quality_low(self, builder):
        """Test bitrate calculation with low quality."""
        bitrate = builder.calculate_bitrate_from_quality(1280, 720, 30.0, "low")

        # Should be around 0.92 * 1000 = 920 kbps
        assert 800 < bitrate < 1100

    def test_calculate_bitrate_from_quality_high(self, builder):
        """Test bitrate calculation with high quality."""
        bitrate = builder.calculate_bitrate_from_quality(1280, 720, 30.0, "high")

        # Should be around 0.92 * 4000 = 3680 kbps
        assert 3500 < bitrate < 4000

    def test_calculate_bitrate_from_quality_ultra(self, builder):
        """Test bitrate calculation with ultra quality."""
        bitrate = builder.calculate_bitrate_from_quality(1280, 720, 30.0, "ultra")

        # Should be around 0.92 * 8000 = 7360 kbps
        assert 7000 < bitrate < 8000

    def test_calculate_bitrate_from_quality_60fps(self, builder):
        """Test bitrate calculation with 60fps."""
        bitrate_30fps = builder.calculate_bitrate_from_quality(1280, 720, 30.0, "medium")
        bitrate_60fps = builder.calculate_bitrate_from_quality(1280, 720, 60.0, "medium")

        # 60fps should be roughly 2x 30fps bitrate
        assert bitrate_60fps > bitrate_30fps * 1.8
        assert bitrate_60fps < bitrate_30fps * 2.2

    def test_create_web_optimized_settings(self, builder):
        """Test creating web-optimized settings."""
        settings = builder.create_web_optimized_settings(quality_level=23)

        assert settings.crf == 23
        assert settings.preset == H264Preset.MEDIUM
        assert settings.profile == H264Profile.HIGH
        assert settings.level == "4.0"
        assert settings.pixel_format == "yuv420p"
        assert settings.keyframe_interval == 60
        assert settings.b_frames == 2

    def test_create_web_optimized_settings_custom_quality(self, builder):
        """Test web-optimized settings with custom quality."""
        settings = builder.create_web_optimized_settings(quality_level=18)

        assert settings.crf == 18

    def test_create_streaming_settings(self, builder):
        """Test creating streaming-optimized settings."""
        settings = builder.create_streaming_settings(bitrate=2500)

        assert settings.bitrate == 2500
        assert settings.max_bitrate == 3000  # 20% headroom
        assert settings.buffer_size == 5000  # 2 seconds default
        assert settings.preset == H264Preset.VERYFAST
        assert settings.profile == H264Profile.MAIN
        assert settings.tune == H264Tune.ZEROLATENCY
        assert settings.keyframe_interval == 60
        assert settings.b_frames == 0  # No B-frames for low latency

    def test_create_streaming_settings_custom_buffer(self, builder):
        """Test streaming settings with custom buffer size."""
        settings = builder.create_streaming_settings(bitrate=2500, buffer_seconds=3.0)

        assert settings.buffer_size == 7500  # 2500 * 3

    def test_create_archive_settings(self, builder):
        """Test creating archive-optimized settings."""
        settings = builder.create_archive_settings(quality_level=18)

        assert settings.crf == 18
        assert settings.preset == H264Preset.SLOWER
        assert settings.profile == H264Profile.HIGH
        assert settings.pixel_format == "yuv420p"
        assert settings.ref_frames == 5
        assert settings.b_frames == 3

    def test_create_archive_settings_custom_quality(self, builder):
        """Test archive settings with custom quality."""
        settings = builder.create_archive_settings(quality_level=16)

        assert settings.crf == 16


class TestAudioEncoderSettings:
    """Tests for AudioEncoderSettings."""

    def test_default_settings(self):
        """Test default audio encoder settings."""
        settings = AudioEncoderSettings()

        assert settings.codec == "aac"
        assert settings.bitrate == 128
        assert settings.sample_rate == 48000
        assert settings.channels == 2

    def test_custom_settings(self):
        """Test custom audio encoder settings."""
        settings = AudioEncoderSettings(
            codec="mp3",
            bitrate=192,
            sample_rate=44100,
            channels=1,
        )

        assert settings.codec == "mp3"
        assert settings.bitrate == 192
        assert settings.sample_rate == 44100
        assert settings.channels == 1

    def test_to_ffmpeg_args_default(self):
        """Test converting to FFmpeg args with default settings."""
        settings = AudioEncoderSettings()
        args = settings.to_ffmpeg_args()

        assert "-c:a" in args
        assert "aac" in args
        assert "-b:a" in args
        assert "128k" in args
        assert "-ar" in args
        assert "48000" in args
        assert "-ac" in args
        assert "2" in args

    def test_to_ffmpeg_args_custom(self):
        """Test converting to FFmpeg args with custom settings."""
        settings = AudioEncoderSettings(
            codec="mp3",
            bitrate=192,
            sample_rate=44100,
            channels=1,
        )
        args = settings.to_ffmpeg_args()

        assert "-c:a" in args
        assert "mp3" in args
        assert "-b:a" in args
        assert "192k" in args
        assert "-ar" in args
        assert "44100" in args
        assert "-ac" in args
        assert "1" in args

    def test_to_ffmpeg_args_copy_codec(self):
        """Test FFmpeg args with copy codec (no re-encoding)."""
        settings = AudioEncoderSettings(codec="copy")
        args = settings.to_ffmpeg_args()

        assert "-c:a" in args
        assert "copy" in args
        # Should not have bitrate, sample rate, or channels with copy
        assert "-b:a" not in args
        assert "-ar" not in args
        assert "-ac" not in args


class TestH264Presets:
    """Tests for H264Preset enum values."""

    def test_preset_values(self):
        """Test all preset enum values."""
        assert H264Preset.ULTRAFAST.value == "ultrafast"
        assert H264Preset.SUPERFAST.value == "superfast"
        assert H264Preset.VERYFAST.value == "veryfast"
        assert H264Preset.FASTER.value == "faster"
        assert H264Preset.FAST.value == "fast"
        assert H264Preset.MEDIUM.value == "medium"
        assert H264Preset.SLOW.value == "slow"
        assert H264Preset.SLOWER.value == "slower"
        assert H264Preset.VERYSLOW.value == "veryslow"


class TestH264Profiles:
    """Tests for H264Profile enum values."""

    def test_profile_values(self):
        """Test all profile enum values."""
        assert H264Profile.BASELINE.value == "baseline"
        assert H264Profile.MAIN.value == "main"
        assert H264Profile.HIGH.value == "high"
        assert H264Profile.HIGH10.value == "high10"
        assert H264Profile.HIGH422.value == "high422"
        assert H264Profile.HIGH444.value == "high444"


class TestH264Tunes:
    """Tests for H264Tune enum values."""

    def test_tune_values(self):
        """Test all tune enum values."""
        assert H264Tune.FILM.value == "film"
        assert H264Tune.ANIMATION.value == "animation"
        assert H264Tune.GRAIN.value == "grain"
        assert H264Tune.STILLIMAGE.value == "stillimage"
        assert H264Tune.FASTDECODE.value == "fastdecode"
        assert H264Tune.ZEROLATENCY.value == "zerolatency"


class TestIntegrationScenarios:
    """Integration tests for real-world encoding scenarios."""

    @pytest.fixture
    def builder(self) -> H264EncoderBuilder:
        """Create encoder builder instance."""
        return H264EncoderBuilder()

    def test_youtube_upload_workflow(self, builder):
        """Test encoding settings for YouTube upload."""
        # YouTube recommends high bitrate for 720p
        settings = H264EncoderSettings(
            crf=21,
            preset=H264Preset.SLOW,  # Better quality
            profile=H264Profile.HIGH,
            keyframe_interval=60,  # 2 second keyframes at 30fps
        )

        args = builder.build_encoder_args(settings)

        assert "-crf" in args
        assert "21" in args
        assert "-preset" in args
        assert "slow" in args
        assert "-g" in args
        assert "60" in args

    def test_web_video_player_workflow(self, builder):
        """Test encoding settings for web video player."""
        settings = builder.create_web_optimized_settings(quality_level=23)
        args = builder.build_encoder_args(settings)

        assert "-crf" in args
        assert "23" in args
        assert "-profile:v" in args
        assert "high" in args
        assert "-level" in args
        assert "4.0" in args

    def test_live_stream_workflow(self, builder):
        """Test encoding settings for live streaming."""
        # Calculate appropriate bitrate for 720p
        bitrate = builder.calculate_bitrate_from_quality(1280, 720, 30.0, "medium")

        settings = builder.create_streaming_settings(bitrate=bitrate)
        args = builder.build_encoder_args(settings)

        assert "-b:v" in args
        assert "-maxrate" in args
        assert "-bufsize" in args
        assert "-tune" in args
        assert "zerolatency" in args

    def test_archive_storage_workflow(self, builder):
        """Test encoding settings for archival storage."""
        settings = builder.create_archive_settings(quality_level=18)
        args = builder.build_encoder_args(settings)

        assert "-crf" in args
        assert "18" in args
        assert "-preset" in args
        assert "slower" in args
        assert "-refs" in args
        assert "5" in args

    def test_fast_preview_workflow(self, builder):
        """Test encoding settings for fast preview generation."""
        settings = H264EncoderSettings(
            crf=28,  # Lower quality for speed
            preset=H264Preset.ULTRAFAST,
            profile=H264Profile.BASELINE,
        )

        args = builder.build_encoder_args(settings)

        assert "-crf" in args
        assert "28" in args
        assert "-preset" in args
        assert "ultrafast" in args
        assert "-profile:v" in args
        assert "baseline" in args

    def test_mobile_device_playback_workflow(self, builder):
        """Test encoding settings optimized for mobile playback."""
        settings = H264EncoderSettings(
            crf=23,
            preset=H264Preset.FAST,
            profile=H264Profile.MAIN,  # Better compatibility
            level="3.1",  # Mobile devices support 3.1
            keyframe_interval=30,  # More frequent keyframes
        )

        args = builder.build_encoder_args(settings)

        assert "-profile:v" in args
        assert "main" in args
        assert "-level" in args
        assert "3.1" in args

    def test_broadcast_workflow(self, builder):
        """Test encoding settings for broadcast quality."""
        bitrate = builder.calculate_bitrate_from_quality(1280, 720, 30.0, "high")

        settings = H264EncoderSettings(
            bitrate=bitrate,
            max_bitrate=int(bitrate * 1.5),
            preset=H264Preset.SLOW,
            profile=H264Profile.HIGH,
            b_frames=3,
        )

        args = builder.build_encoder_args(settings)

        assert "-b:v" in args
        assert "-maxrate" in args
        assert "-bf" in args
        assert "3" in args

    def test_complete_video_with_audio_workflow(self, builder):
        """Test complete encoding with both video and audio."""
        video_settings = builder.create_web_optimized_settings(quality_level=21)
        audio_settings = AudioEncoderSettings(
            codec="aac",
            bitrate=128,
            sample_rate=48000,
        )

        video_args = builder.build_encoder_args(video_settings)
        audio_args = audio_settings.to_ffmpeg_args()

        # Combine all args
        all_args = video_args + audio_args

        # Verify both video and audio present
        assert "-c:v" in all_args
        assert "libx264" in all_args
        assert "-c:a" in all_args
        assert "aac" in all_args
