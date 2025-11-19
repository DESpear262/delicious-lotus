"""
Brand Harmony Models - PR #502: Brand Harmony Module
Models for analyzing color palette compatibility with brand style requirements.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field


class ConflictSeverity(str, Enum):
    """Severity levels for color harmony conflicts"""
    CRITICAL = "critical"  # Blocks accessibility/readability
    HIGH = "high"         # Significant usability issues
    MEDIUM = "medium"     # Noticeable but workable issues
    LOW = "low"          # Minor aesthetic concerns
    NONE = "none"        # No conflict


class ConflictType(str, Enum):
    """Types of conflicts that can be detected"""
    ACCESSIBILITY = "accessibility"           # WCAG compliance issues
    CONTRAST_RATIO = "contrast_ratio"         # Insufficient text/background contrast
    COLOR_BLINDNESS = "color_blindness"        # Issues for color-blind users
    TEMPERATURE_CLASH = "temperature_clash"   # Warm/cool color conflicts
    SATURATION_MISMATCH = "saturation_mismatch" # Too muted or too vibrant
    BRAND_DILUTION = "brand_dilution"         # Colors weaken brand recognition


class ColorHarmonyIssue(BaseModel):
    """A specific harmony issue or conflict detected"""
    conflict_type: ConflictType = Field(..., description="Type of conflict detected")
    severity: ConflictSeverity = Field(..., description="How serious the conflict is")
    description: str = Field(..., description="Human-readable description of the issue")
    affected_colors: List[str] = Field(..., description="Hex color codes involved in the conflict")
    wcag_level: Optional[str] = Field(None, description="WCAG compliance level affected (AA, AAA)")
    measured_value: Optional[float] = Field(None, description="Numerical measurement (contrast ratio, etc.)")
    recommended_threshold: Optional[float] = Field(None, description="Recommended minimum/maximum value")


class ColorCompatibility(BaseModel):
    """Compatibility analysis between two colors"""
    color_a: str = Field(..., description="First color (hex code)")
    color_b: str = Field(..., description="Second color (hex code)")
    contrast_ratio: float = Field(..., description="WCAG contrast ratio")
    temperature_difference: float = Field(..., description="Color temperature difference (0-1)")
    harmony_score: float = Field(..., ge=0.0, le=1.0, description="Overall harmony between colors (0-1)")
    recommended_usage: List[str] = Field(..., description="Recommended usage patterns")


class HarmonyRecommendation(BaseModel):
    """Specific recommendation for improving color harmony"""
    priority: str = Field(..., description="Priority level (critical, high, medium, low)")
    category: str = Field(..., description="Category (accessibility, contrast, branding, aesthetics)")
    action: str = Field(..., description="Recommended action to take")
    rationale: str = Field(..., description="Why this recommendation improves harmony")
    affected_elements: List[str] = Field(..., description="UI/video elements this affects")
    alternative_colors: Optional[List[str]] = Field(None, description="Suggested alternative colors")


class ColorPaletteAnalysis(BaseModel):
    """Comprehensive analysis of a brand color palette"""
    palette_name: str = Field(..., description="Name or identifier for this palette")

    # Color properties
    primary_colors: List[str] = Field(..., description="Primary brand colors")
    secondary_colors: Optional[List[str]] = Field(default=None, description="Secondary/accent colors")
    background_color: Optional[str] = Field(default=None, description="Background color")

    # Temperature analysis
    warm_cool_balance: float = Field(..., ge=0.0, le=1.0, description="Balance between warm/cool colors (0.5 = balanced)")
    average_temperature: float = Field(..., ge=0.0, le=1.0, description="Average color temperature (0=cool, 1=warm)")
    temperature_variance: float = Field(..., ge=0.0, le=1.0, description="How spread out temperatures are")

    # Accessibility metrics
    accessibility_score: float = Field(..., ge=0.0, le=1.0, description="Overall accessibility compliance (0-1)")
    wcag_aa_compliant: bool = Field(..., description="Meets WCAG AA standards")
    wcag_aaa_compliant: bool = Field(..., description="Meets WCAG AAA standards")

    # Color relationships
    color_compatibility_matrix: List[ColorCompatibility] = Field(..., description="Pairwise color compatibility analysis")


class BrandHarmonyAnalysis(BaseModel):
    """
    Comprehensive analysis of brand color harmony and style compatibility.

    This analysis combines a brand's color palette with style vector requirements
    to detect conflicts and provide actionable recommendations for visual consistency.
    """

    # Core identification
    brand_name: str = Field(..., description="Brand name for reference")
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    style_vector_id: str = Field(..., description="ID of the style vector analyzed")

    # Overall scores (weighted combination)
    overall_harmony_score: float = Field(..., ge=0.0, le=1.0, description="Overall brand-style harmony (0-1)")

    # Component scores (weighted inputs to overall score)
    accessibility_score: float = Field(..., ge=0.0, le=1.0, description="Accessibility compliance score")
    contrast_score: float = Field(..., ge=0.0, le=1.0, description="Color contrast quality score")
    temperature_harmony_score: float = Field(..., ge=0.0, le=1.0, description="Color temperature harmony score")
    brand_recognition_score: float = Field(..., ge=0.0, le=1.0, description="Brand recognition preservation score")

    # Detailed analysis results
    palette_analysis: ColorPaletteAnalysis = Field(..., description="Detailed palette analysis")
    detected_conflicts: List[ColorHarmonyIssue] = Field(default_factory=list, description="All conflicts detected")
    recommendations: List[HarmonyRecommendation] = Field(default_factory=list, description="Actionable recommendations")

    # Usage guidelines
    safe_color_combinations: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Safe color combinations for different use cases"
    )
    risk_color_combinations: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Risky color combinations to avoid"
    )

    # Metadata
    analysis_version: str = Field(default="1.0", description="Analysis algorithm version")
    created_at: str = Field(..., description="When analysis was performed")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in analysis accuracy")

    def get_critical_issues(self) -> List[ColorHarmonyIssue]:
        """Get all critical severity issues that should be addressed immediately"""
        return [issue for issue in self.detected_conflicts if issue.severity == ConflictSeverity.CRITICAL]

    def get_accessibility_issues(self) -> List[ColorHarmonyIssue]:
        """Get all accessibility-related issues"""
        return [issue for issue in self.detected_conflicts if issue.conflict_type == ConflictType.ACCESSIBILITY]

    def get_recommendations_by_priority(self, priority: str) -> List[HarmonyRecommendation]:
        """Get recommendations filtered by priority level"""
        return [rec for rec in self.recommendations if rec.priority == priority]

    def is_accessible(self) -> bool:
        """Check if the color palette meets basic accessibility standards"""
        return self.accessibility_score >= 0.8 and self.wcag_aa_compliant

    def get_harmony_summary(self) -> Dict[str, Any]:
        """Get a summary of the harmony analysis for quick reference"""
        return {
            "overall_score": self.overall_harmony_score,
            "critical_issues": len(self.get_critical_issues()),
            "accessibility_compliant": self.is_accessible(),
            "total_recommendations": len(self.recommendations),
            "high_priority_actions": len(self.get_recommendations_by_priority("critical"))
        }


# Utility functions for color analysis
def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def calculate_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance of RGB color (WCAG formula)"""
    # Convert to linear RGB
    rgb = [c / 255.0 for c in (r, g, b)]
    rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]

    # Calculate luminance
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two colors"""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)

    lum1 = calculate_luminance(r1, g1, b1)
    lum2 = calculate_luminance(r2, g2, b2)

    # Ensure lighter color is numerator
    lighter, darker = (lum1, lum2) if lum1 > lum2 else (lum2, lum1)

    return (lighter + 0.05) / (darker + 0.05)


def get_color_temperature(hex_color: str) -> float:
    """
    Estimate color temperature on a 0-1 scale
    0 = cool (blues), 1 = warm (reds/yellows)
    """
    r, g, b = hex_to_rgb(hex_color)

    # Simple temperature estimation based on RGB balance
    # Higher red/yellow = warmer, higher blue = cooler
    warmth = (r + g * 0.5) / (r + g + b + 1)  # Add 1 to avoid division by zero

    return min(1.0, max(0.0, warmth))


def is_wcag_aa_compliant(contrast_ratio: float, is_large_text: bool = False) -> bool:
    """Check if contrast ratio meets WCAG AA standards"""
    return contrast_ratio >= 4.5 if not is_large_text else contrast_ratio >= 3.0


def is_wcag_aaa_compliant(contrast_ratio: float, is_large_text: bool = False) -> bool:
    """Check if contrast ratio meets WCAG AAA standards"""
    return contrast_ratio >= 7.0 if not is_large_text else contrast_ratio >= 4.5
