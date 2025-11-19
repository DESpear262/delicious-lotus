"""
Unit tests for Audio Mixer Builder.

Tests the AudioMixerBuilder class with various audio mixing scenarios.
"""

import pytest
from services.ffmpeg.audio_mixer import AudioMixerBuilder, AudioMixMode, AudioTrack


class TestAudioTrack:
    """Test cases for AudioTrack dataclass."""

    def test_default_track(self):
        """Test default audio track configuration."""
        track = AudioTrack(input_index=0)

        assert track.input_index == 0
        assert track.volume == 1.0
        assert track.start_time == 0.0
        assert track.end_time is None
        assert track.fade_in == 0.0
        assert track.fade_out == 0.0

    def test_custom_track(self):
        """Test custom audio track configuration."""
        track = AudioTrack(
            input_index=2,
            volume=0.5,
            start_time=5.0,
            end_time=15.0,
            fade_in=1.0,
            fade_out=2.0,
        )

        assert track.input_index == 2
        assert track.volume == 0.5
        assert track.start_time == 5.0
        assert track.end_time == 15.0
        assert track.fade_in == 1.0
        assert track.fade_out == 2.0

    def test_track_repr(self):
        """Test string representation."""
        track = AudioTrack(input_index=0, volume=0.75, start_time=0.0, end_time=10.0)

        repr_str = repr(track)
        assert "AudioTrack[0]" in repr_str
        assert "0.75" in repr_str


class TestAudioMixMode:
    """Test cases for AudioMixMode enum."""

    def test_mix_modes_exist(self):
        """Test that expected mix modes are defined."""
        assert hasattr(AudioMixMode, "MERGE")
        assert hasattr(AudioMixMode, "MIX")

    def test_mix_mode_values(self):
        """Test mix mode enum values."""
        assert AudioMixMode.MERGE.value == "merge"
        assert AudioMixMode.MIX.value == "mix"


