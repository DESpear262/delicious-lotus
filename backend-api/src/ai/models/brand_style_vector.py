"""
Brand Style Vector Models - PR 102: Brand & Metadata Extraction Layer
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class StyleDimensions(BaseModel):
    """Individual style dimension weights (0.0 to 1.0 scale)"""

    # Brand adherence dimensions
    brand_recognition: float = Field(..., ge=0.0, le=1.0, description="How recognizable the brand remains (0-1)")
    brand_consistency: float = Field(..., ge=0.0, le=1.0, description="Consistency with brand guidelines (0-1)")

    # Visual style dimensions
    color_harmony: float = Field(..., ge=0.0, le=1.0, description="Harmony between brand colors and content (0-1)")
    visual_appeal: float = Field(..., ge=0.0, le=1.0, description="Overall visual appeal of the combination (0-1)")
    tone_alignment: float = Field(..., ge=0.0, le=1.0, description="Alignment between brand tone and content tone (0-1)")

    # Content adaptation dimensions
    adaptability: float = Field(..., ge=0.0, le=1.0, description="How well brand adapts to content requirements (0-1)")
    creativity: float = Field(..., ge=0.0, le=1.0, description="Creative flexibility while maintaining brand integrity (0-1)")

    # Audience alignment
    audience_fit: float = Field(..., ge=0.0, le=1.0, description="How well the combination fits target audience (0-1)")


class BrandStyleVector(BaseModel):
    """
    Numerical representation of brand-style alignment for video generation

    This vector serves as a "style placeholder" that can be used by downstream
    services (clip generation, composition, etc.) to maintain brand consistency
    across the entire video generation pipeline.
    """

    # Core vector components
    dimensions: StyleDimensions = Field(..., description="Weighted style dimensions")

    # Metadata about the vector generation
    brand_name: str = Field(..., description="Brand name for reference")
    content_description: str = Field(..., description="Brief description of content being generated")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in vector accuracy")

    # Original analysis data for debugging/transparency
    original_brand_config: Dict[str, Any] = Field(..., description="Original brand configuration used")
    prompt_analysis_summary: Dict[str, Any] = Field(..., description="Key insights from prompt analysis")

    # Generation metadata
    version: str = Field(default="1.0", description="Vector format version")
    generated_at: str = Field(..., description="When vector was generated")
    generation_method: str = Field(..., description="How vector was generated (ai_analysis, default, manual)")

    @property
    def overall_score(self) -> float:
        """
        Calculate overall style alignment score from all dimensions

        Returns:
            Weighted average of all dimension scores (0.0 to 1.0)
        """
        dims = self.dimensions
        weights = {
            'brand_recognition': 0.25,    # Most important
            'brand_consistency': 0.20,
            'color_harmony': 0.15,
            'tone_alignment': 0.15,
            'visual_appeal': 0.10,
            'adaptability': 0.08,
            'creativity': 0.05,
            'audience_fit': 0.02
        }

        weighted_sum = sum(
            getattr(dims, dim) * weight
            for dim, weight in weights.items()
        )

        return round(weighted_sum, 3)

    def to_feature_vector(self) -> List[float]:
        """
        Convert to a simple numerical vector for ML models

        Returns:
            List of float values representing the style vector
        """
        dims = self.dimensions
        return [
            dims.brand_recognition,
            dims.brand_consistency,
            dims.color_harmony,
            dims.visual_appeal,
            dims.tone_alignment,
            dims.adaptability,
            dims.creativity,
            dims.audience_fit,
            self.confidence_score,
            self.overall_score
        ]

    def get_recommendations(self) -> Dict[str, Any]:
        """
        Get human-readable recommendations based on the vector

        Returns:
            Dictionary with recommendations for content generation
        """
        score = self.overall_score
        dims = self.dimensions

        recommendations = {
            "overall_alignment": "excellent" if score > 0.8 else "good" if score > 0.6 else "needs_improvement",
            "strengths": [],
            "improvements": [],
            "risks": []
        }

        # Analyze strengths
        if dims.brand_recognition > 0.8:
            recommendations["strengths"].append("Strong brand recognition maintained")
        if dims.color_harmony > 0.8:
            recommendations["strengths"].append("Excellent color harmony")
        if dims.tone_alignment > 0.8:
            recommendations["strengths"].append("Perfect tone alignment")

        # Analyze improvements needed
        if dims.brand_consistency < 0.6:
            recommendations["improvements"].append("Improve brand consistency")
        if dims.adaptability < 0.6:
            recommendations["improvements"].append("Increase brand adaptability to content")
        if dims.audience_fit < 0.6:
            recommendations["improvements"].append("Better align with target audience")

        # Risk assessment
        if dims.brand_recognition < 0.5:
            recommendations["risks"].append("Risk of brand dilution")
        if dims.creativity < 0.3:
            recommendations["risks"].append("Content may feel too rigid/stiff")

        return recommendations


# Default style vectors for common scenarios
DEFAULT_STYLE_VECTORS = {
    "perfect_brand_alignment": {
        "dimensions": {
            "brand_recognition": 0.95,
            "brand_consistency": 0.90,
            "color_harmony": 0.85,
            "visual_appeal": 0.88,
            "tone_alignment": 0.92,
            "adaptability": 0.80,
            "creativity": 0.75,
            "audience_fit": 0.85
        }
    },

    "good_brand_adaptation": {
        "dimensions": {
            "brand_recognition": 0.85,
            "brand_consistency": 0.75,
            "color_harmony": 0.80,
            "visual_appeal": 0.82,
            "tone_alignment": 0.78,
            "adaptability": 0.85,
            "creativity": 0.80,
            "audience_fit": 0.82
        }
    },

    "minimal_brand_presence": {
        "dimensions": {
            "brand_recognition": 0.60,
            "brand_consistency": 0.50,
            "color_harmony": 0.65,
            "visual_appeal": 0.70,
            "tone_alignment": 0.55,
            "adaptability": 0.90,
            "creativity": 0.85,
            "audience_fit": 0.75
        }
    }
}


def create_default_style_vector(scenario: str = "good_brand_adaptation") -> BrandStyleVector:
    """
    Create a default style vector for testing or when analysis fails

    Args:
        scenario: Type of default vector to create

    Returns:
        BrandStyleVector with default values
    """
    import datetime

    vector_data = DEFAULT_STYLE_VECTORS.get(scenario, DEFAULT_STYLE_VECTORS["good_brand_adaptation"])
    vector_data.update({
        "brand_name": "Default Brand",
        "content_description": "Default video content",
        "confidence_score": 0.7,
        "original_brand_config": {},
        "prompt_analysis_summary": {},
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "generation_method": "default"
    })

    return BrandStyleVector(**vector_data)
