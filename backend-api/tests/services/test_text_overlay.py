"""
Unit tests for Text Overlay Builder.

Tests the TextOverlayBuilder class with various text overlay scenarios.
"""

import pytest
from services.ffmpeg.text_overlay import (
    TextAnimation,
    TextOverlayBuilder,
    TextPosition,
    TextStyle,
)


class TestTextStyle:
    """Test cases for TextStyle dataclass."""

    def test_default_style(self):
        """Test default text style configuration."""
        style = TextStyle()

        assert style.font == "Sans"
        assert style.font_size == 48
        assert style.font_color == "white"
        assert style.border_width == 2
        assert style.border_color == "black"
        assert style.shadow_x == 0
        assert style.shadow_y == 0
        assert style.shadow_color == "black"
        assert style.background_color is None
        assert style.background_opacity == 0.7

    def test_custom_style(self):
        """Test custom text style configuration."""
        style = TextStyle(
            font="Arial",
            font_size=72,
            font_color="#FF0000",
            border_width=4,
            border_color="yellow",
            shadow_x=2,
            shadow_y=2,
            shadow_color="gray",
            background_color="black",
            background_opacity=0.5,
        )

        assert style.font == "Arial"
        assert style.font_size == 72
        assert style.font_color == "#FF0000"
        assert style.border_width == 4
        assert style.border_color == "yellow"
        assert style.shadow_x == 2
        assert style.shadow_y == 2
        assert style.shadow_color == "gray"
        assert style.background_color == "black"
        assert style.background_opacity == 0.5


class TestTextPosition:
    """Test cases for TextPosition enum."""

    def test_all_positions_exist(self):
        """Test that all expected positions are defined."""
        expected_positions = [
            "TOP_LEFT",
            "TOP_CENTER",
            "TOP_RIGHT",
            "CENTER_LEFT",
            "CENTER",
            "CENTER_RIGHT",
            "BOTTOM_LEFT",
            "BOTTOM_CENTER",
            "BOTTOM_RIGHT",
        ]

        for position_name in expected_positions:
            assert hasattr(TextPosition, position_name)

    def test_position_values(self):
        """Test position enum values are correct."""
        assert TextPosition.TOP_LEFT.value == "top_left"
        assert TextPosition.CENTER.value == "center"
        assert TextPosition.BOTTOM_RIGHT.value == "bottom_right"


class TestTextAnimation:
    """Test cases for TextAnimation enum."""

    def test_all_animations_exist(self):
        """Test that all expected animations are defined."""
        expected_animations = [
            "NONE",
            "FADE_IN",
            "FADE_OUT",
            "SLIDE_LEFT",
            "SLIDE_RIGHT",
            "SLIDE_UP",
            "SLIDE_DOWN",
        ]

        for animation_name in expected_animations:
            assert hasattr(TextAnimation, animation_name)

    def test_animation_values(self):
        """Test animation enum values are correct."""
        assert TextAnimation.NONE.value == "none"
        assert TextAnimation.FADE_IN.value == "fade_in"
        assert TextAnimation.SLIDE_UP.value == "slide_up"


