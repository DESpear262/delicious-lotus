"""
Audio Mixing and Processing for FFmpeg operations.

This module provides utilities for mixing multiple audio tracks, volume control,
audio ducking for voiceovers, and audio effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AudioMixMode(str, Enum):
    """Audio mixing modes."""

    MERGE = "merge"  # Merge channels (preserves all channels)
    MIX = "mix"  # Mix streams (combines to stereo)


@dataclass
class AudioTrack:
    """Represents an audio track with volume and timing.

    Attributes:
        input_index: Input file index
        volume: Volume level (0.0 to 2.0, where 1.0 is original)
        start_time: When to start playing this track (seconds)
        end_time: When to stop playing this track (seconds, None = end)
        fade_in: Fade in duration in seconds
        fade_out: Fade out duration in seconds
    """

    input_index: int
    volume: float = 1.0
    start_time: float = 0.0
    end_time: float | None = None
    fade_in: float = 0.0
    fade_out: float = 0.0

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AudioTrack[{self.input_index}]: "
            f"volume={self.volume:.2f}, "
            f"{self.start_time:.1f}s - {self.end_time or 'end'}"
        )


class AudioMixerBuilder:
    """
    Builder for creating FFmpeg audio mixing filter expressions.

    Provides utilities for mixing multiple audio tracks with volume control,
    audio ducking, and crossfading.

    Example:
        >>> builder = AudioMixerBuilder()
        >>> tracks = [
        ...     AudioTrack(input_index=0, volume=1.0),  # Main audio
        ...     AudioTrack(input_index=1, volume=0.3),  # Background music
        ... ]
        >>> filter_expr = builder.mix_audio_tracks(tracks)
    """

    def __init__(self) -> None:
        """Initialize the audio mixer builder."""
        self._label_counter = 0

    def _generate_label(self, prefix: str = "a") -> str:
        """
        Generate a unique audio stream label.

        Args:
            prefix: Prefix for the label

        Returns:
            Unique label string
        """
        label = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return label

    def build_volume_filter(
        self,
        input_index: int,
        volume: float,
        output_label: str | None = None,
    ) -> str:
        """
        Build a volume adjustment filter.

        Args:
            input_index: Input file index
            volume: Volume multiplier (0.0 to 2.0, where 1.0 is original)
            output_label: Optional output label

        Returns:
            Filter expression string

        Example:
            >>> builder.build_volume_filter(0, 0.5)
            '[0:a]volume=0.5[a0]'
        """
        if output_label is None:
            output_label = self._generate_label()

        # Clamp volume to reasonable range
        volume = max(0.0, min(2.0, volume))

        filter_expr = f"[{input_index}:a]volume={volume}[{output_label}]"

        return filter_expr

    def build_audio_fade(
        self,
        input_index: int,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        duration: float | None = None,
        output_label: str | None = None,
    ) -> str:
        """
        Build an audio fade filter.

        Args:
            input_index: Input file index
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
            duration: Total audio duration (required for fade out)
            output_label: Optional output label

        Returns:
            Filter expression string

        Example:
            >>> builder.build_audio_fade(0, fade_in=2.0, fade_out=2.0, duration=10.0)
            '[0:a]afade=t=in:st=0:d=2.0,afade=t=out:st=8.0:d=2.0[a0]'
        """
        if output_label is None:
            output_label = self._generate_label()

        filters: list[str] = []

        # Fade in
        if fade_in > 0:
            filters.append(f"afade=t=in:st=0:d={fade_in}")

        # Fade out
        if fade_out > 0 and duration is not None:
            fade_start = max(0, duration - fade_out)
            filters.append(f"afade=t=out:st={fade_start}:d={fade_out}")

        if not filters:
            # No fades, use null filter
            return f"[{input_index}:a]anull[{output_label}]"

        filter_expr = f"[{input_index}:a]{','.join(filters)}[{output_label}]"

        return filter_expr

    def mix_audio_tracks(
        self,
        tracks: list[AudioTrack],
        mode: AudioMixMode = AudioMixMode.MIX,
        output_label: str = "aout",
        normalize: bool = True,
    ) -> str:
        """
        Mix multiple audio tracks together.

        Args:
            tracks: List of AudioTrack objects
            mode: Mixing mode (merge or mix)
            output_label: Output stream label
            normalize: Whether to normalize volume to prevent clipping

        Returns:
            Complete filter expression for mixing

        Example:
            >>> tracks = [
            ...     AudioTrack(0, volume=1.0),  # Main audio at full volume
            ...     AudioTrack(1, volume=0.3),  # Background music at 30%
            ... ]
            >>> filter_expr = builder.mix_audio_tracks(tracks)
        """
        if not tracks:
            raise ValueError("Need at least one audio track to mix")

        if len(tracks) == 1:
            # Single track, just apply volume
            track = tracks[0]
            return self.build_volume_filter(track.input_index, track.volume, output_label)

        # Build volume filters for each track
        volume_filters: list[str] = []
        volume_labels: list[str] = []

        for i, track in enumerate(tracks):
            label = self._generate_label(f"vol{i}")
            volume_labels.append(label)

            # Apply volume adjustment
            filter_expr = f"[{track.input_index}:a]volume={track.volume}[{label}]"
            volume_filters.append(filter_expr)

        # Build mixing filter
        if mode == AudioMixMode.MERGE:
            # Use amerge to preserve all channels
            input_refs = "".join(f"[{label}]" for label in volume_labels)
            mix_filter = f"{input_refs}amerge=inputs={len(tracks)}[{output_label}]"
        else:
            # Use amix to combine streams
            input_refs = "".join(f"[{label}]" for label in volume_labels)
            normalize_arg = "1" if normalize else "0"
            mix_filter = (
                f"{input_refs}amix=inputs={len(tracks)}:duration=longest:normalize={normalize_arg}"
                f"[{output_label}]"
            )

        # Combine all filters
        all_filters = volume_filters + [mix_filter]
        return ";".join(all_filters)

    def build_audio_ducking(
        self,
        main_audio_index: int,
        voiceover_index: int,
        duck_amount: float = 0.3,
        attack_time: float = 0.1,
        release_time: float = 0.3,
        threshold: float = -20.0,
        output_label: str = "aout",
    ) -> str:
        """
        Build audio ducking filter (reduce main audio when voiceover plays).

        Uses sidechaincompress to automatically lower background music/audio
        when voiceover or narration is present.

        Args:
            main_audio_index: Index of main audio to be ducked (background music)
            voiceover_index: Index of voiceover/speech that triggers ducking
            duck_amount: How much to reduce main audio (0.0-1.0, where 0.3 = 70% reduction)
            attack_time: How quickly to duck (seconds)
            release_time: How quickly to restore volume (seconds)
            threshold: Voiceover level threshold in dB (-40 to 0)
            output_label: Output stream label

        Returns:
            Filter expression for audio ducking

        Example:
            >>> # Duck background music when voiceover plays
            >>> filter_expr = builder.build_audio_ducking(
            ...     main_audio_index=0,  # Background music
            ...     voiceover_index=1,   # Voiceover
            ...     duck_amount=0.3      # Reduce to 30% when speaking
            ... )
        """
        # sidechaincompress parameters:
        # - threshold: dB level at which compression starts
        # - ratio: compression ratio (higher = more compression)
        # - attack: how quickly compression engages
        # - release: how quickly compression disengages

        # Convert duck_amount to compression ratio
        # duck_amount of 0.3 means reduce to 30%, which is ~3:1 ratio
        ratio = 1.0 / (1.0 - duck_amount) if duck_amount < 1.0 else 20.0

        filter_expr = (
            f"[{main_audio_index}:a][{voiceover_index}:a]"
            f"sidechaincompress="
            f"threshold={threshold}:"
            f"ratio={ratio}:"
            f"attack={attack_time * 1000}:"  # Convert to milliseconds
            f"release={release_time * 1000}:"
            f"makeup=2"  # Gain makeup
            f"[{output_label}]"
        )

        return filter_expr

    def build_audio_delay(
        self,
        input_index: int,
        delay_ms: float,
        output_label: str | None = None,
    ) -> str:
        """
        Build an audio delay filter.

        Args:
            input_index: Input file index
            delay_ms: Delay in milliseconds
            output_label: Optional output label

        Returns:
            Filter expression string

        Example:
            >>> builder.build_audio_delay(0, 500)  # 500ms delay
            '[0:a]adelay=500[a0]'
        """
        if output_label is None:
            output_label = self._generate_label()

        filter_expr = f"[{input_index}:a]adelay={int(delay_ms)}[{output_label}]"

        return filter_expr

    def build_audio_normalize(
        self,
        input_index: int,
        target_level: float = -23.0,
        output_label: str | None = None,
    ) -> str:
        """
        Build loudness normalization filter (EBU R128).

        Args:
            input_index: Input file index
            target_level: Target loudness in LUFS (default: -23.0 for broadcast)
            output_label: Optional output label

        Returns:
            Filter expression string

        Example:
            >>> builder.build_audio_normalize(0, target_level=-16.0)
            '[0:a]loudnorm=I=-16.0:TP=-1.5:LRA=11[a0]'
        """
        if output_label is None:
            output_label = self._generate_label()

        # EBU R128 normalization with common settings
        # I = Integrated loudness target
        # TP = True peak limit
        # LRA = Loudness range target

        filter_expr = (
            f"[{input_index}:a]loudnorm="
            f"I={target_level}:"
            f"TP=-1.5:"  # True peak limit
            f"LRA=11"  # Loudness range
            f"[{output_label}]"
        )

        return filter_expr

    def build_audio_crossfade(
        self,
        input1_index: int,
        input2_index: int,
        crossfade_duration: float,
        input1_duration: float,
        output_label: str = "aout",
    ) -> str:
        """
        Build audio crossfade between two tracks.

        Args:
            input1_index: First audio track index
            input2_index: Second audio track index
            crossfade_duration: Crossfade duration in seconds
            input1_duration: Duration of first track
            output_label: Output stream label

        Returns:
            Filter expression for audio crossfade

        Example:
            >>> filter_expr = builder.build_audio_crossfade(0, 1, 2.0, 10.0)
        """
        # Use acrossfade filter
        # offset is when to start crossfade (end of first track - crossfade duration)
        offset = input1_duration - crossfade_duration

        filter_expr = (
            f"[{input1_index}:a][{input2_index}:a]"
            f"acrossfade=d={crossfade_duration}:c1=tri:c2=tri"
            f"[{output_label}]"
        )

        return filter_expr

    def build_complex_mix(
        self,
        music_track: AudioTrack | None = None,
        voiceover_track: AudioTrack | None = None,
        original_audio_index: int | None = None,
        duck_music: bool = True,
        output_label: str = "aout",
    ) -> str:
        """
        Build a complex audio mix with background music, voiceover, and original audio.

        This is a higher-level helper that combines multiple audio sources with
        automatic ducking of background music during voiceover.

        Args:
            music_track: Background music track
            voiceover_track: Voiceover/narration track
            original_audio_index: Original video audio index
            duck_music: Whether to duck music during voiceover
            output_label: Final output label

        Returns:
            Complete filter complex for audio mixing

        Example:
            >>> filter_expr = builder.build_complex_mix(
            ...     music_track=AudioTrack(1, volume=0.3),
            ...     voiceover_track=AudioTrack(2, volume=1.0),
            ...     original_audio_index=0,
            ...     duck_music=True
            ... )
        """
        filters: list[str] = []
        intermediate_labels: list[str] = []

        # Process music track
        if music_track is not None:
            music_label = self._generate_label("music")
            music_filter = self.build_volume_filter(
                music_track.input_index,
                music_track.volume,
                music_label,
            )
            filters.append(music_filter)
            intermediate_labels.append(music_label)

        # Process voiceover track
        if voiceover_track is not None:
            vo_label = self._generate_label("vo")
            vo_filter = self.build_volume_filter(
                voiceover_track.input_index,
                voiceover_track.volume,
                vo_label,
            )
            filters.append(vo_filter)

            # Apply ducking if enabled and music exists
            if duck_music and music_track is not None and intermediate_labels:
                ducked_label = self._generate_label("ducked")
                duck_filter = (
                    f"[{intermediate_labels[-1]}][{vo_label}]"
                    f"sidechaincompress=threshold=-20:ratio=4:attack=100:release=300"
                    f"[{ducked_label}]"
                )
                filters.append(duck_filter)
                # Replace music label with ducked version
                intermediate_labels[-1] = ducked_label
                # Add voiceover to mix
                intermediate_labels.append(vo_label)
            else:
                intermediate_labels.append(vo_label)

        # Add original audio if specified
        if original_audio_index is not None:
            orig_label = self._generate_label("orig")
            orig_filter = f"[{original_audio_index}:a]anull[{orig_label}]"
            filters.append(orig_filter)
            intermediate_labels.append(orig_label)

        # Final mix
        if len(intermediate_labels) > 1:
            input_refs = "".join(f"[{label}]" for label in intermediate_labels)
            mix_filter = (
                f"{input_refs}amix=inputs={len(intermediate_labels)}:"
                f"duration=longest:normalize=1[{output_label}]"
            )
            filters.append(mix_filter)
        elif len(intermediate_labels) == 1:
            # Single track, just relabel
            filters.append(f"[{intermediate_labels[0]}]anull[{output_label}]")
        else:
            raise ValueError("No audio tracks provided for mixing")

        return ";".join(filters)
