"""
Text Overlay Builder for FFmpeg drawtext filter.

This module provides utilities for creating text overlays on videos with
advanced positioning, styling, animations, and special effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TextPosition(str, Enum):
    """Predefined text positions."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class TextAnimation(str, Enum):
    """Supported text animation types."""

    NONE = "none"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"


@dataclass
class TextStyle:
    """Text styling configuration.

    Attributes:
        font: Font family name or path to font file
        font_size: Font size in pixels
        font_color: Text color (name or hex code, e.g., "white" or "#FFFFFF")
        border_width: Border/outline width in pixels
        border_color: Border color
        shadow_x: Shadow X offset
        shadow_y: Shadow Y offset
        shadow_color: Shadow color
        background_color: Background box color (None for transparent)
        background_opacity: Background opacity (0.0 to 1.0)
    """

    font: str = "Sans"
    font_size: int = 48
    font_color: str = "white"
    border_width: int = 2
    border_color: str = "black"
    shadow_x: int = 0
    shadow_y: int = 0
    shadow_color: str = "black"
    background_color: str | None = None
    background_opacity: float = 0.7


class TextOverlayBuilder:
    """
    Builder for creating FFmpeg drawtext filter expressions.

    Provides high-level interface for adding text overlays to videos with
    positioning, styling, and animations.

    Example:
        >>> builder = TextOverlayBuilder()
        >>> overlay = builder.create_text_overlay(
        ...     text="Hello World",
        ...     position=TextPosition.CENTER,
        ...     start_time=0.0,
        ...     end_time=5.0,
        ...     style=TextStyle(font_size=72, font_color="yellow")
        ... )
    """

    def __init__(self) -> None:
        """Initialize the text overlay builder."""
        pass

    def _escape_text(self, text: str) -> str:
        """
        Escape special characters in text for FFmpeg drawtext filter.

        FFmpeg drawtext requires escaping of certain characters:
        - Single quotes must be replaced with '\\\''
        - Colons must be escaped as \\:
        - Newlines as \\n

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for drawtext filter
        """
        # Replace special characters
        text = text.replace("'", r"'\\\''")  # Escape single quotes
        text = text.replace(":", r"\\:")  # Escape colons
        text = text.replace("\n", r"\\n")  # Escape newlines
        text = text.replace("%", r"\\%")  # Escape percent signs

        return text

    def _position_to_coordinates(
        self,
        position: TextPosition,
        margin: int = 20,
    ) -> tuple[str, str]:
        """
        Convert position enum to FFmpeg x,y expressions.

        Args:
            position: Text position
            margin: Margin from edges in pixels

        Returns:
            Tuple of (x_expression, y_expression)
        """
        # FFmpeg expression variables:
        # w, h = video width/height
        # tw, th = text width/height
        # x, y = current position

        position_map = {
            TextPosition.TOP_LEFT: (str(margin), str(margin)),
            TextPosition.TOP_CENTER: ("(w-tw)/2", str(margin)),
            TextPosition.TOP_RIGHT: (f"w-tw-{margin}", str(margin)),
            TextPosition.CENTER_LEFT: (str(margin), "(h-th)/2"),
            TextPosition.CENTER: ("(w-tw)/2", "(h-th)/2"),
            TextPosition.CENTER_RIGHT: (f"w-tw-{margin}", "(h-th)/2"),
            TextPosition.BOTTOM_LEFT: (str(margin), f"h-th-{margin}"),
            TextPosition.BOTTOM_CENTER: ("(w-tw)/2", f"h-th-{margin}"),
            TextPosition.BOTTOM_RIGHT: (f"w-tw-{margin}", f"h-th-{margin}"),
        }

        return position_map.get(position, ("(w-tw)/2", "(h-th)/2"))

    def _build_animation_expression(
        self,
        animation: TextAnimation,
        start_time: float,
        end_time: float,
        base_x: str,
        base_y: str,
    ) -> tuple[tuple[str, str], str | None]:
        """
        Build animation expressions for x, y coordinates and alpha.

        Args:
            animation: Animation type
            start_time: Start time in seconds
            end_time: End time in seconds
            base_x: Base X expression
            base_y: Base Y expression

        Returns:
            Tuple of ((x_expression, y_expression), alpha_expression)
        """
        duration = end_time - start_time

        if animation == TextAnimation.FADE_IN:
            # Fade in over first 0.5 seconds
            fade_duration = min(0.5, duration / 4)
            alpha_expr = (
                f"if(lt(t,{start_time + fade_duration}),(t-{start_time})/{fade_duration},1)"
            )
            return (base_x, base_y), alpha_expr

        elif animation == TextAnimation.FADE_OUT:
            # Fade out over last 0.5 seconds
            fade_duration = min(0.5, duration / 4)
            fade_start = end_time - fade_duration
            alpha_expr = f"if(gt(t,{fade_start}),({end_time}-t)/{fade_duration},1)"
            return (base_x, base_y), alpha_expr

        elif animation == TextAnimation.SLIDE_LEFT:
            # Slide from right to left
            x_expr = f"if(lt(t,{start_time}),w,if(gt(t,{end_time}),{base_x},w-(w-({base_x}))*(t-{start_time})/{duration}))"
            return (x_expr, base_y), None

        elif animation == TextAnimation.SLIDE_RIGHT:
            # Slide from left to right
            x_expr = f"if(lt(t,{start_time}),-tw,if(gt(t,{end_time}),{base_x},-tw+({base_x}+tw)*(t-{start_time})/{duration}))"
            return (x_expr, base_y), None

        elif animation == TextAnimation.SLIDE_UP:
            # Slide from bottom to top
            y_expr = f"if(lt(t,{start_time}),h,if(gt(t,{end_time}),{base_y},h-(h-({base_y}))*(t-{start_time})/{duration}))"
            return (base_x, y_expr), None

        elif animation == TextAnimation.SLIDE_DOWN:
            # Slide from top to bottom
            y_expr = f"if(lt(t,{start_time}),-th,if(gt(t,{end_time}),{base_y},-th+({base_y}+th)*(t-{start_time})/{duration}))"
            return (base_x, y_expr), None

        # No animation
        return (base_x, base_y), None

    def create_text_overlay(  # noqa: C901
        self,
        input_index: int,
        text: str,
        position: TextPosition | tuple[int, int] | tuple[str, str] = TextPosition.CENTER,
        start_time: float = 0.0,
        end_time: float | None = None,
        style: TextStyle | None = None,
        animation: TextAnimation = TextAnimation.NONE,
        output_label: str | None = None,
    ) -> str:
        """
        Create a text overlay filter expression.

        Args:
            input_index: Input video index
            text: Text to display
            position: Position (enum, pixel coords, or FFmpeg expressions)
            start_time: When to show text (seconds)
            end_time: When to hide text (seconds, None = end of video)
            style: Text styling configuration
            animation: Animation type
            output_label: Optional output label

        Returns:
            FFmpeg drawtext filter expression

        Example:
            >>> overlay = builder.create_text_overlay(
            ...     input_index=0,
            ...     text="Hello",
            ...     position=TextPosition.CENTER,
            ...     style=TextStyle(font_size=72)
            ... )
        """
        if style is None:
            style = TextStyle()

        if output_label is None:
            output_label = "vout"

        # Escape text for FFmpeg
        escaped_text = self._escape_text(text)

        # Determine x, y coordinates
        if isinstance(position, TextPosition):
            x, y = self._position_to_coordinates(position)
        elif isinstance(position, tuple) and len(position) == 2:
            x, y = str(position[0]), str(position[1])
        else:
            x, y = "(w-tw)/2", "(h-th)/2"

        # Apply animation
        if animation != TextAnimation.NONE and end_time is not None:
            (x, y), alpha_expr = self._build_animation_expression(
                animation, start_time, end_time, x, y
            )
        else:
            alpha_expr = None

        # Build drawtext parameters
        params: list[str] = [
            f"text='{escaped_text}'",
            f"fontfile={style.font}" if "/" in style.font else f"font={style.font}",
            f"fontsize={style.font_size}",
            f"fontcolor={style.font_color}",
            f"x={x}",
            f"y={y}",
        ]

        # Border/outline
        if style.border_width > 0:
            params.append(f"borderw={style.border_width}")
            params.append(f"bordercolor={style.border_color}")

        # Shadow
        if style.shadow_x != 0 or style.shadow_y != 0:
            params.append(f"shadowx={style.shadow_x}")
            params.append(f"shadowy={style.shadow_y}")
            params.append(f"shadowcolor={style.shadow_color}")

        # Background box
        if style.background_color is not None:
            params.append("box=1")
            params.append(f"boxcolor={style.background_color}")
            # Convert opacity to hex alpha (0.0-1.0 to 00-FF)
            alpha_hex = format(int(style.background_opacity * 255), "02X")  # noqa: F841
            params.append("boxborderw=5")

        # Alpha animation
        if alpha_expr is not None:
            params.append(f"alpha='{alpha_expr}'")

        # Time enable/disable
        if end_time is not None:
            params.append(f"enable='between(t,{start_time},{end_time})'")
        elif start_time > 0:
            params.append(f"enable='gte(t,{start_time})'")

        # Build complete filter expression
        filter_expr = f"[{input_index}:v]drawtext={':'.join(params)}[{output_label}]"

        return filter_expr

    def create_timestamp_overlay(
        self,
        input_index: int,
        position: TextPosition = TextPosition.TOP_RIGHT,
        style: TextStyle | None = None,
        output_label: str | None = None,
        format_string: str = "%H\\:%M\\:%S",
    ) -> str:
        """
        Create a timestamp overlay showing current time.

        Args:
            input_index: Input video index
            position: Position on screen
            style: Text styling
            output_label: Optional output label
            format_string: Time format string (FFmpeg strftime format)

        Returns:
            FFmpeg drawtext filter expression
        """
        if style is None:
            style = TextStyle(font_size=32, font_color="white")

        if output_label is None:
            output_label = "vout"

        x, y = self._position_to_coordinates(position)

        params: list[str] = [
            f"text='%{{pts\\:localtime\\:{format_string}}}'",
            f"fontfile={style.font}" if "/" in style.font else f"font={style.font}",
            f"fontsize={style.font_size}",
            f"fontcolor={style.font_color}",
            f"x={x}",
            f"y={y}",
        ]

        if style.border_width > 0:
            params.append(f"borderw={style.border_width}")
            params.append(f"bordercolor={style.border_color}")

        filter_expr = f"[{input_index}:v]drawtext={':'.join(params)}[{output_label}]"

        return filter_expr

    def create_frame_number_overlay(
        self,
        input_index: int,
        position: TextPosition = TextPosition.TOP_LEFT,
        style: TextStyle | None = None,
        output_label: str | None = None,
        prefix: str = "Frame: ",
    ) -> str:
        """
        Create a frame number overlay.

        Args:
            input_index: Input video index
            position: Position on screen
            style: Text styling
            output_label: Optional output label
            prefix: Text prefix before frame number

        Returns:
            FFmpeg drawtext filter expression
        """
        if style is None:
            style = TextStyle(font_size=32, font_color="yellow")

        if output_label is None:
            output_label = "vout"

        escaped_prefix = self._escape_text(prefix)
        x, y = self._position_to_coordinates(position)

        params: list[str] = [
            f"text='{escaped_prefix}%{{n}}'",
            f"fontfile={style.font}" if "/" in style.font else f"font={style.font}",
            f"fontsize={style.font_size}",
            f"fontcolor={style.font_color}",
            f"x={x}",
            f"y={y}",
        ]

        if style.border_width > 0:
            params.append(f"borderw={style.border_width}")
            params.append(f"bordercolor={style.border_color}")

        filter_expr = f"[{input_index}:v]drawtext={':'.join(params)}[{output_label}]"

        return filter_expr

    def chain_text_overlays(
        self,
        input_index: int,
        overlays: list[dict[str, Any]],
        output_label: str = "final",
    ) -> str:
        """
        Chain multiple text overlays together.

        Args:
            input_index: Input video index
            overlays: List of overlay configurations (dicts with text, position, etc.)
            output_label: Final output label

        Returns:
            Chained filter expression

        Example:
            >>> overlays = [
            ...     {"text": "Title", "position": TextPosition.TOP_CENTER},
            ...     {"text": "Subtitle", "position": TextPosition.BOTTOM_CENTER},
            ... ]
            >>> filter_expr = builder.chain_text_overlays(0, overlays)
        """
        if not overlays:
            return f"[{input_index}:v]null[{output_label}]"

        filter_parts: list[str] = []
        current_input = input_index

        for i, overlay_config in enumerate(overlays):
            # Determine output label
            current_output = output_label if i == len(overlays) - 1 else f"v{i}"

            # Create overlay
            overlay_expr = self.create_text_overlay(
                input_index=current_input if i == 0 else -1,  # Use label after first
                output_label=current_output,
                **overlay_config,
            )

            # For subsequent overlays, replace input index with previous output label
            if i > 0:
                overlay_expr = overlay_expr.replace(f"[{current_input}:v]", f"[v{i-1}]", 1)

            filter_parts.append(overlay_expr)

        return ";".join(filter_parts)
