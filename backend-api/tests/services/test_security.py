"""
Unit tests for FFmpeg Security module.

Tests command escaping, validation, and security measures.
"""

import pytest

from services.ffmpeg.security import (
    FFmpegCommandValidator,
    FFmpegSecurityError,
    safe_quote,
    validate_duration,
    validate_numeric_range,
)


class TestFFmpegCommandValidator:
    """Test cases for FFmpegCommandValidator."""

    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        validator = FFmpegCommandValidator()
        assert validator.strict_mode is True

        validator_lenient = FFmpegCommandValidator(strict_mode=False)
        assert validator_lenient.strict_mode is False

    def test_escape_path_simple(self):
        """Test escaping simple paths."""
        validator = FFmpegCommandValidator()

        path = "video.mp4"
        escaped = validator.escape_path(path)

        # Should be quoted for safety
        assert escaped == "'video.mp4'" or escaped == "video.mp4"

    def test_escape_path_with_spaces(self):
        """Test escaping paths with spaces."""
        validator = FFmpegCommandValidator()

        path = "my video file.mp4"
        escaped = validator.escape_path(path)

        # Must be quoted when containing spaces
        assert "'" in escaped or '"' in escaped

    def test_escape_path_too_long_raises_error(self):
        """Test that excessively long paths are rejected."""
        validator = FFmpegCommandValidator()

        long_path = "a" * 5000
        with pytest.raises(FFmpegSecurityError, match="Path too long"):
            validator.escape_path(long_path)

    def test_validate_path_dangerous_patterns(self):
        """Test that dangerous path patterns are rejected in strict mode."""
        validator = FFmpegCommandValidator(strict_mode=True)

        dangerous_paths = [
            "../etc/passwd",  # Parent directory traversal
            "~/secret.txt",  # Home directory
            "file$VAR",  # Variable expansion
            "file`whoami`",  # Command substitution
        ]

        for path in dangerous_paths:
            with pytest.raises(FFmpegSecurityError):
                validator.validate_path(path)

    def test_validate_path_shell_metacharacters(self):
        """Test that paths with shell metacharacters are rejected."""
        validator = FFmpegCommandValidator()

        dangerous_chars = [";", "&", "|", ">", "<", "\n"]

        for char in dangerous_chars:
            path = f"file{char}name.mp4"
            with pytest.raises(FFmpegSecurityError, match="shell metacharacter"):
                validator.validate_path(path)

    def test_validate_path_null_byte(self):
        """Test that paths with null bytes are rejected."""
        validator = FFmpegCommandValidator()

        path = "file\x00name.mp4"
        with pytest.raises(FFmpegSecurityError, match="null byte"):
            validator.validate_path(path)

    def test_validate_path_allowed_extensions(self):
        """Test extension validation."""
        validator = FFmpegCommandValidator()

        # Allowed extension should pass
        validator.validate_path("video.mp4", allowed_extensions=[".mp4", ".mov"])

        # Disallowed extension should fail
        with pytest.raises(FFmpegSecurityError, match="not in allowed list"):
            validator.validate_path("script.sh", allowed_extensions=[".mp4", ".mov"])

    def test_validate_filter_expression_simple(self):
        """Test validating simple filter expressions."""
        validator = FFmpegCommandValidator()

        # Valid filter expressions
        valid_filters = [
            "[0:v]scale=1920:1080[out]",
            "[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "[0:v]fps=30[v0]",
        ]

        for filter_expr in valid_filters:
            assert validator.validate_filter_expression(filter_expr) is True

    def test_validate_filter_expression_too_long(self):
        """Test that excessively long filter expressions are rejected."""
        validator = FFmpegCommandValidator()

        long_filter = "[0:v]" + ("scale=1920:1080," * 10000) + "[out]"
        with pytest.raises(FFmpegSecurityError, match="Filter expression too long"):
            validator.validate_filter_expression(long_filter)

    def test_validate_filter_expression_null_byte(self):
        """Test that filter expressions with null bytes are rejected."""
        validator = FFmpegCommandValidator()

        filter_expr = "[0:v]scale=1920:1080\x00[out]"
        with pytest.raises(FFmpegSecurityError, match="null byte"):
            validator.validate_filter_expression(filter_expr)

    def test_validate_filter_suspicious_chars_strict(self):
        """Test that suspicious characters are rejected in strict mode."""
        validator = FFmpegCommandValidator(strict_mode=True)

        suspicious_filters = [
            "[0:v];whoami",
            "[0:v]|cat /etc/passwd",
            "[0:v]`id`",
        ]

        for filter_expr in suspicious_filters:
            with pytest.raises(FFmpegSecurityError, match="suspicious character"):
                validator.validate_filter_expression(filter_expr)

    def test_validate_option_valid(self):
        """Test validating valid FFmpeg options."""
        validator = FFmpegCommandValidator()

        valid_options = [
            ("-c:v", "libx264"),
            ("-crf", "21"),
            ("-preset", "medium"),
            ("--help", None),
        ]

        for option, value in valid_options:
            assert validator.validate_option(option, value) is True

    def test_validate_option_no_dash_prefix(self):
        """Test that options without - prefix are rejected."""
        validator = FFmpegCommandValidator()

        with pytest.raises(FFmpegSecurityError, match="must start with"):
            validator.validate_option("invalid")

    def test_validate_option_shell_metacharacters(self):
        """Test that options with shell metacharacters are rejected."""
        validator = FFmpegCommandValidator()

        with pytest.raises(FFmpegSecurityError, match="shell metacharacter"):
            validator.validate_option("-c:v;whoami")

    def test_validate_option_value_null_byte(self):
        """Test that option values with null bytes are rejected."""
        validator = FFmpegCommandValidator()

        with pytest.raises(FFmpegSecurityError, match="null byte"):
            validator.validate_option("-c:v", "libx264\x00")

    def test_validate_command_length_string(self):
        """Test validating command length from string."""
        validator = FFmpegCommandValidator()

        # Normal command should pass
        command = "ffmpeg -i input.mp4 -c:v libx264 output.mp4"
        assert validator.validate_command_length(command) is True

        # Excessively long command should fail
        long_command = "ffmpeg " + (" -i input.mp4" * 10000)
        with pytest.raises(FFmpegSecurityError, match="Command too long"):
            validator.validate_command_length(long_command)

    def test_validate_command_length_list(self):
        """Test validating command length from argument list."""
        validator = FFmpegCommandValidator()

        # Normal command should pass
        command_args = ["ffmpeg", "-i", "input.mp4", "-c:v", "libx264", "output.mp4"]
        assert validator.validate_command_length(command_args) is True

    def test_sanitize_text_simple(self):
        """Test sanitizing simple text."""
        validator = FFmpegCommandValidator()

        text = "Hello World"
        sanitized = validator.sanitize_text(text)

        assert sanitized == "Hello World"

    def test_sanitize_text_removes_control_chars(self):
        """Test that control characters are removed (except newline/tab)."""
        validator = FFmpegCommandValidator()

        text = "Hello\x01\x02World"
        sanitized = validator.sanitize_text(text)

        # Control characters should be removed
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized
        assert "Hello" in sanitized
        assert "World" in sanitized

    def test_sanitize_text_preserves_newline_tab(self):
        """Test that newlines and tabs are preserved."""
        validator = FFmpegCommandValidator()

        text = "Hello\nWorld\tTest"
        sanitized = validator.sanitize_text(text)

        assert "\n" in sanitized
        assert "\t" in sanitized

    def test_sanitize_text_too_long(self):
        """Test that excessively long text is rejected."""
        validator = FFmpegCommandValidator()

        long_text = "a" * 2000
        with pytest.raises(FFmpegSecurityError, match="Text too long"):
            validator.sanitize_text(long_text, max_length=1000)

    def test_sanitize_text_null_byte(self):
        """Test that text with null bytes is rejected."""
        validator = FFmpegCommandValidator()

        text = "Hello\x00World"
        with pytest.raises(FFmpegSecurityError, match="null byte"):
            validator.sanitize_text(text)