class TestAudioMixerBuilder:
    """Test cases for AudioMixerBuilder."""

    @pytest.fixture
    def builder(self):
        """Create an audio mixer builder."""
        return AudioMixerBuilder()

    def test_builder_initialization(self, builder):
        """Test builder initializes correctly."""
        assert builder is not None
        assert builder._label_counter == 0

    def test_generate_label(self, builder):
        """Test label generation."""
        label1 = builder._generate_label()
        label2 = builder._generate_label()
        label3 = builder._generate_label("custom")

        assert label1 == "a0"
        assert label2 == "a1"
        assert label3 == "custom2"

    def test_generate_label_increments(self, builder):
        """Test that label counter increments."""
        for i in range(5):
            label = builder._generate_label()
            assert label == f"a{i}"

    def test_build_volume_filter(self, builder):
        """Test building volume filter."""
        filter_expr = builder.build_volume_filter(input_index=0, volume=0.5)

        assert "[0:a]" in filter_expr
        assert "volume=0.5" in filter_expr
        assert "[a0]" in filter_expr

    def test_build_volume_filter_custom_label(self, builder):
        """Test volume filter with custom output label."""
        filter_expr = builder.build_volume_filter(input_index=1, volume=0.8, output_label="custom")

        assert "[1:a]" in filter_expr
        assert "volume=0.8" in filter_expr
        assert "[custom]" in filter_expr

    def test_build_volume_filter_clamps_values(self, builder):
        """Test volume filter clamps extreme values."""
        # Test negative volume (should clamp to 0)
        filter_low = builder.build_volume_filter(input_index=0, volume=-1.0)
        assert "volume=0.0" in filter_low

        # Test very high volume (should clamp to 2.0)
        filter_high = builder.build_volume_filter(input_index=0, volume=5.0)
        assert "volume=2.0" in filter_high

    def test_build_audio_fade_in_only(self, builder):
        """Test audio fade with only fade-in."""
        filter_expr = builder.build_audio_fade(input_index=0, fade_in=2.0)

        assert "[0:a]" in filter_expr
        assert "afade=t=in" in filter_expr
        assert "st=0" in filter_expr
        assert "d=2.0" in filter_expr

    def test_build_audio_fade_out_only(self, builder):
        """Test audio fade with only fade-out."""
        filter_expr = builder.build_audio_fade(input_index=0, fade_out=3.0, duration=10.0)

        assert "[0:a]" in filter_expr
        assert "afade=t=out" in filter_expr
        assert "st=7.0" in filter_expr  # 10 - 3
        assert "d=3.0" in filter_expr

    def test_build_audio_fade_both(self, builder):
        """Test audio fade with both fade-in and fade-out."""
        filter_expr = builder.build_audio_fade(
            input_index=0, fade_in=1.0, fade_out=2.0, duration=10.0
        )

        assert "[0:a]" in filter_expr
        assert "afade=t=in" in filter_expr
        assert "afade=t=out" in filter_expr
        assert "," in filter_expr  # Both fades separated by comma

    def test_build_audio_fade_no_fades(self, builder):
        """Test audio fade with no fades (null filter)."""
        filter_expr = builder.build_audio_fade(input_index=0)

        assert "[0:a]" in filter_expr
        assert "anull" in filter_expr

    def test_build_audio_fade_custom_label(self, builder):
        """Test audio fade with custom output label."""
        filter_expr = builder.build_audio_fade(input_index=0, fade_in=1.0, output_label="custom")

        assert "[custom]" in filter_expr

    def test_mix_audio_tracks_single_track(self, builder):
        """Test mixing a single audio track."""
        tracks = [AudioTrack(input_index=0, volume=0.8)]

        filter_expr = builder.mix_audio_tracks(tracks)

        # Single track should just apply volume
        assert "[0:a]" in filter_expr
        assert "volume=0.8" in filter_expr

    def test_mix_audio_tracks_two_tracks(self, builder):
        """Test mixing two audio tracks."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),
            AudioTrack(input_index=1, volume=0.3),
        ]

        filter_expr = builder.mix_audio_tracks(tracks)

        # Should have volume filters for both tracks
        assert "volume=1.0" in filter_expr
        assert "volume=0.3" in filter_expr
        # Should have amix filter
        assert "amix" in filter_expr
        assert "inputs=2" in filter_expr
        assert "duration=longest" in filter_expr

    def test_mix_audio_tracks_multiple_tracks(self, builder):
        """Test mixing multiple audio tracks."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),
            AudioTrack(input_index=1, volume=0.5),
            AudioTrack(input_index=2, volume=0.3),
        ]

        filter_expr = builder.mix_audio_tracks(tracks)

        assert "inputs=3" in filter_expr
        assert filter_expr.count("volume=") == 3

    def test_mix_audio_tracks_with_normalize(self, builder):
        """Test mixing with normalization enabled."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),
            AudioTrack(input_index=1, volume=0.5),
        ]

        filter_expr = builder.mix_audio_tracks(tracks, normalize=True)

        assert "normalize=1" in filter_expr

    def test_mix_audio_tracks_without_normalize(self, builder):
        """Test mixing with normalization disabled."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),
            AudioTrack(input_index=1, volume=0.5),
        ]

        filter_expr = builder.mix_audio_tracks(tracks, normalize=False)

        assert "normalize=0" in filter_expr

    def test_mix_audio_tracks_merge_mode(self, builder):
        """Test mixing in merge mode."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),
            AudioTrack(input_index=1, volume=1.0),
        ]

        filter_expr = builder.mix_audio_tracks(tracks, mode=AudioMixMode.MERGE)

        # Should use amerge instead of amix
        assert "amerge" in filter_expr
        assert "inputs=2" in filter_expr

    def test_mix_audio_tracks_custom_output_label(self, builder):
        """Test mixing with custom output label."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),
            AudioTrack(input_index=1, volume=0.5),
        ]

        filter_expr = builder.mix_audio_tracks(tracks, output_label="custom")

        assert "[custom]" in filter_expr

    def test_mix_audio_tracks_empty_list(self, builder):
        """Test mixing with no tracks raises error."""
        with pytest.raises(ValueError, match="Need at least one audio track"):
            builder.mix_audio_tracks([])

    def test_build_audio_ducking(self, builder):
        """Test building audio ducking filter."""
        filter_expr = builder.build_audio_ducking(main_audio_index=0, voiceover_index=1)

        assert "[0:a][1:a]" in filter_expr
        assert "sidechaincompress" in filter_expr
        assert "threshold=" in filter_expr
        assert "ratio=" in filter_expr
        assert "attack=" in filter_expr
        assert "release=" in filter_expr

    def test_build_audio_ducking_custom_parameters(self, builder):
        """Test audio ducking with custom parameters."""
        filter_expr = builder.build_audio_ducking(
            main_audio_index=0,
            voiceover_index=1,
            duck_amount=0.5,
            attack_time=0.2,
            release_time=0.5,
            threshold=-15.0,
        )

        assert "threshold=-15.0" in filter_expr
        assert "attack=200" in filter_expr  # 0.2 * 1000
        assert "release=500" in filter_expr  # 0.5 * 1000

    def test_build_audio_ducking_custom_output_label(self, builder):
        """Test audio ducking with custom output label."""
        filter_expr = builder.build_audio_ducking(
            main_audio_index=0, voiceover_index=1, output_label="ducked"
        )

        assert "[ducked]" in filter_expr

    def test_build_audio_delay(self, builder):
        """Test building audio delay filter."""
        filter_expr = builder.build_audio_delay(input_index=0, delay_ms=500)

        assert "[0:a]" in filter_expr
        assert "adelay=500" in filter_expr

    def test_build_audio_delay_custom_label(self, builder):
        """Test audio delay with custom output label."""
        filter_expr = builder.build_audio_delay(
            input_index=0, delay_ms=1000, output_label="delayed"
        )

        assert "[delayed]" in filter_expr
        assert "adelay=1000" in filter_expr

    def test_build_audio_normalize(self, builder):
        """Test building loudness normalization filter."""
        filter_expr = builder.build_audio_normalize(input_index=0)

        assert "[0:a]" in filter_expr
        assert "loudnorm" in filter_expr
        assert "I=-23.0" in filter_expr  # Default target level
        assert "TP=-1.5" in filter_expr  # True peak
        assert "LRA=11" in filter_expr  # Loudness range

    def test_build_audio_normalize_custom_level(self, builder):
        """Test normalization with custom target level."""
        filter_expr = builder.build_audio_normalize(input_index=0, target_level=-16.0)

        assert "I=-16.0" in filter_expr

    def test_build_audio_normalize_custom_label(self, builder):
        """Test normalization with custom output label."""
        filter_expr = builder.build_audio_normalize(input_index=0, output_label="normalized")

        assert "[normalized]" in filter_expr

    def test_build_audio_crossfade(self, builder):
        """Test building audio crossfade filter."""
        filter_expr = builder.build_audio_crossfade(
            input1_index=0,
            input2_index=1,
            crossfade_duration=2.0,
            input1_duration=10.0,
        )

        assert "[0:a][1:a]" in filter_expr
        assert "acrossfade" in filter_expr
        assert "d=2.0" in filter_expr
        assert "c1=tri" in filter_expr  # Curve type
        assert "c2=tri" in filter_expr

    def test_build_audio_crossfade_custom_output(self, builder):
        """Test audio crossfade with custom output label."""
        filter_expr = builder.build_audio_crossfade(
            input1_index=0,
            input2_index=1,
            crossfade_duration=1.5,
            input1_duration=8.0,
            output_label="faded",
        )

        assert "[faded]" in filter_expr

    def test_build_complex_mix_music_only(self, builder):
        """Test complex mix with only music."""
        music_track = AudioTrack(input_index=0, volume=0.5)

        filter_expr = builder.build_complex_mix(music_track=music_track)

        assert "volume=0.5" in filter_expr

    def test_build_complex_mix_voiceover_only(self, builder):
        """Test complex mix with only voiceover."""
        voiceover_track = AudioTrack(input_index=1, volume=1.0)

        filter_expr = builder.build_complex_mix(voiceover_track=voiceover_track)

        assert "volume=1.0" in filter_expr

    def test_build_complex_mix_music_and_voiceover(self, builder):
        """Test complex mix with music and voiceover."""
        music_track = AudioTrack(input_index=0, volume=0.3)
        voiceover_track = AudioTrack(input_index=1, volume=1.0)

        filter_expr = builder.build_complex_mix(
            music_track=music_track, voiceover_track=voiceover_track
        )

        # Should have volume filters
        assert "volume=0.3" in filter_expr
        assert "volume=1.0" in filter_expr
        # Should have final mix
        assert "amix" in filter_expr

    def test_build_complex_mix_with_ducking(self, builder):
        """Test complex mix with music ducking during voiceover."""
        music_track = AudioTrack(input_index=0, volume=0.5)
        voiceover_track = AudioTrack(input_index=1, volume=1.0)

        filter_expr = builder.build_complex_mix(
            music_track=music_track, voiceover_track=voiceover_track, duck_music=True
        )

        # Should have sidechaincompress for ducking
        assert "sidechaincompress" in filter_expr

    def test_build_complex_mix_without_ducking(self, builder):
        """Test complex mix without music ducking."""
        music_track = AudioTrack(input_index=0, volume=0.5)
        voiceover_track = AudioTrack(input_index=1, volume=1.0)

        filter_expr = builder.build_complex_mix(
            music_track=music_track, voiceover_track=voiceover_track, duck_music=False
        )

        # Should not have sidechaincompress
        assert "sidechaincompress" not in filter_expr
        # Should still have final mix
        assert "amix" in filter_expr

    def test_build_complex_mix_with_original_audio(self, builder):
        """Test complex mix with original audio included."""
        music_track = AudioTrack(input_index=1, volume=0.3)
        voiceover_track = AudioTrack(input_index=2, volume=1.0)

        filter_expr = builder.build_complex_mix(
            music_track=music_track,
            voiceover_track=voiceover_track,
            original_audio_index=0,
        )

        # Should include all three audio sources
        assert "inputs=3" in filter_expr

    def test_build_complex_mix_all_sources(self, builder):
        """Test complex mix with all audio sources."""
        music_track = AudioTrack(input_index=1, volume=0.3)
        voiceover_track = AudioTrack(input_index=2, volume=1.0)

        filter_expr = builder.build_complex_mix(
            music_track=music_track,
            voiceover_track=voiceover_track,
            original_audio_index=0,
            duck_music=True,
        )

        # Should have ducking
        assert "sidechaincompress" in filter_expr
        # Should mix all sources
        assert "amix" in filter_expr

    def test_build_complex_mix_custom_output_label(self, builder):
        """Test complex mix with custom output label."""
        music_track = AudioTrack(input_index=0, volume=0.5)

        filter_expr = builder.build_complex_mix(music_track=music_track, output_label="final")

        assert "[final]" in filter_expr

    def test_build_complex_mix_no_sources(self, builder):
        """Test complex mix with no audio sources raises error."""
        with pytest.raises(ValueError, match="No audio tracks provided"):
            builder.build_complex_mix()


