"""
Unit tests for FFmpeg Command Builder.

Tests the core FFmpegCommandBuilder class with various scenarios.
"""

import pytest

from services.ffmpeg.command_builder import FFmpegCommandBuilder, InputFile, OutputFile


class TestFFmpegCommandBuilder:
    """Test cases for FFmpegCommandBuilder."""

    def test_builder_initialization(self):
        """Test builder initializes with empty state."""
        builder = FFmpegCommandBuilder()

        assert builder.get_input_count() == 0
        assert builder._output is None
        assert len(builder._filter_complex) == 0

    def test_add_single_input(self):
        """Test adding a single input file."""
        builder = FFmpegCommandBuilder()
        builder.add_input("video.mp4")

        assert builder.get_input_count() == 1
        input_file = builder.get_input_by_index(0)
        assert input_file is not None
        assert input_file.path == "video.mp4"
        assert input_file.index == 0

    def test_add_multiple_inputs(self):
        """Test adding multiple input files with auto-incrementing indices."""
        builder = FFmpegCommandBuilder()
        builder.add_input("video1.mp4")
        builder.add_input("video2.mp4")
        builder.add_input("audio.mp3")

        assert builder.get_input_count() == 3

        for i in range(3):
            input_file = builder.get_input_by_index(i)
            assert input_file is not None
            assert input_file.index == i

    def test_add_input_with_options(self):
        """Test adding input with options like seek and duration."""
        builder = FFmpegCommandBuilder()
        builder.add_input("video.mp4", seek=10.0, duration=30.0)

        input_file = builder.get_input_by_index(0)
        assert input_file is not None
        assert input_file.options["-ss"] == "10.0"
        assert input_file.options["-t"] == "30.0"

    def test_add_input_with_label(self):
        """Test adding input with custom label."""
        builder = FFmpegCommandBuilder()
        builder.add_input("music.mp3", label="background_music")

        input_file = builder.get_input_by_label("background_music")
        assert input_file is not None
        assert input_file.path == "music.mp3"

    def test_set_output(self):
        """Test setting output file with encoding options."""
        builder = FFmpegCommandBuilder()
        builder.set_output("output.mp4", codec="libx264", crf=21, preset="medium")

        assert builder._output is not None
        assert builder._output.path == "output.mp4"
        assert builder._output.options["-c:v"] == "libx264"
        assert builder._output.options["-crf"] == "21"
        assert builder._output.options["-preset"] == "medium"

    def test_add_global_option(self):
        """Test adding global options."""
        builder = FFmpegCommandBuilder()
        builder.add_global_option("-y")
        builder.add_global_option("-loglevel", "error")

        assert "-y" in builder._global_options
        assert "-loglevel" in builder._global_options
        assert "error" in builder._global_options

    def test_add_filter_complex(self):
        """Test adding filter complex expressions."""
        builder = FFmpegCommandBuilder()
        builder.add_filter_complex("[0:v][1:v]concat=n=2:v=1:a=0[out]")

        assert len(builder._filter_complex) == 1
        assert "[0:v][1:v]concat=n=2:v=1:a=0[out]" in builder._filter_complex

    def test_build_simple_command(self):
        """Test building a simple FFmpeg command."""
        builder = FFmpegCommandBuilder()
        builder.add_global_option("-y")
        builder.add_input("input.mp4")
        builder.set_output("output.mp4", codec="libx264", crf=21)

        command = builder.build()

        assert command.startswith("ffmpeg")
        assert "-y" in command
        assert "-i" in command
        assert "'input.mp4'" in command or "input.mp4" in command
        assert "-c:v libx264" in command
        assert "-crf 21" in command

    def test_build_command_with_filter_complex(self):
        """Test building command with filter complex."""
        builder = FFmpegCommandBuilder()
        builder.add_input("video1.mp4")
        builder.add_input("video2.mp4")
        builder.add_filter_complex("[0:v][1:v]concat=n=2:v=1:a=0[out]")
        builder.set_output("output.mp4", codec="libx264", crf=21")

        command = builder.build()

        assert "-filter_complex" in command
        assert "concat" in command

    def test_build_args_list(self):
        """Test building command as argument list (for subprocess)."""
        builder = FFmpegCommandBuilder()
        builder.add_input("input.mp4")
        builder.set_output("output.mp4", codec="libx264", crf=21")

        args = builder.build_args()

        assert isinstance(args, list)
        assert args[0] == "ffmpeg"
        assert "-i" in args
        assert "input.mp4" in args
        assert "-c:v" in args
        assert "libx264" in args

    def test_build_without_output_raises_error(self):
        """Test that building without output raises ValueError."""
        builder = FFmpegCommandBuilder()
        builder.add_input("input.mp4")

        with pytest.raises(ValueError, match="Cannot build command without output file"):
            builder.build()

    def test_build_without_inputs_raises_error(self):
        """Test that building without inputs raises ValueError."""
        builder = FFmpegCommandBuilder()
        builder.set_output("output.mp4")

        with pytest.raises(ValueError, match="Cannot build command without input files"):
            builder.build()

    def test_method_chaining(self):
        """Test fluent API with method chaining."""
        builder = FFmpegCommandBuilder()

        result = (
            builder.add_global_option("-y")
            .add_input("input.mp4")
            .add_filter_complex("[0:v]scale=1920:1080[v]")
            .set_output("output.mp4", codec="libx264", crf=21)
        )

        # Method chaining should return self
        assert result is builder

        # Command should build successfully
        command = builder.build()
        assert command.startswith("ffmpeg")

    def test_path_escaping(self):
        """Test that paths with spaces are properly escaped."""
        builder = FFmpegCommandBuilder()
        builder.add_input("my video file.mp4")
        builder.set_output("output file.mp4", codec="copy")

        command = builder.build()

        # Paths with spaces should be quoted
        assert "'" in command or '"' in command

    def test_get_input_by_invalid_index(self):
        """Test getting input by invalid index returns None."""
        builder = FFmpegCommandBuilder()
        builder.add_input("video.mp4")

        assert builder.get_input_by_index(99) is None
        assert builder.get_input_by_index(-1) is None

    def test_get_input_by_nonexistent_label(self):
        """Test getting input by nonexistent label returns None."""
        builder = FFmpegCommandBuilder()
        builder.add_input("video.mp4", label="test")

        assert builder.get_input_by_label("nonexistent") is None

    def test_set_video_codec(self):
        """Test setting video codec separately."""
        builder = FFmpegCommandBuilder()
        builder.add_input("input.mp4")
        builder.set_video_codec("libx265", crf=28)
        builder.set_output("output.mp4")

        assert builder._video_codec == "libx265"
        assert builder._additional_output_options["-c:v"] == "libx265"
        assert builder._additional_output_options["crf"] == 28

    def test_set_audio_codec(self):
        """Test setting audio codec separately."""
        builder = FFmpegCommandBuilder()
        builder.add_input("input.mp4")
        builder.set_audio_codec("aac", bitrate="128k")
        builder.set_output("output.mp4")

        assert builder._audio_codec == "aac"
        assert builder._additional_output_options["-c:a"] == "aac"

    def test_repr(self):
        """Test string representation of builder."""
        builder = FFmpegCommandBuilder()
        builder.add_input("video1.mp4")
        builder.add_input("video2.mp4")
        builder.set_output("output.mp4")

        repr_str = repr(builder)

        assert "FFmpegCommandBuilder" in repr_str
        assert "inputs=2" in repr_str
        assert "output.mp4" in repr_str


class TestInputFile:
    """Test cases for InputFile dataclass."""

    def test_input_file_creation(self):
        """Test creating an InputFile."""
        input_file = InputFile(path="video.mp4", index=0)

        assert input_file.path == "video.mp4"
        assert input_file.index == 0
        assert input_file.options == {}
        assert input_file.label is None

    def test_input_file_with_options(self):
        """Test InputFile with options."""
        options = {"-ss": "10", "-t": "30"}
        input_file = InputFile(path="video.mp4", index=0, options=options)

        assert input_file.options == options

    def test_input_file_str_representation(self):
        """Test string representation of InputFile."""
        input_file = InputFile(path="video.mp4", index=0)
        str_repr = str(input_file)

        assert "Input[0]" in str_repr
        assert "video.mp4" in str_repr


class TestOutputFile:
    """Test cases for OutputFile dataclass."""

    def test_output_file_creation(self):
        """Test creating an OutputFile."""
        output_file = OutputFile(path="output.mp4")

        assert output_file.path == "output.mp4"
        assert output_file.options == {}

    def test_output_file_with_options(self):
        """Test OutputFile with encoding options."""
        options = {"-c:v": "libx264", "-crf": "21"}
        output_file = OutputFile(path="output.mp4", options=options)

        assert output_file.options == options

    def test_output_file_str_representation(self):
        """Test string representation of OutputFile."""
        output_file = OutputFile(path="output.mp4")
        str_repr = str(output_file)

        assert "Output" in str_repr
        assert "output.mp4" in str_repr


@pytest.mark.parametrize(
    "crf,expected",
    [
        (18, "-crf 18"),
        (21, "-crf 21"),
        (28, "-crf 28"),
    ],
)
def test_crf_values(crf, expected):
    """Test different CRF values are properly included."""
    builder = FFmpegCommandBuilder()
    builder.add_input("input.mp4")
    builder.set_output("output.mp4", codec="libx264", crf=crf)

    command = builder.build()

    assert expected in command


@pytest.mark.parametrize(
    "preset",
    ["ultrafast", "fast", "medium", "slow", "veryslow"],
)
def test_encoding_presets(preset):
    """Test different encoding presets."""
    builder = FFmpegCommandBuilder()
    builder.add_input("input.mp4")
    builder.set_output("output.mp4", codec="libx264", preset=preset)

    command = builder.build()

    assert f"-preset {preset}" in command
