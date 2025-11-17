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


def decompose_video_scenes(request: SceneDecompositionRequest) -> SceneDecompositionResponse:
    """
    Decompose a video prompt into individual scenes based on narrative structure.

    This is a rule-based scene decomposition for MVP, focusing on ads.
    Future versions could use AI for more sophisticated scene planning.

    Args:
        request: Scene decomposition request with video type, duration, and analysis

    Returns:
        SceneDecompositionResponse with ordered list of scenes
    """
    if request.video_type == "ad":
        return _decompose_ad_video(request)
    elif request.video_type == "music_video":
        return _decompose_music_video(request)
    else:
        raise ValueError(f"Unsupported video type: {request.video_type}")


def _decompose_ad_video(request: SceneDecompositionRequest) -> SceneDecompositionResponse:
    """Decompose an advertisement video into scenes using AD_SCENE_RULES"""

    scenes = []
    current_time = 0.0

    for rule in AD_SCENE_RULES:
        # Calculate duration for this scene
        duration = request.total_duration * rule.duration_percentage

        # Ensure minimum duration
        duration = max(duration, request.min_scene_duration)

        # Generate scene content based on rule and analysis
        scene_content = _generate_scene_content(rule, request, duration)

        # Create scene
        scene = Scene(
            scene_id=f"scene_{len(scenes) + 1}",
            scene_type=rule.scene_type,
            start_time=current_time,
            duration=duration,
            end_time=current_time + duration,
            title=_generate_scene_title(rule, request),
            content_description=scene_content,
            narrative_purpose=rule.description_template,
            visual_style=rule.visual_style_hint or VisualStyle.PRODUCT_SHOT,
            key_elements=_generate_key_elements(rule, request),
            brand_references=_generate_brand_references(request),
            pacing="medium"  # Default pacing
        )

        scenes.append(scene)
        current_time += duration

    # Validate that we haven't exceeded total duration
    total_scene_duration = sum(scene.duration for scene in scenes)
    if total_scene_duration > request.total_duration:
        # Scale down durations proportionally
        scale_factor = request.total_duration / total_scene_duration
        current_time = 0.0
        for scene in scenes:
            scene.duration *= scale_factor
            scene.start_time = current_time
            scene.end_time = current_time + scene.duration
            current_time += scene.duration

    return SceneDecompositionResponse(
        video_type=request.video_type,
        total_duration=request.total_duration,
        scenes=scenes,
        decomposition_method="rule_based_ad",
        average_scene_duration=sum(scene.duration for scene in scenes) / len(scenes),
        brand_consistency_score=_calculate_brand_consistency(request, scenes)
    )


def _decompose_music_video(request: SceneDecompositionRequest) -> SceneDecompositionResponse:
    """Placeholder for music video decomposition - not implemented in MVP"""
    raise NotImplementedError("Music video decomposition not implemented in MVP")


def _generate_scene_content(rule: SceneDistributionRule, request: SceneDecompositionRequest, duration: float) -> str:
    """Generate descriptive content for a scene based on the rule and analysis"""

    # Base content from rule template
    content = rule.description_template

    # Enhance with prompt analysis
    prompt_analysis = request.prompt_analysis
    if prompt_analysis:
        tone = prompt_analysis.get('tone', 'professional')
        style = prompt_analysis.get('style', 'modern')

        # Add tone and style context
        content += f" in a {tone} {style} manner"

        # Add key themes if available
        key_themes = prompt_analysis.get('key_themes', [])
        if key_themes and len(key_themes) > 0:
            content += f", emphasizing {', '.join(key_themes[:2])}"

    # Add duration-appropriate detail level
    if duration < 5.0:
        content += ". Keep it concise and impactful."
    elif duration > 10.0:
        content += ". Provide detailed demonstration and explanation."
    else:
        content += ". Balance detail with engagement."

    return content


def _generate_scene_title(rule: SceneDistributionRule, request: SceneDecompositionRequest) -> str:
    """Generate a brief title for the scene"""
    titles = {
        SceneType.INTRODUCTION: "Opening Hook",
        SceneType.DEVELOPMENT: "Main Demonstration",
        SceneType.CLIMAX: "Key Message",
        SceneType.CONCLUSION: "Call to Action"
    }

    base_title = titles.get(rule.scene_type, f"{rule.scene_type.value.title()} Scene")

    # Add brand context if available
    if request.brand_config and request.brand_config.get('name'):
        brand_name = request.brand_config['name']
        base_title += f" - {brand_name}"

    return base_title


