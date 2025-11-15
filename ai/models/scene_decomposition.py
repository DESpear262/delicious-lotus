"""
Scene Decomposition Models - PR 103: Scene Decomposition (Ads & Music)
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class SceneType(str, Enum):
    """Types of scenes in a video narrative"""
    INTRODUCTION = "introduction"  # Opening hook, brand introduction
    DEVELOPMENT = "development"   # Main content, product demonstration
    CLIMAX = "climax"            # Peak moment, key message
    CONCLUSION = "conclusion"     # Wrap-up, reinforcement
    CTA = "cta"                  # Call-to-action, final push


class VisualStyle(str, Enum):
    """Visual style options for scenes"""
    PRODUCT_SHOT = "product_shot"
    LIFESTYLE = "lifestyle"
    GRAPHIC_OVERLAY = "graphic_overlay"
    TEXT_ANIMATION = "text_animation"
    BRAND_SHOWCASE = "brand_showcase"
    DEMONSTRATION = "demonstration"


class SceneElement(BaseModel):
    """A key element that should appear in a scene"""
    element_type: str = Field(..., description="Type of element (product, person, location, etc.)")
    description: str = Field(..., description="Detailed description of the element")
    importance: int = Field(..., ge=1, le=5, description="Importance level 1-5")
    brand_relevance: Optional[int] = Field(None, ge=0, le=5, description="How relevant to brand (0-5)")


class BrandReference(BaseModel):
    """Brand elements to include in the scene"""
    colors: List[str] = Field(default_factory=list, description="Brand colors to use (hex codes)")
    logo_placement: Optional[str] = Field(None, description="Where to place logo (corner, center, overlay, etc.)")
    typography_style: Optional[str] = Field(None, description="Typography style to use")
    visual_consistency: Optional[str] = Field(None, description="Consistency notes for this scene")


class Scene(BaseModel):
    """A single scene in the video"""
    scene_id: str = Field(..., description="Unique identifier for the scene")
    scene_type: SceneType = Field(..., description="Type of scene in narrative structure")
    start_time: float = Field(..., ge=0.0, description="Start time in seconds")
    duration: float = Field(..., gt=0.0, description="Duration in seconds")
    end_time: float = Field(..., gt=0.0, description="End time in seconds (calculated)")

    # Content
    title: str = Field(..., description="Brief title for the scene")
    content_description: str = Field(..., description="Detailed description of what happens in this scene")
    narrative_purpose: str = Field(..., description="Why this scene exists in the story")

    # Visual elements
    visual_style: VisualStyle = Field(..., description="Primary visual style for this scene")
    key_elements: List[SceneElement] = Field(default_factory=list, description="Key elements to include")
    brand_references: BrandReference = Field(default_factory=BrandReference, description="Brand elements to incorporate")

    # Technical hints
    camera_movement: Optional[str] = Field(None, description="Camera movement suggestions")
    pacing: str = Field(default="medium", description="Pacing: slow, medium, fast")
    transition_hint: Optional[str] = Field(None, description="Transition to next scene")

    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end_time equals start_time + duration"""
        if 'start_time' in values and 'duration' in values:
            expected_end = values['start_time'] + values['duration']
            if abs(v - expected_end) > 0.001:  # Small tolerance for floating point
                raise ValueError(f"end_time ({v}) must equal start_time + duration ({expected_end})")
        return v

    class Config:
        use_enum_values = True


class VideoType(str, Enum):
    """Type of video being decomposed"""
    AD = "ad"           # Commercial advertisement (15-60s)
    MUSIC_VIDEO = "music_video"  # Music video (60-180s)


class SceneDecompositionRequest(BaseModel):
    """Request to decompose a video into scenes"""
    video_type: VideoType = Field(..., description="Type of video to decompose")
    total_duration: int = Field(..., ge=15, le=180, description="Total video duration in seconds")

    # Analysis inputs
    prompt_analysis: Dict[str, Any] = Field(..., description="Structured prompt analysis from PR 101")
    brand_config: Optional[Dict[str, Any]] = Field(None, description="Brand configuration from PR 102")

    # Optional constraints
    min_scene_duration: float = Field(default=3.0, ge=1.0, description="Minimum scene duration in seconds")
    max_scenes: Optional[int] = Field(None, description="Maximum number of scenes to generate")


class SceneDecompositionResponse(BaseModel):
    """Response containing the decomposed scenes"""
    video_type: VideoType
    total_duration: int
    scenes: List[Scene] = Field(..., description="Ordered list of scenes")

    # Metadata
    decomposition_method: str = Field(..., description="Method used for decomposition (rule-based, ai-assisted, etc.)")
    average_scene_duration: float = Field(..., description="Average duration per scene")
    brand_consistency_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="How well brand elements are distributed")

    @validator('scenes')
    def validate_scene_sequence(cls, v):
        """Validate that scenes form a continuous, non-overlapping sequence"""
        if not v:
            return v

        # Check timing continuity
        expected_start = 0.0
        for i, scene in enumerate(v):
            if abs(scene.start_time - expected_start) > 0.001:
                raise ValueError(f"Scene {i} start_time ({scene.start_time}) doesn't match expected ({expected_start})")

            expected_start = scene.end_time

        # Check total duration coverage
        total_duration = sum(scene.duration for scene in v)
        if total_duration <= 0:
            raise ValueError("Total scene duration must be positive")

        return v


class SceneDistributionRule(BaseModel):
    """Rule for distributing content across scenes"""
    scene_type: SceneType
    duration_percentage: float = Field(..., ge=0.0, le=1.0, description="Percentage of total duration")
    content_priority: int = Field(..., ge=1, le=5, description="Priority for content assignment (1=lowest, 5=highest)")
    visual_style_hint: Optional[VisualStyle] = Field(None, description="Suggested visual style")
    description_template: str = Field(..., description="Template for scene description")


# Predefined rules for ads (MVP focus)
AD_SCENE_RULES = [
    SceneDistributionRule(
        scene_type=SceneType.INTRODUCTION,
        duration_percentage=0.20,  # 20% of total duration
        content_priority=4,
        visual_style_hint=VisualStyle.BRAND_SHOWCASE,
        description_template="Introduce the brand and hook the viewer with the main value proposition"
    ),
    SceneDistributionRule(
        scene_type=SceneType.DEVELOPMENT,
        duration_percentage=0.50,  # 50% of total duration
        content_priority=5,
        visual_style_hint=VisualStyle.PRODUCT_SHOT,
        description_template="Demonstrate the product/service and key benefits"
    ),
    SceneDistributionRule(
        scene_type=SceneType.CTA,
        duration_percentage=0.30,  # 30% of total duration
        content_priority=3,
        visual_style_hint=VisualStyle.TEXT_ANIMATION,
        description_template="Clear call-to-action with contact information and next steps"
    )
]


# Placeholder for music video rules (post-MVP)
MUSIC_VIDEO_SCENE_RULES = [
    SceneDistributionRule(
        scene_type=SceneType.INTRODUCTION,
        duration_percentage=0.15,
        content_priority=4,
        description_template="Opening scene setting the mood and introducing main themes"
    ),
    # Additional rules would be defined for music videos
]
