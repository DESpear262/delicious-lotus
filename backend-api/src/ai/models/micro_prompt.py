"""
Micro-Prompt Models - PR 301: Micro-Prompt Builder
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# Import harmony analysis for consistency enforcement
try:
    from .brand_harmony import BrandHarmonyAnalysis
except ImportError:
    # Handle circular import during initial development
    BrandHarmonyAnalysis = Any


class PromptPriority(str, Enum):
    """Priority level for micro-prompt elements"""
    CRITICAL = "critical"  # Must be included
    HIGH = "high"         # Should be included if possible
    MEDIUM = "medium"     # Nice to have
    LOW = "low"          # Optional


class PromptElement(BaseModel):
    """An element that should be included in the micro-prompt"""
    content: str = Field(..., description="The actual content to include")
    priority: PromptPriority = Field(..., description="How important this element is")
    category: str = Field(..., description="Category (narrative, visual, brand, technical, etc.)")
    source: str = Field(..., description="Where this element came from (scene, brand, style, etc.)")


class MicroPrompt(BaseModel):
    """
    A micro-prompt optimized for Replicate video generation models

    Each micro-prompt represents one scene/shot that will be generated
    as a video clip and later composed into the final video.
    """

    # Core identification
    scene_id: str = Field(..., description="ID of the scene this prompt is for")
    prompt_id: str = Field(..., description="Unique ID for this micro-prompt")

    # The actual prompt text for the model
    prompt_text: str = Field(..., description="Complete prompt text optimized for Replicate")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt to avoid unwanted elements")

    # Metadata about generation requirements
    estimated_duration: float = Field(..., gt=0.0, description="Expected duration in seconds")
    aspect_ratio: str = Field(default="16:9", description="Video aspect ratio")
    resolution: str = Field(default="1024x576", description="Target resolution")

    # Style and brand integration
    style_vector_score: float = Field(..., ge=0.0, le=1.0, description="Brand-style alignment score")
    brand_elements: List[str] = Field(default_factory=list, description="Brand elements explicitly included")

    # Quality and confidence metrics
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in prompt quality")
    generation_hints: Dict[str, Any] = Field(default_factory=dict, description="Model-specific generation hints")

    # Source tracking
    source_elements: List[PromptElement] = Field(..., description="Elements that contributed to this prompt")
    original_scene_data: Dict[str, Any] = Field(..., description="Original scene data for reference")

    def get_prompt_summary(self) -> str:
        """Get a human-readable summary of the prompt"""
        return f"Scene {self.scene_id}: {self.prompt_text[:100]}{'...' if len(self.prompt_text) > 100 else ''}"

    def validate_prompt_quality(self) -> Dict[str, Any]:
        """
        Validate prompt quality and return assessment

        Returns:
            Dict with validation results and recommendations
        """
        issues = []
        warnings = []

        # Check minimum requirements
        if len(self.prompt_text.split()) < 10:
            issues.append("Prompt too short (< 10 words)")

        if not any(word in self.prompt_text.lower() for word in ['video', 'scene', 'shot', 'clip']):
            warnings.append("No explicit video/scene terminology")

        # Check brand integration
        if self.style_vector_score < 0.6:
            warnings.append(f"Low brand-style alignment ({self.style_vector_score:.2f})")

        # Check technical specs
        if not self.aspect_ratio or not self.resolution:
            warnings.append("Missing technical specifications")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "overall_quality": "good" if len(issues) == 0 and len(warnings) == 0 else "fair" if len(issues) == 0 else "poor"
        }


class MicroPromptRequest(BaseModel):
    """Request to generate micro-prompts from scene decomposition"""

    generation_id: str = Field(..., description="ID of the generation job")

    # Input data from previous stages
    scenes: List[Dict[str, Any]] = Field(..., description="Scene decomposition results from PR 103")
    prompt_analysis: Dict[str, Any] = Field(..., description="Prompt analysis from PR 101")
    brand_config: Optional[Dict[str, Any]] = Field(None, description="Brand configuration from PR 102")
    brand_style_vector: Optional[Dict[str, Any]] = Field(None, description="Brand style vector from PR 102")
    brand_harmony_analysis: Optional[Dict[str, Any]] = Field(None, description="Brand harmony analysis from PR 502")

    # Generation parameters
    target_model: str = Field(default="google/veo-3.1-fast", description="Replicate model to target")
    max_prompt_length: int = Field(default=500, description="Maximum prompt length in characters")

    # Consistency enforcement settings
    enforce_accessibility: bool = Field(default=True, description="Enforce accessibility compliance in prompts")
    enforce_brand_consistency: bool = Field(default=True, description="Enforce brand consistency in prompts")
    harmony_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum harmony score required")


class MicroPromptResponse(BaseModel):
    """Response containing generated micro-prompts"""

    generation_id: str
    micro_prompts: List[MicroPrompt] = Field(..., description="Generated micro-prompts for each scene")

    # Metadata
    total_scenes: int = Field(..., description="Number of scenes processed")
    average_confidence: float = Field(..., description="Average confidence across all prompts")
    generation_time_ms: int = Field(..., description="Time taken to generate prompts")

    # Validation results
    validation_summary: Dict[str, Any] = Field(default_factory=dict, description="Overall validation results")


class PromptBuilderConfig(BaseModel):
    """Configuration for the micro-prompt builder"""

    # Model targeting
    target_model: str = Field(default="google/veo-3.1-fast")
    model_specific_templates: Dict[str, str] = Field(default_factory=dict)

    # Prompt construction
    max_prompt_length: int = Field(default=500)
    min_prompt_length: int = Field(default=50)
    include_negative_prompts: bool = Field(default=True)

    # Quality thresholds
    min_confidence_threshold: float = Field(default=0.7)
    min_style_alignment_threshold: float = Field(default=0.6)

    # Template components
    base_templates: Dict[str, str] = Field(default_factory=dict)
    brand_integration_templates: Dict[str, str] = Field(default_factory=dict)