def _generate_key_elements(rule: SceneDistributionRule, request: SceneDecompositionRequest) -> List[SceneElement]:
    """Generate key elements that should appear in the scene"""

    elements = []

    # Add product-focused elements for development scenes
    if rule.scene_type == SceneType.DEVELOPMENT:
        prompt_analysis = request.prompt_analysis
        if prompt_analysis and prompt_analysis.get('product_focus'):
            elements.append(SceneElement(
                element_type="product",
                description=f"Main product: {prompt_analysis.get('primary_product', 'featured product')}",
                importance=5,
                brand_relevance=5
            ))

        # Add supporting elements
        key_features = prompt_analysis.get('key_features', []) if prompt_analysis else []
        for i, feature in enumerate(key_features[:2]):
            elements.append(SceneElement(
                element_type="feature",
                description=f"Key feature: {feature}",
                importance=4,
                brand_relevance=3
            ))

    # Add CTA elements for conclusion scenes
    elif rule.scene_type == SceneType.CONCLUSION:
        elements.append(SceneElement(
            element_type="call_to_action",
            description="Clear call-to-action with contact information",
            importance=5,
            brand_relevance=4
        ))

    # Add brand elements for introduction
    elif rule.scene_type == SceneType.INTRODUCTION:
        if request.brand_config:
            elements.append(SceneElement(
                element_type="brand_identity",
                description=f"Brand introduction: {request.brand_config.get('name', 'brand')}",
                importance=5,
                brand_relevance=5
            ))

    return elements


def _generate_brand_references(request: SceneDecompositionRequest) -> BrandReference:
    """Generate brand references for the scene"""

    brand_ref = BrandReference()

    if not request.brand_config:
        return brand_ref

    config = request.brand_config

    # Colors
    colors = config.get('colors')
    # New BrandConfig format: colors is an object with primary/secondary/background
    if isinstance(colors, dict):
        flat_colors = []
        primary = colors.get('primary') or []
        secondary = colors.get('secondary') or []

        if isinstance(primary, list):
            flat_colors.extend(primary)
        elif primary:
            flat_colors.append(primary)

        if isinstance(secondary, list):
            flat_colors.extend(secondary)
        elif secondary:
            flat_colors.append(secondary)

        brand_ref.colors = flat_colors[:3]  # Limit to 3 colors
    # Backwards compatibility: support legacy list format
    elif isinstance(colors, list):
        brand_ref.colors = colors[:3]

    # Logo placement suggestions based on scene type
    # (This would be more sophisticated in a full implementation)
    brand_ref.logo_placement = "corner"  # Default safe placement

    # Typography
    typography = config.get('typography', {}).get('primary_font')
    if typography:
        brand_ref.typography_style = typography

    # Visual consistency notes
    if config.get('name'):
        brand_ref.visual_consistency = f"Maintain consistent visual identity for {config['name']}"

    return brand_ref


def _calculate_brand_consistency(request: SceneDecompositionRequest, scenes: List[Scene]) -> Optional[float]:
    """Calculate how well brand elements are distributed across scenes"""

    if not request.brand_config or not scenes:
        return None

    # Simple scoring based on brand element distribution
    total_scenes = len(scenes)
    scenes_with_brand_elements = sum(1 for scene in scenes if scene.key_elements)

    # Bonus for introduction and conclusion having brand elements
    intro_has_brand = any(e.brand_relevance and e.brand_relevance >= 4
                         for e in scenes[0].key_elements) if scenes else False
    conclusion_has_brand = any(e.brand_relevance and e.brand_relevance >= 4
                              for e in scenes[-1].key_elements) if len(scenes) > 1 else False

    base_score = scenes_with_brand_elements / total_scenes
    bonus_score = 0.2 if intro_has_brand else 0.0
    bonus_score += 0.2 if conclusion_has_brand else 0.0

    return min(base_score + bonus_score, 1.0)