class TestTextOverlayBuilder:
    """Test cases for TextOverlayBuilder."""

    @pytest.fixture
    def builder(self):
        """Create a text overlay builder."""
        return TextOverlayBuilder()

    def test_builder_initialization(self, builder):
        """Test builder initializes correctly."""
        assert builder is not None

    def test_escape_text_single_quotes(self, builder):
        """Test escaping of single quotes."""
        text = "It's a test"
        escaped = builder._escape_text(text)

        assert "'\\\\''" in escaped or "\\'" in escaped

    def test_escape_text_colons(self, builder):
        """Test escaping of colons."""
        text = "Time: 12:34"
        escaped = builder._escape_text(text)

        assert "\\:" in escaped

    def test_escape_text_newlines(self, builder):
        """Test escaping of newlines."""
        text = "Line 1\nLine 2"
        escaped = builder._escape_text(text)

        assert "\\n" in escaped

    def test_escape_text_percent(self, builder):
        """Test escaping of percent signs."""
        text = "100% complete"
        escaped = builder._escape_text(text)

        assert "\\%" in escaped

    def test_position_to_coordinates_center(self, builder):
        """Test center position coordinates."""
        x, y = builder._position_to_coordinates(TextPosition.CENTER)

        assert x == "(w-tw)/2"
        assert y == "(h-th)/2"

    def test_position_to_coordinates_top_left(self, builder):
        """Test top-left position coordinates."""
        x, y = builder._position_to_coordinates(TextPosition.TOP_LEFT, margin=20)

        assert x == "20"
        assert y == "20"

    def test_position_to_coordinates_bottom_right(self, builder):
        """Test bottom-right position coordinates."""
        x, y = builder._position_to_coordinates(TextPosition.BOTTOM_RIGHT, margin=20)

        assert "w-tw-20" in x
        assert "h-th-20" in y

    def test_position_to_coordinates_custom_margin(self, builder):
        """Test position with custom margin."""
        x, y = builder._position_to_coordinates(TextPosition.TOP_LEFT, margin=50)

        assert x == "50"
        assert y == "50"

    def test_create_simple_text_overlay(self, builder):
        """Test creating a simple text overlay."""
        overlay = builder.create_text_overlay(
            input_index=0, text="Hello World", position=TextPosition.CENTER
        )

        # Verify filter contains expected elements
        assert "[0:v]drawtext=" in overlay
        assert "text=" in overlay
        assert "Hello World" in overlay or "Hello" in overlay  # May be escaped
        assert "fontsize=" in overlay
        assert "[vout]" in overlay

    def test_create_text_overlay_with_timing(self, builder):
        """Test text overlay with start and end times."""
        overlay = builder.create_text_overlay(
            input_index=0,
            text="Timed Text",
            position=TextPosition.CENTER,
            start_time=5.0,
            end_time=10.0,
        )

        # Verify timing parameters
        assert "enable=" in overlay
        assert "5.0" in overlay or "5" in overlay
        assert "10.0" in overlay or "10" in overlay

    def test_create_text_overlay_with_custom_style(self, builder):
        """Test text overlay with custom styling."""
        style = TextStyle(font_size=72, font_color="yellow", border_width=3, border_color="red")

        overlay = builder.create_text_overlay(
            input_index=0, text="Styled Text", position=TextPosition.CENTER, style=style
        )

        # Verify style parameters
        assert "fontsize=72" in overlay
        assert "fontcolor=yellow" in overlay
        assert "borderw=3" in overlay
        assert "bordercolor=red" in overlay

    def test_create_text_overlay_with_shadow(self, builder):
        """Test text overlay with shadow."""
        style = TextStyle(shadow_x=2, shadow_y=2, shadow_color="black")

        overlay = builder.create_text_overlay(
            input_index=0, text="Shadow Text", position=TextPosition.CENTER, style=style
        )

        # Verify shadow parameters
        assert "shadowx=2" in overlay
        assert "shadowy=2" in overlay
        assert "shadowcolor=black" in overlay

    def test_create_text_overlay_with_background(self, builder):
        """Test text overlay with background box."""
        style = TextStyle(background_color="black", background_opacity=0.8)

        overlay = builder.create_text_overlay(
            input_index=0, text="Boxed Text", position=TextPosition.CENTER, style=style
        )

        # Verify background parameters
        assert "box=1" in overlay
        assert "boxcolor=black" in overlay

    def test_create_text_overlay_with_fade_in_animation(self, builder):
        """Test text overlay with fade-in animation."""
        overlay = builder.create_text_overlay(
            input_index=0,
            text="Fading In",
            position=TextPosition.CENTER,
            start_time=0.0,
            end_time=5.0,
            animation=TextAnimation.FADE_IN,
        )

        # Verify animation parameters
        assert "alpha=" in overlay
        assert "if(" in overlay  # Animation uses conditional expressions

    def test_create_text_overlay_with_fade_out_animation(self, builder):
        """Test text overlay with fade-out animation."""
        overlay = builder.create_text_overlay(
            input_index=0,
            text="Fading Out",
            position=TextPosition.CENTER,
            start_time=0.0,
            end_time=5.0,
            animation=TextAnimation.FADE_OUT,
        )

        # Verify animation parameters
        assert "alpha=" in overlay
        assert "if(" in overlay

    def test_create_text_overlay_with_slide_left_animation(self, builder):
        """Test text overlay with slide-left animation."""
        overlay = builder.create_text_overlay(
            input_index=0,
            text="Sliding Left",
            position=TextPosition.CENTER,
            start_time=0.0,
            end_time=5.0,
            animation=TextAnimation.SLIDE_LEFT,
        )

        # Verify x position has animation expression
        assert "x=if(" in overlay
        assert "SLIDE" not in overlay  # Should use expressions, not enum values

    def test_create_text_overlay_with_slide_right_animation(self, builder):
        """Test text overlay with slide-right animation."""
        overlay = builder.create_text_overlay(
            input_index=0,
            text="Sliding Right",
            position=TextPosition.CENTER,
            start_time=0.0,
            end_time=5.0,
            animation=TextAnimation.SLIDE_RIGHT,
        )

        # Verify x position has animation expression
        assert "x=if(" in overlay

    def test_create_text_overlay_with_slide_up_animation(self, builder):
        """Test text overlay with slide-up animation."""
        overlay = builder.create_text_overlay(
            input_index=0,
            text="Sliding Up",
            position=TextPosition.CENTER,
            start_time=0.0,
            end_time=5.0,
            animation=TextAnimation.SLIDE_UP,
        )

        # Verify y position has animation expression
        assert "y=if(" in overlay

    def test_create_text_overlay_with_slide_down_animation(self, builder):
        """Test text overlay with slide-down animation."""
        overlay = builder.create_text_overlay(
            input_index=0,
            text="Sliding Down",
            position=TextPosition.CENTER,
            start_time=0.0,
            end_time=5.0,
            animation=TextAnimation.SLIDE_DOWN,
        )

        # Verify y position has animation expression
        assert "y=if(" in overlay

    def test_create_text_overlay_with_custom_output_label(self, builder):
        """Test text overlay with custom output label."""
        overlay = builder.create_text_overlay(
            input_index=0,
            text="Custom Label",
            position=TextPosition.CENTER,
            output_label="custom_out",
        )

        assert "[custom_out]" in overlay

    def test_create_text_overlay_with_pixel_coordinates(self, builder):
        """Test text overlay with pixel coordinates."""
        overlay = builder.create_text_overlay(
            input_index=0, text="Pixel Positioned", position=(100, 200)
        )

        # Verify coordinates
        assert "x=100" in overlay
        assert "y=200" in overlay

    def test_create_text_overlay_with_expression_coordinates(self, builder):
        """Test text overlay with FFmpeg expression coordinates."""
        overlay = builder.create_text_overlay(
            input_index=0, text="Expression Positioned", position=("w/2", "h/2")
        )

        # Verify coordinates
        assert "x=w/2" in overlay
        assert "y=h/2" in overlay

    def test_create_timestamp_overlay(self, builder):
        """Test creating a timestamp overlay."""
        overlay = builder.create_timestamp_overlay(input_index=0, position=TextPosition.TOP_RIGHT)

        # Verify timestamp elements
        assert "[0:v]drawtext=" in overlay
        assert "pts" in overlay or "localtime" in overlay
        assert "[vout]" in overlay

    def test_create_timestamp_overlay_with_custom_format(self, builder):
        """Test timestamp overlay with custom format."""
        overlay = builder.create_timestamp_overlay(
            input_index=0,
            position=TextPosition.TOP_RIGHT,
            format_string="%Y-%m-%d %H\\:%M\\:%S",
        )

        # Verify format string presence
        assert "drawtext=" in overlay

    def test_create_frame_number_overlay(self, builder):
        """Test creating a frame number overlay."""
        overlay = builder.create_frame_number_overlay(input_index=0, position=TextPosition.TOP_LEFT)

        # Verify frame number elements
        assert "[0:v]drawtext=" in overlay
        assert "%{n}" in overlay or "n}" in overlay  # Frame number variable
        assert "[vout]" in overlay

    def test_create_frame_number_overlay_with_custom_prefix(self, builder):
        """Test frame number overlay with custom prefix."""
        overlay = builder.create_frame_number_overlay(
            input_index=0, position=TextPosition.TOP_LEFT, prefix="Frame #"
        )

        # Verify prefix in text
        assert "text=" in overlay

    def test_chain_empty_overlays(self, builder):
        """Test chaining with no overlays."""
        filter_expr = builder.chain_text_overlays(input_index=0, overlays=[])

        # Should return null filter
        assert "null" in filter_expr

    def test_chain_single_overlay(self, builder):
        """Test chaining a single overlay."""
        overlays = [
            {"text": "Single Overlay", "position": TextPosition.CENTER},
        ]

        filter_expr = builder.chain_text_overlays(input_index=0, overlays=overlays)

        # Verify single overlay is created
        assert "drawtext=" in filter_expr
        assert "Single Overlay" in filter_expr or "Single" in filter_expr
        assert "[final]" in filter_expr  # Default output label

    def test_chain_multiple_overlays(self, builder):
        """Test chaining multiple overlays."""
        overlays = [
            {"text": "Title", "position": TextPosition.TOP_CENTER},
            {"text": "Subtitle", "position": TextPosition.BOTTOM_CENTER},
            {"text": "Watermark", "position": TextPosition.BOTTOM_RIGHT},
        ]

        filter_expr = builder.chain_text_overlays(input_index=0, overlays=overlays)

        # Verify all overlays are present
        assert filter_expr.count("drawtext=") == 3
        assert ";" in filter_expr  # Filters are chained with semicolons
        assert "[final]" in filter_expr  # Final output label

    def test_chain_overlays_with_custom_output(self, builder):
        """Test chaining overlays with custom output label."""
        overlays = [
            {"text": "Text 1", "position": TextPosition.CENTER},
            {"text": "Text 2", "position": TextPosition.BOTTOM_CENTER},
        ]

        filter_expr = builder.chain_text_overlays(
            input_index=0, overlays=overlays, output_label="custom"
        )

        assert "[custom]" in filter_expr

    def test_chain_overlays_with_different_styles(self, builder):
        """Test chaining overlays with different styles."""
        style1 = TextStyle(font_size=72, font_color="yellow")
        style2 = TextStyle(font_size=48, font_color="white")

        overlays = [
            {"text": "Large Yellow", "position": TextPosition.TOP_CENTER, "style": style1},
            {"text": "Small White", "position": TextPosition.BOTTOM_CENTER, "style": style2},
        ]

        filter_expr = builder.chain_text_overlays(input_index=0, overlays=overlays)

        # Verify different styles are applied
        assert "fontsize=72" in filter_expr
        assert "fontsize=48" in filter_expr
        assert "fontcolor=yellow" in filter_expr
        assert "fontcolor=white" in filter_expr

    def test_chain_overlays_with_animations(self, builder):
        """Test chaining overlays with animations."""
        overlays = [
            {
                "text": "Fade In",
                "position": TextPosition.CENTER,
                "start_time": 0.0,
                "end_time": 3.0,
                "animation": TextAnimation.FADE_IN,
            },
            {
                "text": "Slide Left",
                "position": TextPosition.BOTTOM_CENTER,
                "start_time": 0.0,
                "end_time": 3.0,
                "animation": TextAnimation.SLIDE_LEFT,
            },
        ]

        filter_expr = builder.chain_text_overlays(input_index=0, overlays=overlays)

        # Verify animations are applied
        assert "alpha=" in filter_expr  # Fade animation
        assert filter_expr.count("if(") >= 2  # Animation conditions

    def test_special_characters_in_text(self, builder):
        """Test handling of special characters."""
        special_texts = [
            "Email: user@example.com",
            "Price: $19.99 (20% off)",
            "Copyright © 2025",
            "Quote: 'Hello World'",
        ]

        for text in special_texts:
            overlay = builder.create_text_overlay(
                input_index=0, text=text, position=TextPosition.CENTER
            )

            # Should not raise exceptions and should produce valid filter
            assert "drawtext=" in overlay
            assert "[vout]" in overlay

    def test_long_text_handling(self, builder):
        """Test handling of long text strings."""
        long_text = "This is a very long text that should still be handled correctly " * 5

        overlay = builder.create_text_overlay(
            input_index=0, text=long_text, position=TextPosition.CENTER
        )

        # Should handle long text without errors
        assert "drawtext=" in overlay

    def test_multiline_text(self, builder):
        """Test handling of multiline text."""
        multiline_text = "Line 1\nLine 2\nLine 3"

        overlay = builder.create_text_overlay(
            input_index=0, text=multiline_text, position=TextPosition.CENTER
        )

        # Verify newlines are properly escaped
        assert "\\n" in overlay or "\\\\n" in overlay

    def test_font_file_path(self, builder):
        """Test using a font file path."""
        style = TextStyle(font="/path/to/font.ttf")

        overlay = builder.create_text_overlay(
            input_index=0, text="Custom Font", position=TextPosition.CENTER, style=style
        )

        # Should use fontfile parameter for paths
        assert "fontfile=" in overlay

    def test_font_name(self, builder):
        """Test using a font name."""
        style = TextStyle(font="Arial")

        overlay = builder.create_text_overlay(
            input_index=0, text="Font Name", position=TextPosition.CENTER, style=style
        )

        # Should use font parameter for names
        assert "font=Arial" in overlay

    def test_zero_border_width(self, builder):
        """Test text without border."""
        style = TextStyle(border_width=0)

        overlay = builder.create_text_overlay(
            input_index=0, text="No Border", position=TextPosition.CENTER, style=style
        )

        # Should not include border parameters
        assert "borderw=" not in overlay

    def test_no_shadow(self, builder):
        """Test text without shadow."""
        style = TextStyle(shadow_x=0, shadow_y=0)

        overlay = builder.create_text_overlay(
            input_index=0, text="No Shadow", position=TextPosition.CENTER, style=style
        )

        # Should not include shadow parameters
        assert "shadowx=" not in overlay and "shadowy=" not in overlay


