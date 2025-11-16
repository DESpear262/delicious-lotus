"""
Prompt Analysis Models - PR 101: Prompt Parsing Module
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class Tone(str, Enum):
    """Overall tone of the video content"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    ENTHUSIASTIC = "enthusiastic"
    SERIOUS = "serious"
    PLAYFUL = "playful"
    DRAMATIC = "dramatic"
    CALM = "calm"
    ENERGETIC = "energetic"


class Style(str, Enum):
    """Visual and narrative style"""
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMALIST = "minimalist"
    CINEMATIC = "cinematic"
    DOCUMENTARY = "documentary"
    ANIMATION = "animation"
    PHOTOREALISTIC = "photorealistic"
    ARTISTIC = "artistic"


class VisualTheme(str, Enum):
    """Overall visual theme and aesthetic"""
    BRIGHT = "bright"
    DARK = "dark"
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"
    VIBRANT = "vibrant"
    MONOCHROME = "monochrome"
    EARTHY = "earthy"


class NarrativeStructure(str, Enum):
    """How the story/content is structured"""
    PROBLEM_SOLUTION = "problem_solution"
    STORYTELLING = "storytelling"
    DEMONSTRATION = "demonstration"
    TESTIMONIAL = "testimonial"
    COMPARISON = "comparison"
    EXPLANATION = "explanation"
    CELEBRATION = "celebration"
    ANNOUNCEMENT = "announcement"


class TargetAudience(str, Enum):
    """Primary target audience"""
    BUSINESS = "business"
    CONSUMERS = "consumers"
    TEENS = "teens"
    PROFESSIONALS = "professionals"
    FAMILIES = "families"
    ELDERS = "elders"
    GENERAL = "general"


class ImageryStyle(str, Enum):
    """Specific imagery and visual elements"""
    PHOTOGRAPHY = "photography"
    ILLUSTRATION = "illustration"
    GRAPHICS = "graphics"
    TEXT_OVERLAYS = "text_overlays"
    PRODUCT_SHOTS = "product_shots"
    LIFESTYLE = "lifestyle"
    ABSTRACT = "abstract"
    REALISTIC = "realistic"


class KeyElement(BaseModel):
    """A key element extracted from the prompt"""
    element_type: str = Field(..., description="Type of element (product, person, location, etc.)")
    description: str = Field(..., description="Description of the element")
    importance: int = Field(..., ge=1, le=5, description="Importance level 1-5")


class ColorPalette(BaseModel):
    """Suggested color palette for consistency"""
    primary_colors: List[str] = Field(default_factory=list, description="Primary colors (hex codes)")
    secondary_colors: List[str] = Field(default_factory=list, description="Secondary colors (hex codes)")
    mood: str = Field(default="", description="Overall color mood/temperature")


class PromptAnalysis(BaseModel):
    """Comprehensive analysis of a video generation prompt"""

    # Core narrative elements
    tone: Tone = Field(..., description="Overall emotional tone of the video")
    style: Style = Field(..., description="Visual and narrative style approach")
    narrative_intent: str = Field(..., description="What the video is trying to achieve")
    narrative_structure: NarrativeStructure = Field(..., description="How the content is structured")

    # Thematic consistency elements
    target_audience: TargetAudience = Field(..., description="Primary audience for the content")
    key_themes: List[str] = Field(default_factory=list, description="Main themes to maintain throughout")
    key_messages: List[str] = Field(default_factory=list, description="Core messages to convey")

    # Visual consistency elements
    visual_theme: VisualTheme = Field(..., description="Overall visual aesthetic")
    imagery_style: ImageryStyle = Field(..., description="Type of visual elements to use")
    color_palette: ColorPalette = Field(default_factory=ColorPalette, description="Suggested color scheme")

    # Content elements
    key_elements: List[KeyElement] = Field(default_factory=list, description="Important elements to include")
    product_focus: Optional[str] = Field(None, description="Main product/service being featured")

    # Technical guidance
    pacing: str = Field(default="moderate", description="Suggested pacing (slow, moderate, fast)")
    music_style: str = Field(default="corporate", description="Recommended music style")

    # Quality indicators
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in analysis")
    analysis_notes: List[str] = Field(default_factory=list, description="Additional analysis notes")

    # Metadata
    original_prompt: str = Field(..., description="Original user prompt for reference")
    analysis_timestamp: str = Field(..., description="When analysis was performed")
    model_version: str = Field(..., description="AI model used for analysis")

    @validator('key_themes', 'key_messages', 'analysis_notes')
    def validate_list_length(cls, v):
        """Ensure lists aren't excessively long"""
        if len(v) > 10:
            raise ValueError("List cannot contain more than 10 items")
        return v

    @validator('key_elements')
    def validate_elements_length(cls, v):
        """Limit number of key elements"""
        if len(v) > 5:
            raise ValueError("Cannot have more than 5 key elements")
        return v


class AnalysisRequest(BaseModel):
    """Request model for prompt analysis"""
    prompt: str = Field(..., min_length=10, max_length=2000, description="User prompt to analyze")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for analysis")


class AnalysisResponse(BaseModel):
    """Response model for prompt analysis"""
    analysis: PromptAnalysis
    processing_time: float = Field(..., description="Time taken for analysis in seconds")
    status: str = Field(default="success", description="Analysis status")


class MockAnalysisResponse(BaseModel):
    """Mock response for testing without OpenAI calls"""
    analysis: PromptAnalysis
    is_mock: bool = Field(default=True, description="Indicates this is mock data")
    mock_reason: str = Field(default="testing", description="Reason for using mock data")