class TestIntegrationScenarios:
    """Test integration scenarios with complete workflows."""

    @pytest.fixture
    def builder(self):
        """Create an audio mixer builder."""
        return AudioMixerBuilder()

    def test_podcast_workflow(self, builder):
        """Test mixing podcast with music and voiceover."""
        # Background music with fade-out
        music_track = AudioTrack(input_index=1, volume=0.5, fade_out=2.0)
        voiceover_track = AudioTrack(input_index=2, volume=1.0)

        # Mix voiceover with background music
        filter_expr = builder.build_complex_mix(
            music_track=music_track, voiceover_track=voiceover_track, duck_music=True
        )

        # Verify ducking is applied
        assert "sidechaincompress" in filter_expr

    def test_video_with_background_music(self, builder):
        """Test video with background music at low volume."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),  # Original video audio
            AudioTrack(input_index=1, volume=0.2),  # Background music
        ]

        filter_expr = builder.mix_audio_tracks(tracks)

        # Verify both tracks are mixed
        assert "volume=1.0" in filter_expr
        assert "volume=0.2" in filter_expr
        assert "amix" in filter_expr

    def test_multi_track_composition(self, builder):
        """Test complex composition with multiple audio tracks."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),  # Original audio
            AudioTrack(input_index=1, volume=0.3),  # Background music
            AudioTrack(input_index=2, volume=0.8),  # Sound effects
            AudioTrack(input_index=3, volume=1.0),  # Voiceover
        ]

        filter_expr = builder.mix_audio_tracks(tracks, normalize=True)

        # Verify all tracks
        assert "inputs=4" in filter_expr
        assert "normalize=1" in filter_expr

    def test_broadcast_normalization_workflow(self, builder):
        """Test normalization for broadcast standards."""
        # Normalize to EBU R128 standard
        filter_expr = builder.build_audio_normalize(input_index=0, target_level=-23.0)

        # Verify EBU R128 parameters
        assert "loudnorm" in filter_expr
        assert "I=-23.0" in filter_expr
        assert "TP=-1.5" in filter_expr
        assert "LRA=11" in filter_expr

    def test_audio_sync_with_delay(self, builder):
        """Test audio sync correction with delay."""
        # Delay audio by 200ms to sync with video
        filter_expr = builder.build_audio_delay(input_index=0, delay_ms=200)

        assert "adelay=200" in filter_expr

    def test_smooth_transition_between_tracks(self, builder):
        """Test smooth crossfade between two music tracks."""
        filter_expr = builder.build_audio_crossfade(
            input1_index=0,
            input2_index=1,
            crossfade_duration=3.0,
            input1_duration=60.0,
        )

        # Verify crossfade parameters
        assert "acrossfade" in filter_expr
        assert "d=3.0" in filter_expr

    def test_narrator_with_background_music(self, builder):
        """Test narrator with automatically ducked background music."""
        filter_expr = builder.build_audio_ducking(
            main_audio_index=0,  # Background music
            voiceover_index=1,  # Narrator
            duck_amount=0.3,  # Reduce music to 30%
            attack_time=0.1,
            release_time=0.3,
        )

        # Verify ducking parameters
        assert "sidechaincompress" in filter_expr
        assert "attack=100" in filter_expr
        assert "release=300" in filter_expr

    def test_complete_production_workflow(self, builder):
        """Test complete audio production workflow."""
        # Original video audio
        # Background music at 20%
        # Voiceover at 100%
        # Duck music during voiceover

        music_track = AudioTrack(input_index=1, volume=0.2, fade_in=2.0, fade_out=2.0)
        voiceover_track = AudioTrack(input_index=2, volume=1.0)

        filter_expr = builder.build_complex_mix(
            music_track=music_track,
            voiceover_track=voiceover_track,
            original_audio_index=0,
            duck_music=True,
            output_label="final",
        )

        # Verify complete workflow
        assert "sidechaincompress" in filter_expr  # Ducking
        assert "amix" in filter_expr  # Final mix
        assert "[final]" in filter_expr  # Output label

    def test_stereo_preservation(self, builder):
        """Test mixing in merge mode to preserve stereo channels."""
        tracks = [
            AudioTrack(input_index=0, volume=1.0),
            AudioTrack(input_index=1, volume=0.5),
        ]

        filter_expr = builder.mix_audio_tracks(tracks, mode=AudioMixMode.MERGE)

        # Should use amerge to preserve channels
        assert "amerge" in filter_expr
        assert "inputs=2" in filter_expr

    def test_volume_normalization_chain(self, builder):
        """Test chaining volume adjustment with normalization."""
        # First apply volume, then normalize
        vol_filter = builder.build_volume_filter(input_index=0, volume=1.5, output_label="vol")
        norm_filter = builder.build_audio_normalize(input_index=0, output_label="norm")

        # Both filters should be independent
        assert "volume=1.5" in vol_filter
        assert "loudnorm" in norm_filter
