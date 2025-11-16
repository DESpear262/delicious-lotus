"""
Micro-Prompt Builder Service - PR 301: Micro-Prompt Builder
"""

import uuid
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.micro_prompt import (
    MicroPrompt,
    MicroPromptRequest,
    MicroPromptResponse,
    PromptElement,
    PromptPriority,
    PromptBuilderConfig
)
from ..models.scene_decomposition import Scene
from ..models.brand_style_vector import BrandStyleVector
from ..models.brand_harmony import BrandHarmonyAnalysis


class MicroPromptBuilderService:
    """
    Service for building micro-prompts optimized for Replicate video generation

    Converts scene decomposition results into detailed, model-specific prompts
    that maintain narrative consistency and brand integrity.
    """

    def __init__(self, config: Optional[PromptBuilderConfig] = None):
        self.config = config or PromptBuilderConfig()

        # Initialize default templates for Replicate models
        self._setup_default_templates()

    def _setup_default_templates(self):
        """Setup default prompt templates for different models"""

        # Base templates for different scene types
        self.config.base_templates.update({
            "introduction": "Professional video introduction scene: {scene_description}. High-quality production, {visual_style}, {brand_tone}. {brand_elements}. Clear, engaging, {pacing} pacing.",
            "development": "Detailed product demonstration video: {scene_description}. {visual_style}, {technical_specs}. {brand_elements}. Professional cinematography, {lighting}, {camera_work}.",
            "climax": "Dramatic video climax: {scene_description}. Intense, engaging, {visual_style}. {brand_elements}. High production quality, {pacing} energy, {camera_work}.",
            "conclusion": "Professional video conclusion with call-to-action: {scene_description}. {visual_style}, {brand_elements}. Clear messaging, {pacing} close, compelling finish."
        })

        # Brand integration templates
        self.config.brand_integration_templates.update({
            "color_scheme": "using {brand_colors} color palette",
            "typography": "with {brand_typography} style text",
            "logo": "featuring {brand_logo} prominently",
            "tone": "in {brand_tone} tone",
            "assets": "incorporating {brand_assets}"
        })

        # Model-specific optimizations
        self.config.model_specific_templates.update({
            "google/veo-3.1-fast": {
                "resolution_hint": "high resolution, detailed, sharp focus",
                "motion_hint": "smooth motion, cinematic camera movement",
                "quality_hint": "professional quality, high production value"
            }
        })

    async def build_micro_prompts(self, request: MicroPromptRequest) -> MicroPromptResponse:
        """
        Build micro-prompts from scene decomposition results

        Args:
            request: Request containing scenes and analysis data

        Returns:
            Response with generated micro-prompts
        """
        start_time = time.time()

        # Convert scene dicts to Scene objects
        scenes = [Scene(**scene_data) for scene_data in request.scenes]

        # Parse brand style vector if provided
        brand_style_vector = None
        if request.brand_style_vector:
            brand_style_vector = BrandStyleVector(**request.brand_style_vector)

        # Parse brand harmony analysis if provided
        brand_harmony_analysis = None
        if request.brand_harmony_analysis:
            brand_harmony_analysis = BrandHarmonyAnalysis(**request.brand_harmony_analysis)

        # Generate micro-prompts for each scene
        micro_prompts = []
        total_confidence = 0.0

        for scene in scenes:
            prompt = await self._build_single_prompt(
                scene=scene,
                request=request,
                brand_style_vector=brand_style_vector,
                brand_harmony_analysis=brand_harmony_analysis
            )
            micro_prompts.append(prompt)
            total_confidence += prompt.confidence_score

        # Calculate response metrics
        average_confidence = total_confidence / len(micro_prompts) if micro_prompts else 0.0
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Validate all prompts
        validation_summary = self._validate_prompt_batch(micro_prompts)

        return MicroPromptResponse(
            generation_id=request.generation_id,
            micro_prompts=micro_prompts,
            total_scenes=len(scenes),
            average_confidence=average_confidence,
            generation_time_ms=generation_time_ms,
            validation_summary=validation_summary
        )

    async def _build_single_prompt(
        self,
        scene: Scene,
        request: MicroPromptRequest,
        brand_style_vector: Optional[BrandStyleVector],
        brand_harmony_analysis: Optional[BrandHarmonyAnalysis]
    ) -> MicroPrompt:
        """Build a single micro-prompt for one scene"""

        # Generate unique prompt ID
        prompt_id = f"mp_{uuid.uuid4().hex[:12]}"

        # Perform consistency enforcement checks
        consistency_warnings = self._check_consistency_requirements(
            request, brand_style_vector, brand_harmony_analysis
        )

        # Collect all prompt elements
        prompt_elements = []

        # 1. Core scene description
        core_description = self._build_core_description(scene, request.prompt_analysis)
        prompt_elements.append(PromptElement(
            content=core_description,
            priority=PromptPriority.CRITICAL,
            category="narrative",
            source="scene"
        ))

        # 2. Visual style elements
        visual_elements = self._build_visual_elements(scene)
        if visual_elements:
            prompt_elements.append(PromptElement(
                content=visual_elements,
                priority=PromptPriority.HIGH,
                category="visual",
                source="scene"
            ))

        # 3. Brand integration with consistency enforcement
        brand_elements = self._build_brand_elements(
            scene, request.brand_config, brand_style_vector, brand_harmony_analysis, request
        )
        if brand_elements:
            prompt_elements.append(PromptElement(
                content=brand_elements,
                priority=PromptPriority.HIGH,
                category="brand",
                source="brand_config"
            ))

        # 4. Technical specifications
        technical_specs = self._build_technical_specs(scene, brand_style_vector)
        if technical_specs:
            prompt_elements.append(PromptElement(
                content=technical_specs,
                priority=PromptPriority.MEDIUM,
                category="technical",
                source="requirements"
            ))

        # 5. Visual consistency anchors (from harmony analysis)
        if brand_harmony_analysis and request.enforce_brand_consistency:
            visual_anchors = self._build_visual_consistency_anchors(
                brand_harmony_analysis, request
            )
            if visual_anchors:
                prompt_elements.append(PromptElement(
                    content=visual_anchors,
                    priority=PromptPriority.CRITICAL if self._has_critical_accessibility_issues(brand_harmony_analysis) else PromptPriority.HIGH,
                    category="consistency",
                    source="harmony_analysis"
                ))

        # 6. Quality and style hints
        quality_hints = self._build_quality_hints(brand_style_vector)
        if quality_hints:
            prompt_elements.append(PromptElement(
                content=quality_hints,
                priority=PromptPriority.MEDIUM,
                category="quality",
                source="style_vector"
            ))

        # Assemble final prompt - safely handle both enum and string values
        scene_type_value = scene.scene_type.value if hasattr(scene.scene_type, 'value') else str(scene.scene_type)
        prompt_text = self._assemble_prompt_text(prompt_elements, scene_type_value)

        # Generate negative prompt if enabled
        negative_prompt = None
        if self.config.include_negative_prompts:
            negative_prompt = self._build_negative_prompt(scene, request.prompt_analysis)

        # Calculate confidence and style scores
        confidence_score = self._calculate_confidence_score(prompt_elements, brand_style_vector, brand_harmony_analysis)
        style_vector_score = brand_style_vector.overall_score if brand_style_vector else 0.7

        # Extract brand elements list
        brand_elements_list = []
        if request.brand_config:
            brand_elements_list = self._extract_brand_keywords(request.brand_config)

        return MicroPrompt(
            scene_id=scene.scene_id,
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            negative_prompt=negative_prompt,
            estimated_duration=scene.duration,
            aspect_ratio=getattr(request, 'aspect_ratio', '16:9'),
            resolution=getattr(request, 'resolution', '1024x576'),
            style_vector_score=style_vector_score,
            brand_elements=brand_elements_list,
            confidence_score=confidence_score,
            generation_hints=self._get_model_hints(),
            source_elements=prompt_elements,
            original_scene_data=scene.dict()
        )

    def _build_core_description(self, scene: Scene, prompt_analysis: Dict[str, Any]) -> str:
        """Build the core narrative description for the scene"""
        base_desc = scene.content_description

        # Enhance with prompt analysis insights
        tone = prompt_analysis.get('tone', 'professional')
        style = prompt_analysis.get('style', 'modern')

        # Add narrative context
        narrative_context = f" in {tone} {style} style"

        return f"{base_desc}{narrative_context}"

    def _build_visual_elements(self, scene: Scene) -> str:
        """Build visual style and camera elements"""
        elements = []

        # Visual style - safely handle both enum and string values
        if scene.visual_style:
            visual_style_value = scene.visual_style.value if hasattr(scene.visual_style, 'value') else str(scene.visual_style)
            elements.append(f"{visual_style_value} visual style")

        # Camera work
        if scene.camera_movement:
            elements.append(f"{scene.camera_movement} camera movement")

        # Pacing
        if scene.pacing:
            elements.append(f"{scene.pacing} pacing")

        return ", ".join(elements)

    def _build_brand_elements(
        self,
        scene: Scene,
        brand_config: Optional[Dict[str, Any]],
        brand_style_vector: Optional[BrandStyleVector]
    ) -> str:
        """Build brand integration elements"""
        if not brand_config:
            return ""

        elements = []

        # Colors
        colors = brand_config.get('colors', [])
        if colors:
            elements.append(f"using {', '.join(colors[:3])} color scheme")

        # Typography
        typography = brand_config.get('typography', {}).get('primary_font')
        if typography:
            elements.append(f"with {typography} typography style")

        # Logo placement
        logo_placement = scene.brand_references.logo_placement
        if logo_placement:
            elements.append(f"logo positioned {logo_placement}")

        # Brand tone from style vector
        if brand_style_vector:
            recommendations = brand_style_vector.get_recommendations()
            tone_hints = recommendations.get('strengths', [])
            if tone_hints:
                elements.append(f"maintaining {tone_hints[0].lower()}")

        return ", ".join(elements)

    def _build_technical_specs(
        self,
        scene: Scene,
        brand_style_vector: Optional[BrandStyleVector]
    ) -> str:
        """Build technical specifications for the model"""
        specs = []

        # Resolution and quality hints
        model_hints = self.config.model_specific_templates.get(self.config.target_model, {})
        if model_hints:
            specs.extend(model_hints.values())

        # Style vector quality recommendations
        if brand_style_vector and brand_style_vector.overall_score > 0.8:
            specs.append("premium quality, high production value")

        return ", ".join(specs)

    def _build_quality_hints(self, brand_style_vector: Optional[BrandStyleVector]) -> str:
        """Build quality and style hints based on brand analysis"""
        if not brand_style_vector:
            return "professional quality, high production value"

        recommendations = brand_style_vector.get_recommendations()

        hints = []
        if recommendations.get('overall_alignment') == 'excellent':
            hints.append("exceptional brand consistency")
        elif recommendations.get('overall_alignment') == 'good':
            hints.append("strong brand alignment")

        strengths = recommendations.get('strengths', [])
        if strengths:
            hints.append(strengths[0].lower())

        return ", ".join(hints)

    def _build_negative_prompt(self, scene: Scene, prompt_analysis: Dict[str, Any]) -> str:
        """Build negative prompt to avoid unwanted elements"""
        negative_elements = []

        # Generic quality negatives
        negative_elements.extend([
            "blurry", "low quality", "distorted", "pixelated",
            "poor lighting", "amateur", "unprofessional"
        ])

        # Scene-specific negatives - safely handle both enum and string values
        scene_type = scene.scene_type.value if hasattr(scene.scene_type, 'value') else str(scene.scene_type)
        if scene_type == "introduction":
            negative_elements.extend(["dark", "confusing", "boring"])
        elif scene_type == "development":
            negative_elements.extend(["static", "unengaging", "unclear"])

        # Brand-specific negatives (avoid generic/competitor brands)
        negative_elements.extend([
            "generic branding", "confusing logos", "poor brand representation"
        ])

        return ", ".join(set(negative_elements))  # Remove duplicates

    def _assemble_prompt_text(self, elements: List[PromptElement], scene_type: str) -> str:
        """Assemble all elements into the final prompt text"""
        # Start with base template
        base_template = self.config.base_templates.get(scene_type, self.config.base_templates["development"])

        # Extract content by priority
        critical_content = [e.content for e in elements if e.priority == PromptPriority.CRITICAL]
        high_content = [e.content for e in elements if e.priority == PromptPriority.HIGH]
        medium_content = [e.content for e in elements if e.priority == PromptPriority.MEDIUM]

        # Build the prompt
        prompt_parts = []

        # Add core content
        if critical_content:
            prompt_parts.extend(critical_content)

        # Add high-priority elements
        if high_content:
            prompt_parts.extend(high_content)

        # Add medium-priority elements if space allows
        combined_length = sum(len(part) for part in prompt_parts)
        for content in medium_content:
            if combined_length + len(content) + 20 < self.config.max_prompt_length:
                prompt_parts.append(content)
                combined_length += len(content)

        # Join and ensure length constraints
        final_prompt = ". ".join(prompt_parts)

        if len(final_prompt) > self.config.max_prompt_length:
            final_prompt = final_prompt[:self.config.max_prompt_length - 3] + "..."

        return final_prompt

    def _calculate_confidence_score(
        self,
        elements: List[PromptElement],
        brand_style_vector: Optional[BrandStyleVector]
    ) -> float:
        """Calculate confidence score for the generated prompt"""
        base_score = 0.7  # Base confidence

        # Boost for having critical elements
        critical_count = sum(1 for e in elements if e.priority == PromptPriority.CRITICAL)
        base_score += min(critical_count * 0.1, 0.2)

        # Boost for brand integration
        brand_elements = sum(1 for e in elements if e.category == "brand")
        base_score += min(brand_elements * 0.05, 0.1)

        # Style vector alignment
        if brand_style_vector:
            style_boost = brand_style_vector.overall_score * 0.1
            base_score += style_boost

        return min(base_score, 1.0)

    def _get_model_hints(self) -> Dict[str, Any]:
        """Get model-specific generation hints"""
        return self.config.model_specific_templates.get(self.config.target_model, {})

    def _extract_brand_keywords(self, brand_config: Dict[str, Any]) -> List[str]:
        """Extract brand-related keywords for tracking"""
        keywords = []

        if brand_config.get('name'):
            keywords.append(brand_config['name'])

        colors = brand_config.get('colors', [])
        keywords.extend(colors[:2])  # Limit to first 2 colors

        if brand_config.get('tagline'):
            keywords.append(brand_config['tagline'])

        return keywords

    def _validate_prompt_batch(self, prompts: List[MicroPrompt]) -> Dict[str, Any]:
        """Validate a batch of prompts and return summary"""
        if not prompts:
            return {"total_prompts": 0, "valid_prompts": 0, "issues": [], "warnings": []}

        validations = [p.validate_prompt_quality() for p in prompts]

        total_valid = sum(1 for v in validations if v['is_valid'])
        all_issues = []
        all_warnings = []

        for validation in validations:
            all_issues.extend(validation['issues'])
            all_warnings.extend(validation['warnings'])

        return {
            "total_prompts": len(prompts),
            "valid_prompts": total_valid,
            "validation_rate": total_valid / len(prompts),
            "total_issues": len(all_issues),
            "total_warnings": len(all_warnings),
            "common_issues": list(set(all_issues))[:5],  # Top 5 unique issues
            "common_warnings": list(set(all_warnings))[:5]  # Top 5 unique warnings
        }

    # ===== CONSISTENCY ENFORCEMENT METHODS =====

    def _check_consistency_requirements(
        self,
        request: MicroPromptRequest,
        brand_style_vector: Optional[BrandStyleVector],
        brand_harmony_analysis: Optional[BrandHarmonyAnalysis]
    ) -> List[str]:
        """
        Check consistency requirements and return warnings.

        Args:
            request: The micro-prompt request
            brand_style_vector: Brand style vector
            brand_harmony_analysis: Brand harmony analysis

        Returns:
            List of consistency warnings
        """
        warnings = []

        # Check harmony threshold
        if brand_harmony_analysis and request.harmony_threshold > 0:
            if brand_harmony_analysis.overall_harmony_score < request.harmony_threshold:
                warnings.append(
                    ".3f"
                )

        # Check for accessibility enforcement conflicts
        if request.enforce_accessibility and brand_harmony_analysis:
            if not brand_harmony_analysis.is_accessible():
                warnings.append("Accessibility enforcement enabled but harmony analysis shows accessibility issues")

        # Check for critical accessibility issues
        if brand_harmony_analysis and self._has_critical_accessibility_issues(brand_harmony_analysis):
            warnings.append("Critical accessibility issues detected - visual consistency may be limited")

        return warnings

    def _has_critical_accessibility_issues(self, harmony_analysis: BrandHarmonyAnalysis) -> bool:
        """Check if harmony analysis has critical accessibility issues"""
        critical_issues = harmony_analysis.get_critical_issues()
        return any(issue.conflict_type.value == "accessibility" for issue in critical_issues)

    def _build_brand_elements(
        self,
        scene: Scene,
        brand_config: Optional[Dict[str, Any]],
        brand_style_vector: Optional[BrandStyleVector],
        brand_harmony_analysis: Optional[BrandHarmonyAnalysis],
        request: MicroPromptRequest
    ) -> str:
        """Build brand integration elements with harmony awareness"""
        if not brand_config:
            return ""

        elements = []

        # Basic color integration (respecting harmony recommendations)
        colors = brand_config.get('colors', [])
        if colors and brand_harmony_analysis:
            # Use harmony-safe color combinations
            safe_combinations = brand_harmony_analysis.safe_color_combinations
            if safe_combinations.get('text_on_background'):
                # Suggest harmony-approved color usage
                elements.append("using brand-approved color combinations for visual consistency")
            else:
                # Fallback to basic colors but note potential issues
                elements.append(f"using {', '.join(colors[:2])} brand colors")
        elif colors:
            elements.append(f"using {', '.join(colors[:2])} brand colors")

        # Typography (no harmony conflicts typically)
        typography = brand_config.get('typography', {}).get('primary_font')
        if typography:
            elements.append(f"with {typography} typography style")

        # Logo placement (scene-specific)
        logo_placement = scene.brand_references.logo_placement
        if logo_placement:
            elements.append(f"logo positioned {logo_placement}")

        # Brand tone from style vector (enhanced with harmony context)
        if brand_style_vector:
            recommendations = brand_style_vector.get_recommendations()
            tone_hints = recommendations.get('strengths', [])

            # Add harmony-aware tone suggestions
            if brand_harmony_analysis and brand_harmony_analysis.overall_harmony_score > 0.8:
                tone_hints.append("visually cohesive brand presentation")

            if tone_hints:
                elements.append(f"maintaining {', '.join(tone_hints[:2])}")

        # Accessibility enforcement
        if request.enforce_accessibility and brand_harmony_analysis:
            if brand_harmony_analysis.wcag_aa_compliant:
                elements.append("ensuring WCAG AA accessibility compliance")
            elif brand_harmony_analysis.wcag_aaa_compliant:
                elements.append("ensuring WCAG AAA accessibility compliance")

        return "; ".join(elements)

    def _build_visual_consistency_anchors(
        self,
        brand_harmony_analysis: BrandHarmonyAnalysis,
        request: MicroPromptRequest
    ) -> str:
        """
        Build visual consistency anchors from harmony analysis.

        Args:
            brand_harmony_analysis: The harmony analysis results
            request: The micro-prompt request with consistency settings

        Returns:
            String with visual consistency instructions
        """
        anchors = []

        # Critical accessibility anchors
        if request.enforce_accessibility and self._has_critical_accessibility_issues(brand_harmony_analysis):
            anchors.append("PRIORITY: Ensure all text meets WCAG AA contrast requirements")
            anchors.append("Use only approved color combinations for text and backgrounds")

        # Safe color combination anchors
        safe_combinations = brand_harmony_analysis.safe_color_combinations
        if safe_combinations:
            if safe_combinations.get('text_on_background'):
                combinations = safe_combinations['text_on_background'][:2]  # Limit to avoid prompt bloat
                anchors.append(f"Use these approved color combinations: {', '.join(combinations)}")

        # Risk avoidance anchors
        risk_combinations = brand_harmony_analysis.risk_color_combinations
        if risk_combinations and risk_combinations.get('text_combinations'):
            anchors.append("Avoid these problematic color combinations for text readability")

        # Harmony score-based anchors
        harmony_score = brand_harmony_analysis.overall_harmony_score
        if harmony_score > 0.8:
            anchors.append("Maintain high visual consistency with established brand harmony")
        elif harmony_score > 0.6:
            anchors.append("Follow brand harmony guidelines for visual consistency")
        else:
            anchors.append("Use brand colors thoughtfully to maintain visual consistency")

        # Recommendation-based anchors
        recommendations = brand_harmony_analysis.recommendations
        critical_recs = [r for r in recommendations if r.priority == "critical"]
        if critical_recs:
            # Take the most important recommendation
            top_rec = critical_recs[0]
            anchors.append(f"CRITICAL: {top_rec.action}")

        return "; ".join(anchors)

    def _calculate_confidence_score(
        self,
        elements: List[PromptElement],
        brand_style_vector: Optional[BrandStyleVector],
        brand_harmony_analysis: Optional[BrandHarmonyAnalysis] = None
    ) -> float:
        """Calculate confidence score for the generated prompt with harmony awareness"""
        base_score = 0.7  # Base confidence

        # Boost for having critical elements
        critical_count = sum(1 for e in elements if e.priority == PromptPriority.CRITICAL)
        base_score += min(critical_count * 0.1, 0.2)

        # Boost for brand integration
        brand_elements = sum(1 for e in elements if e.category == "brand")
        base_score += min(brand_elements * 0.05, 0.1)

        # Style vector alignment
        if brand_style_vector:
            style_boost = brand_style_vector.overall_score * 0.1
            base_score += style_boost

        # Harmony analysis alignment
        if brand_harmony_analysis:
            harmony_boost = brand_harmony_analysis.overall_harmony_score * 0.05
            base_score += harmony_boost

            # Penalty for critical issues
            if self._has_critical_accessibility_issues(brand_harmony_analysis):
                base_score -= 0.1

        return min(max(base_score, 0.0), 1.0)
