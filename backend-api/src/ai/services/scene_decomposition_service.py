"""
Scene Decomposition Service - PR 103: Scene Decomposition (Ads & Music)
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..models.scene_decomposition import (
    Scene,
    SceneType,
    VisualStyle,
    SceneElement,
    BrandReference,
    SceneDecompositionRequest,
    SceneDecompositionResponse,
    VideoType,
    AD_SCENE_RULES,
    MUSIC_VIDEO_SCENE_RULES
)
from ..models.prompt_analysis import PromptAnalysis, KeyElement
from ..models.brand_config import BrandConfig

logger = logging.getLogger(__name__)


class SceneDecompositionService:
    """Service for decomposing videos into structured scenes"""

    def __init__(self):
        """Initialize the scene decomposition service"""
        logger.info("SceneDecompositionService initialized")

    async def decompose_video(
        self,
        request: SceneDecompositionRequest
    ) -> SceneDecompositionResponse:
        """
        Decompose a video into structured scenes based on analysis and brand data

        Args:
            request: Decomposition request with analysis data

        Returns:
            Response containing ordered list of scenes
        """
        logger.info(f"Decomposing {request.video_type.value} video of {request.total_duration}s")

        if request.video_type == VideoType.AD:
            scenes = await self._decompose_ad(request)
        elif request.video_type == VideoType.MUSIC_VIDEO:
            scenes = await self._decompose_music_video(request)
        else:
            raise ValueError(f"Unsupported video type: {request.video_type}")

        # Calculate metadata
        total_scene_duration = sum(scene.duration for scene in scenes)
        avg_duration = total_scene_duration / len(scenes) if scenes else 0

        # Calculate brand consistency (placeholder - could be more sophisticated)
        brand_consistency = self._calculate_brand_consistency(scenes, request.brand_config)

        response = SceneDecompositionResponse(
            video_type=request.video_type,
            total_duration=request.total_duration,
            scenes=scenes,
            decomposition_method="rule-based",
            average_scene_duration=avg_duration,
            brand_consistency_score=brand_consistency
        )

        logger.info(f"Successfully decomposed into {len(scenes)} scenes")
        return response

    async def _decompose_ad(self, request: SceneDecompositionRequest) -> List[Scene]:
        """
        Decompose an advertisement into 3 scenes: Introduction, Development, CTA

        Args:
            request: Decomposition request

        Returns:
            List of scenes for the ad
        """
        logger.info("Decomposing advertisement into scenes")

        # Parse inputs
        prompt_analysis = self._parse_prompt_analysis(request.prompt_analysis)
        brand_config = self._parse_brand_config(request.brand_config)

        # Calculate scene durations based on rules
        scene_durations = self._calculate_ad_scene_durations(
            request.total_duration,
            request.min_scene_duration
        )

        # Create scenes
        scenes = []
        current_time = 0.0

        for rule in AD_SCENE_RULES:
            duration = scene_durations[rule.scene_type]
            if duration <= 0:
                continue

            scene = await self._create_ad_scene(
                scene_type=rule.scene_type,
                start_time=current_time,
                duration=duration,
                rule=rule,
                prompt_analysis=prompt_analysis,
                brand_config=brand_config,
                total_duration=request.total_duration
            )

            scenes.append(scene)
            current_time += duration

        # Validate total duration coverage
        total_scene_duration = sum(scene.duration for scene in scenes)
        if abs(total_scene_duration - request.total_duration) > 0.1:
            logger.warning(f"Scene duration mismatch: {total_scene_duration} vs {request.total_duration}")

        return scenes

    async def _decompose_music_video(self, request: SceneDecompositionRequest) -> List[Scene]:
        """
        Decompose a music video into multiple scenes (post-MVP)

        For now, returns a placeholder implementation
        """
        logger.info("Music video decomposition requested - using placeholder implementation")

        # Placeholder: equal distribution for MVP
        num_scenes = min(12, max(8, request.total_duration // 8))  # 8-12 scenes
        scene_duration = request.total_duration / num_scenes

        scenes = []
        current_time = 0.0

        for i in range(num_scenes):
            # Cycle through scene types
            scene_type = [
                SceneType.INTRODUCTION,
                SceneType.DEVELOPMENT,
                SceneType.CLIMAX,
                SceneType.CONCLUSION
            ][i % 4]

            scene = Scene(
                scene_id=f"scene_{i+1:02d}",
                scene_type=scene_type,
                start_time=current_time,
                duration=scene_duration,
                end_time=current_time + scene_duration,
                title=f"Scene {i+1}",
                content_description=f"Music video scene {i+1} - placeholder implementation",
                narrative_purpose=f"Part of the musical narrative - scene {i+1}",
                visual_style=VisualStyle.LIFESTYLE,
                key_elements=[],
                brand_references=BrandReference(),
                pacing="medium"
            )

            scenes.append(scene)
            current_time += scene_duration

        return scenes

    def _calculate_ad_scene_durations(
        self,
        total_duration: int,
        min_scene_duration: float
    ) -> Dict[SceneType, float]:
        """
        Calculate duration for each scene type in an ad

        Args:
            total_duration: Total video duration in seconds
            min_scene_duration: Minimum allowed scene duration

        Returns:
            Dictionary mapping scene types to durations
        """
        durations = {}

        for rule in AD_SCENE_RULES:
            calculated_duration = total_duration * rule.duration_percentage

            # Ensure minimum duration
            if calculated_duration < min_scene_duration:
                calculated_duration = min_scene_duration

            durations[rule.scene_type] = calculated_duration

        # Adjust to fit total duration (redistribute extra time)
        current_total = sum(durations.values())
        if abs(current_total - total_duration) > 0.1:
            # Simple redistribution - could be more sophisticated
            adjustment_factor = total_duration / current_total
            for scene_type in durations:
                durations[scene_type] *= adjustment_factor

        return durations

    async def _create_ad_scene(
        self,
        scene_type: SceneType,
        start_time: float,
        duration: float,
        rule: Any,  # SceneDistributionRule
        prompt_analysis: PromptAnalysis,
        brand_config: Optional[BrandConfig],
        total_duration: int
    ) -> Scene:
        """
        Create a single ad scene with content and branding

        Args:
            scene_type: Type of scene to create
            start_time: Start time in seconds
            duration: Duration in seconds
            rule: Distribution rule for this scene type
            prompt_analysis: Structured prompt analysis
            brand_config: Brand configuration
            total_duration: Total video duration

        Returns:
            Configured Scene object
        """
        scene_id = f"ad_{scene_type.value}_{uuid.uuid4().hex[:8]}"

        # Select appropriate key elements based on scene type and importance
        key_elements = self._select_scene_elements(scene_type, prompt_analysis)

        # Configure brand references
        brand_references = self._configure_brand_references(scene_type, brand_config)

        # Generate scene content
        title, description, purpose = self._generate_scene_content(
            scene_type, rule, prompt_analysis, key_elements
        )

        # Determine visual style
        visual_style = self._determine_visual_style(scene_type, rule, prompt_analysis)

        scene = Scene(
            scene_id=scene_id,
            scene_type=scene_type,
            start_time=start_time,
            duration=duration,
            end_time=start_time + duration,
            title=title,
            content_description=description,
            narrative_purpose=purpose,
            visual_style=visual_style,
            key_elements=key_elements,
            brand_references=brand_references,
            pacing=self._determine_pacing(scene_type, duration),
            transition_hint=self._suggest_transition(scene_type, total_duration, start_time + duration)
        )

        return scene

    def _select_scene_elements(
        self,
        scene_type: SceneType,
        prompt_analysis: PromptAnalysis
    ) -> List[SceneElement]:
        """
        Select which key elements should appear in this scene

        Args:
            scene_type: Type of scene
            prompt_analysis: Full prompt analysis

        Returns:
            List of scene elements for this scene
        """
        if not prompt_analysis.key_elements:
            return []

        elements = []

        # Priority mapping based on scene type
        priority_map = {
            SceneType.INTRODUCTION: [5, 4],  # High importance elements
            SceneType.DEVELOPMENT: [4, 3, 2],  # Medium importance
            SceneType.CLIMAX: [5, 4],  # Peak elements
            SceneType.CONCLUSION: [4, 3],  # Summary elements
            SceneType.CTA: [3, 2, 1]  # Lower priority, focus on action
        }

        target_priorities = priority_map.get(scene_type, [3, 2])
        max_elements = 2 if scene_type == SceneType.INTRODUCTION else 3

        for element in prompt_analysis.key_elements:
            if element.importance in target_priorities:
                scene_element = SceneElement(
                    element_type=element.element_type,
                    description=element.description,
                    importance=element.importance,
                    brand_relevance=None  # Could be calculated based on brand analysis
                )
                elements.append(scene_element)

                if len(elements) >= max_elements:
                    break

        return elements

    def _configure_brand_references(
        self,
        scene_type: SceneType,
        brand_config: Optional[BrandConfig]
    ) -> BrandReference:
        """
        Configure brand elements for this scene

        Args:
            scene_type: Type of scene
            brand_config: Brand configuration

        Returns:
            BrandReference object
        """
        if not brand_config:
            return BrandReference()

        # Select colors based on scene type
        colors = []
        if brand_config.color_palette.primary:
            if scene_type == SceneType.INTRODUCTION:
                colors = brand_config.color_palette.primary[:2]  # Primary colors for intro
            elif scene_type == SceneType.CTA:
                colors = brand_config.color_palette.primary[-2:]  # Accent colors for CTA
            else:
                colors = brand_config.color_palette.primary[:3]  # Mix for development

        # Logo placement hints
        logo_placement = None
        if scene_type == SceneType.INTRODUCTION:
            logo_placement = "center_overlay"
        elif scene_type == SceneType.CTA:
            logo_placement = "bottom_right"

        return BrandReference(
            colors=colors,
            logo_placement=logo_placement,
            typography_style=getattr(brand_config.typography, 'primary_font', None),
            visual_consistency=f"Maintain {brand_config.category.value} brand aesthetic"
        )

    def _generate_scene_content(
        self,
        scene_type: SceneType,
        rule: Any,  # SceneDistributionRule
        prompt_analysis: PromptAnalysis,
        key_elements: List[SceneElement]
    ) -> Tuple[str, str, str]:
        """
        Generate title, description, and purpose for the scene

        Returns:
            Tuple of (title, description, purpose)
        """
        base_title = {
            SceneType.INTRODUCTION: "Opening Hook",
            SceneType.DEVELOPMENT: "Main Content",
            SceneType.CLIMAX: "Key Moment",
            SceneType.CONCLUSION: "Summary",
            SceneType.CTA: "Call to Action"
        }.get(scene_type, "Scene")

        # Build description incorporating key elements
        element_descriptions = []
        for element in key_elements:
            element_descriptions.append(f"{element.element_type}: {element.description}")

        if element_descriptions:
            description = f"{rule.description_template}. Featuring: {', '.join(element_descriptions[:2])}"
        else:
            description = rule.description_template

        # Add tone and style context
        if prompt_analysis.tone:
            description += f" Presented in a {prompt_analysis.tone.value} tone."

        purpose = f"Advance the {prompt_analysis.narrative_structure.value} narrative structure"

        return base_title, description, purpose

    def _determine_visual_style(
        self,
        scene_type: SceneType,
        rule: Any,  # SceneDistributionRule
        prompt_analysis: PromptAnalysis
    ) -> VisualStyle:
        """
        Determine the visual style for this scene
        """
        # Start with rule hint
        if rule.visual_style_hint:
            return rule.visual_style_hint

        # Fallback based on scene type and prompt analysis
        style_map = {
            SceneType.INTRODUCTION: VisualStyle.BRAND_SHOWCASE,
            SceneType.DEVELOPMENT: VisualStyle.PRODUCT_SHOT,
            SceneType.CLIMAX: VisualStyle.LIFESTYLE,
            SceneType.CONCLUSION: VisualStyle.DEMONSTRATION,
            SceneType.CTA: VisualStyle.TEXT_ANIMATION
        }

        return style_map.get(scene_type, VisualStyle.PRODUCT_SHOT)

    def _determine_pacing(self, scene_type: SceneType, duration: float) -> str:
        """
        Determine pacing for the scene based on type and duration
        """
        if scene_type == SceneType.CLIMAX:
            return "fast"
        elif scene_type == SceneType.INTRODUCTION and duration < 5:
            return "fast"
        elif duration > 10:
            return "slow"
        else:
            return "medium"

    def _suggest_transition(self, scene_type: SceneType, total_duration: int, end_time: float) -> Optional[str]:
        """
        Suggest transition to next scene
        """
        if end_time >= total_duration:
            return None  # Last scene

        if scene_type == SceneType.INTRODUCTION:
            return "fade_to_demonstration"
        elif scene_type == SceneType.DEVELOPMENT:
            return "cut_to_cta"
        else:
            return "smooth_transition"

    def _calculate_brand_consistency(
        self,
        scenes: List[Scene],
        brand_config: Optional[Dict[str, Any]]
    ) -> Optional[float]:
        """
        Calculate how well brand elements are distributed across scenes
        """
        if not brand_config or not scenes:
            return None

        # Simple scoring: check if each scene has brand references
        scenes_with_brand = sum(1 for scene in scenes if scene.brand_references.colors)
        return scenes_with_brand / len(scenes)

    def _parse_prompt_analysis(self, analysis_data: Dict[str, Any]) -> PromptAnalysis:
        """
        Parse prompt analysis data into PromptAnalysis object
        """
        # This would normally deserialize from the analysis service
        # For now, create a basic object
        return PromptAnalysis(
            tone=analysis_data.get('tone', 'professional'),
            style=analysis_data.get('style', 'modern'),
            narrative_structure=analysis_data.get('narrative_structure', 'problem_solution'),
            target_audience=analysis_data.get('target_audience', 'general'),
            key_elements=analysis_data.get('key_elements', []),
            visual_themes=analysis_data.get('visual_themes', []),
            color_palette=analysis_data.get('color_palette', {}),
            imagery_styles=analysis_data.get('imagery_styles', []),
            brand_alignment_score=analysis_data.get('brand_alignment_score', 0.5)
        )

    def _parse_brand_config(self, brand_data: Optional[Dict[str, Any]]) -> Optional[BrandConfig]:
        """
        Parse brand configuration data
        """
        if not brand_data:
            return None

        # This would normally deserialize from the brand service
        # For now, return None to avoid complexity
        return None