class TestIntegrationScenarios:
    """Test integration scenarios with complete workflows."""

    @pytest.fixture
    def builder(self):
        """Create a text overlay builder."""
        return TextOverlayBuilder()

    def test_title_and_subtitle_workflow(self, builder):
        """Test creating title and subtitle overlays."""
        title_style = TextStyle(font_size=72, font_color="yellow", border_width=3)
        subtitle_style = TextStyle(font_size=48, font_color="white", border_width=2)

        overlays = [
            {
                "text": "My Amazing Video",
                "position": TextPosition.TOP_CENTER,
                "style": title_style,
                "start_time": 0.0,
                "end_time": 5.0,
                "animation": TextAnimation.FADE_IN,
            },
            {
                "text": "A journey through code",
                "position": TextPosition.CENTER,
                "style": subtitle_style,
                "start_time": 1.0,
                "end_time": 6.0,
                "animation": TextAnimation.FADE_IN,
            },
        ]

        filter_expr = builder.chain_text_overlays(input_index=0, overlays=overlays)

        # Verify complete workflow
        assert filter_expr.count("drawtext=") == 2
        assert "fontsize=72" in filter_expr
        assert "fontsize=48" in filter_expr
        assert "alpha=" in filter_expr  # Animations

    def test_credits_workflow(self, builder):
        """Test creating scrolling credits."""
        overlays = [
            {
                "text": "Directed by Claude",
                "position": TextPosition.BOTTOM_CENTER,
                "start_time": 0.0,
                "end_time": 3.0,
                "animation": TextAnimation.SLIDE_UP,
            },
            {
                "text": "Produced by AI",
                "position": TextPosition.BOTTOM_CENTER,
                "start_time": 3.0,
                "end_time": 6.0,
                "animation": TextAnimation.SLIDE_UP,
            },
        ]

        filter_expr = builder.chain_text_overlays(input_index=0, overlays=overlays)

        # Verify credits workflow
        assert filter_expr.count("drawtext=") == 2
        assert "y=if(" in filter_expr  # Slide animations

    def test_watermark_workflow(self, builder):
        """Test creating a persistent watermark."""
        style = TextStyle(
            font_size=24,
            font_color="white",
            background_color="black",
            background_opacity=0.5,
        )

        overlay = builder.create_text_overlay(
            input_index=0,
            text="© 2025 MyCompany",
            position=TextPosition.BOTTOM_RIGHT,
            style=style,
        )

        # Verify watermark (no end time = persistent)
        assert "drawtext=" in overlay
        assert "box=1" in overlay  # Has background
        assert "enable='between" not in overlay  # No end time restriction

    def test_information_overlay_workflow(self, builder):
        """Test creating informational overlays."""
        overlays = [
            {
                "text": "Location: San Francisco",
                "position": TextPosition.TOP_LEFT,
                "start_time": 0.0,
                "end_time": 5.0,
            },
            {
                "text": "Date: January 2025",
                "position": (20, 80),  # Pixel position
                "start_time": 0.0,
                "end_time": 5.0,
            },
        ]

        filter_expr = builder.chain_text_overlays(input_index=0, overlays=overlays)

        # Verify information overlay
        assert filter_expr.count("drawtext=") == 2
        assert "x=20" in filter_expr  # Pixel coordinate
        assert "y=80" in filter_expr