class TestSecurityHelpers:
    """Test cases for security helper functions."""

    def test_safe_quote_simple_string(self):
        """Test safe_quote with simple string."""
        result = safe_quote("video.mp4")
        # Should be safely quoted
        assert result == "'video.mp4'" or result == "video.mp4"

    def test_safe_quote_with_spaces(self):
        """Test safe_quote with spaces."""
        result = safe_quote("my video file.mp4")
        # Must contain quotes
        assert "'" in result or '"' in result

    def test_safe_quote_number(self):
        """Test safe_quote with number."""
        result = safe_quote(42)
        assert result == "42" or result == "'42'"

    def test_validate_duration_valid(self):
        """Test validating valid durations."""
        assert validate_duration(10.0) is True
        assert validate_duration(60.0) is True
        assert validate_duration(3600.0) is True

    def test_validate_duration_negative_raises_error(self):
        """Test that negative durations are rejected."""
        with pytest.raises(FFmpegSecurityError, match="cannot be negative"):
            validate_duration(-10.0)

    def test_validate_duration_too_long_raises_error(self):
        """Test that excessively long durations are rejected."""
        with pytest.raises(FFmpegSecurityError, match="Duration too long"):
            validate_duration(7200.0, max_duration=3600.0)

    def test_validate_numeric_range_valid(self):
        """Test validating values within range."""
        assert validate_numeric_range(50, 0, 100, "value") is True
        assert validate_numeric_range(0, 0, 100, "value") is True
        assert validate_numeric_range(100, 0, 100, "value") is True

    def test_validate_numeric_range_below_minimum(self):
        """Test that values below minimum are rejected."""
        with pytest.raises(FFmpegSecurityError, match="must be between"):
            validate_numeric_range(-10, 0, 100, "value")

    def test_validate_numeric_range_above_maximum(self):
        """Test that values above maximum are rejected."""
        with pytest.raises(FFmpegSecurityError, match="must be between"):
            validate_numeric_range(150, 0, 100, "value")

    def test_validate_numeric_range_custom_name(self):
        """Test that custom name appears in error message."""
        try:
            validate_numeric_range(150, 0, 100, "CRF")
        except FFmpegSecurityError as e:
            assert "CRF" in str(e)


@pytest.mark.parametrize(
    "path,expected_valid",
    [
        ("video.mp4", True),
        ("path/to/video.mp4", True),
        ("/absolute/path/video.mp4", True),
        ("file with spaces.mp4", True),
        ("file;danger.mp4", False),
        ("file&danger.mp4", False),
        ("file|danger.mp4", False),
    ],
)
def test_path_validation_parametrized(path, expected_valid):
    """Parametrized test for path validation."""
    validator = FFmpegCommandValidator()

    if expected_valid:
        # Should not raise
        validator.validate_path(path)
    else:
        # Should raise FFmpegSecurityError
        with pytest.raises(FFmpegSecurityError):
            validator.validate_path(path)
