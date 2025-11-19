"""
Style Vector Builder Service - PR #501: Style Vector Builder
Derives style vectors from brand configuration and prompt analysis for visual consistency.
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from ..models.brand_config import BrandConfig
from ..models.prompt_analysis import PromptAnalysis
from ..models.brand_style_vector import (
    BrandStyleVector,
    StyleDimensions,
    create_default_style_vector
)

logger = logging.getLogger(__name__)


class StyleVectorBuilderService:
    """
    Service for building brand style vectors from brand configuration and prompt analysis.

    This service normalizes brand characteristics and content requirements into
    numerical style dimensions that can be used for visual consistency across
    video generation pipelines.
    """

    def __init__(self, redis_client=None, use_mock: bool = False):
        """
        Initialize the style vector builder service.

        Args:
            redis_client: Optional Redis client for caching
            use_mock: Whether to use mock responses for testing
        """
        self.redis_client = redis_client
        self.use_mock = use_mock
        self.cache_ttl = 3600  # 1 hour cache TTL

    async def build_style_vector(
        self,
        brand_config: BrandConfig,
        prompt_analysis: PromptAnalysis,
        cache_key: Optional[str] = None
    ) -> BrandStyleVector:
        """
        Build a brand style vector from brand configuration and prompt analysis.

        Args:
            brand_config: Complete brand configuration
            prompt_analysis: Analyzed prompt data
            cache_key: Optional cache key for storing/retrieving the vector

        Returns:
            BrandStyleVector: Computed style vector for visual consistency
        """
        try:
            # Check cache first if available
            if cache_key and self.redis_client and not self.use_mock:
                cached_vector = await self._get_cached_vector(cache_key)
                if cached_vector:
                    logger.info(f"Retrieved style vector from cache: {cache_key}")
                    return cached_vector

            # Compute style vector
            style_vector = await self._compute_style_vector(brand_config, prompt_analysis)

            # Cache the result
            if cache_key and self.redis_client and not self.use_mock:
                await self._cache_vector(cache_key, style_vector)

            logger.info(f"Built style vector for brand: {brand_config.name}")
            return style_vector

        except Exception as e:
            logger.error(f"Failed to build style vector: {str(e)}")
            # Always return a default vector, never fail
            return self._create_fallback_vector(brand_config, prompt_analysis)

    async def _compute_style_vector(
        self,
        brand_config: BrandConfig,
        prompt_analysis: PromptAnalysis
    ) -> BrandStyleVector:
        """
        Compute style vector dimensions from brand config and prompt analysis.

        Args:
            brand_config: Brand configuration
            prompt_analysis: Prompt analysis results

        Returns:
            BrandStyleVector: Computed vector
        """
        # Extract base dimensions from brand config
        base_dimensions = self._extract_brand_dimensions(brand_config)

        # Adjust dimensions based on prompt analysis
        adjusted_dimensions = self._adjust_for_prompt(base_dimensions, prompt_analysis)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(brand_config, prompt_analysis)

        # Create style vector
        style_vector = BrandStyleVector(
            dimensions=adjusted_dimensions,
            brand_name=brand_config.name,
            content_description=prompt_analysis.primary_intent or "Video content",
            confidence_score=confidence_score,
            original_brand_config=brand_config.dict(),
            prompt_analysis_summary=self._summarize_prompt_analysis(prompt_analysis),
            generated_at=datetime.utcnow().isoformat() + "Z",
            generation_method="computed"
        )

        return style_vector

    def _extract_brand_dimensions(self, brand_config: BrandConfig) -> StyleDimensions:
        """
        Extract base style dimensions from brand configuration.

        Args:
            brand_config: Brand configuration

        Returns:
            StyleDimensions: Base dimensions from brand config
        """
        # Brand recognition - how distinctive/recognizable the brand is
        brand_recognition = self._calculate_brand_recognition(brand_config)

        # Brand consistency - how well the config defines consistent guidelines
        brand_consistency = self._calculate_brand_consistency(brand_config)

        # Color harmony - quality and coherence of color palette
        color_harmony = self._calculate_color_harmony(brand_config)

        # Visual appeal - overall visual sophistication
        visual_appeal = self._calculate_visual_appeal(brand_config)

        # Tone alignment - how well brand tone is defined
        tone_alignment = self._calculate_tone_alignment(brand_config)

        # Adaptability - how flexible the brand is for different content
        adaptability = self._calculate_adaptability(brand_config)

        # Creativity - room for creative expression within brand guidelines
        creativity = self._calculate_creativity(brand_config)

        # Audience fit - how well the brand serves target audience
        audience_fit = self._calculate_audience_fit(brand_config)

        return StyleDimensions(
            brand_recognition=brand_recognition,
            brand_consistency=brand_consistency,
            color_harmony=color_harmony,
            visual_appeal=visual_appeal,
            tone_alignment=tone_alignment,
            adaptability=adaptability,
            creativity=creativity,
            audience_fit=audience_fit
        )

    def _adjust_for_prompt(
        self,
        base_dimensions: StyleDimensions,
        prompt_analysis: PromptAnalysis
    ) -> StyleDimensions:
        """
        Adjust style dimensions based on prompt analysis insights.

        Args:
            base_dimensions: Base dimensions from brand config
            prompt_analysis: Prompt analysis results

        Returns:
            StyleDimensions: Adjusted dimensions
        """
        # Create a copy to modify
        adjusted = StyleDimensions(
            brand_recognition=base_dimensions.brand_recognition,
            brand_consistency=base_dimensions.brand_consistency,
            color_harmony=base_dimensions.color_harmony,
            visual_appeal=base_dimensions.visual_appeal,
            tone_alignment=base_dimensions.tone_alignment,
            adaptability=base_dimensions.adaptability,
            creativity=base_dimensions.creativity,
            audience_fit=base_dimensions.audience_fit
        )

        # Adjust tone alignment based on prompt tone
        if prompt_analysis.tone and prompt_analysis.tone.lower() in ['professional', 'corporate']:
            adjusted.tone_alignment = min(1.0, adjusted.tone_alignment + 0.1)
        elif prompt_analysis.tone and prompt_analysis.tone.lower() in ['casual', 'friendly']:
            adjusted.tone_alignment = max(0.0, adjusted.tone_alignment - 0.1)

        # Adjust creativity based on content type
        if prompt_analysis.content_type and 'advertisement' in prompt_analysis.content_type.lower():
            adjusted.creativity = min(1.0, adjusted.creativity + 0.15)
        elif prompt_analysis.content_type and 'educational' in prompt_analysis.content_type.lower():
            adjusted.creativity = max(0.0, adjusted.creativity - 0.1)

        # Adjust adaptability for specific use cases
        if prompt_analysis.primary_intent:
            intent_lower = prompt_analysis.primary_intent.lower()
            if 'product demonstration' in intent_lower:
                adjusted.adaptability = min(1.0, adjusted.adaptability + 0.1)
            elif 'brand awareness' in intent_lower:
                adjusted.brand_recognition = min(1.0, adjusted.brand_recognition + 0.1)

        return adjusted

    def _calculate_brand_recognition(self, brand_config: BrandConfig) -> float:
        """Calculate brand recognition score (0.0-1.0)"""
        score = 0.5  # Base score

        # Higher for established brands
        if hasattr(brand_config, 'category') and brand_config.category:
            if brand_config.category in ['luxury', 'corporate', 'financial']:
                score += 0.2
            elif brand_config.category == 'startup':
                score += 0.1

        # Higher for distinctive visual identity
        if brand_config.visual_style and brand_config.visual_style.logo_description:
            score += 0.1

        # Higher for strong color palette
        if brand_config.colors and len(brand_config.colors.primary) >= 2:
            score += 0.1

        return min(1.0, max(0.0, score))

    def _calculate_brand_consistency(self, brand_config: BrandConfig) -> float:
        """Calculate brand consistency score based on guideline completeness"""
        fields_filled = 0
        total_fields = 8  # colors, fonts, tone, visual_style, etc.

        if brand_config.colors and brand_config.colors.primary:
            fields_filled += 1
        if brand_config.typography and brand_config.typography.primary_font:
            fields_filled += 1
        if brand_config.tone:
            fields_filled += 1
        if brand_config.visual_style:
            fields_filled += 1
        if brand_config.audience:
            fields_filled += 1
        if brand_config.values:
            fields_filled += 1
        if brand_config.personality_traits:
            fields_filled += 1
        if brand_config.content_guidelines:
            fields_filled += 1

        return fields_filled / total_fields

    def _calculate_color_harmony(self, brand_config: BrandConfig) -> float:
        """Calculate color harmony score"""
        if not brand_config.colors or not brand_config.colors.primary:
            return 0.3  # Low score for missing colors

        primary_count = len(brand_config.colors.primary)
        has_secondary = bool(brand_config.colors.secondary and len(brand_config.colors.secondary) > 0)

        score = 0.4  # Base score

        if primary_count >= 3:
            score += 0.2
        elif primary_count >= 2:
            score += 0.1

        if has_secondary:
            score += 0.2

        if brand_config.colors.background:
            score += 0.1

        return min(1.0, score)

    def _calculate_visual_appeal(self, brand_config: BrandConfig) -> float:
        """Calculate overall visual appeal score"""
        score = 0.5  # Base score

        # Higher for luxury/corporate categories
        if hasattr(brand_config, 'category'):
            if brand_config.category == 'luxury':
                score += 0.2
            elif brand_config.category in ['corporate', 'technology']:
                score += 0.1

        # Higher for complete visual style
        if brand_config.visual_style:
            style_score = 0
            if brand_config.visual_style.logo_description:
                style_score += 0.1
            if brand_config.visual_style.imaging_style:
                style_score += 0.1
            if brand_config.visual_style.color_usage:
                style_score += 0.1
            score += style_score

        return min(1.0, max(0.0, score))

    def _calculate_tone_alignment(self, brand_config: BrandConfig) -> float:
        """Calculate tone alignment score"""
        if not brand_config.tone:
            return 0.4  # Neutral score

        # Higher score for well-defined tone
        score = 0.6

        # Higher for specific tone definitions
        if len(brand_config.tone.split()) > 2:
            score += 0.2

        # Higher for personality traits alignment
        if brand_config.personality_traits and len(brand_config.personality_traits) > 2:
            score += 0.2

        return min(1.0, score)

    def _calculate_adaptability(self, brand_config: BrandConfig) -> float:
        """Calculate brand adaptability score"""
        score = 0.6  # Base adaptability

        # Lower for luxury brands (less adaptable)
        if hasattr(brand_config, 'category') and brand_config.category == 'luxury':
            score -= 0.2

        # Higher for brands with flexible guidelines
        if brand_config.content_guidelines and 'flexible' in str(brand_config.content_guidelines).lower():
            score += 0.2

        # Higher for diverse audience targeting
        if brand_config.audience and len(brand_config.audience) > 1:
            score += 0.1

        return min(1.0, max(0.0, score))

    def _calculate_creativity(self, brand_config: BrandConfig) -> float:
        """Calculate creativity allowance within brand guidelines"""
        score = 0.5  # Base creativity

        # Higher for startup/technology brands
        if hasattr(brand_config, 'category'):
            if brand_config.category in ['startup', 'technology']:
                score += 0.2
            elif brand_config.category == 'luxury':
                score -= 0.1

        # Higher for brands that encourage creativity
        if brand_config.values and any(word in str(brand_config.values).lower()
                                     for word in ['innovation', 'creative', 'dynamic']):
            score += 0.15

        # Lower for highly structured brands
        if brand_config.content_guidelines and 'strict' in str(brand_config.content_guidelines).lower():
            score -= 0.1

        return min(1.0, max(0.0, score))

    def _calculate_audience_fit(self, brand_config: BrandConfig) -> float:
        """Calculate audience fit score"""
        if not brand_config.audience:
            return 0.5  # Neutral score

        score = 0.6  # Base score for having audience defined

        # Higher for multiple audience segments
        if len(brand_config.audience) > 1:
            score += 0.2

        # Higher for specific audience targeting
        if any('demographics' in str(aud).lower() or 'age' in str(aud).lower()
               for aud in brand_config.audience):
            score += 0.2

        return min(1.0, score)

    def _calculate_confidence_score(
        self,
        brand_config: BrandConfig,
        prompt_analysis: PromptAnalysis
    ) -> float:
        """Calculate overall confidence in the style vector"""
        brand_completeness = self._calculate_brand_consistency(brand_config)
        prompt_confidence = getattr(prompt_analysis, 'confidence_score', 0.8)

        # Weighted average
        confidence = (brand_completeness * 0.7) + (prompt_confidence * 0.3)

        return min(1.0, max(0.0, confidence))

    def _summarize_prompt_analysis(self, prompt_analysis: PromptAnalysis) -> Dict[str, Any]:
        """Create a summary of prompt analysis for metadata"""
        return {
            "primary_intent": prompt_analysis.primary_intent,
            "tone": prompt_analysis.tone,
            "content_type": prompt_analysis.content_type,
            "target_audience": prompt_analysis.target_audience,
            "key_themes": prompt_analysis.key_themes,
            "sentiment": prompt_analysis.sentiment
        }

    def _create_fallback_vector(
        self,
        brand_config: BrandConfig,
        prompt_analysis: PromptAnalysis
    ) -> BrandStyleVector:
        """Create a fallback style vector when computation fails"""
        logger.warning("Using fallback style vector due to computation failure")

        fallback = create_default_style_vector("good_brand_adaptation")
        fallback.brand_name = brand_config.name
        fallback.content_description = prompt_analysis.primary_intent or "Video content"
        fallback.confidence_score = 0.3  # Low confidence for fallback
        fallback.original_brand_config = brand_config.dict()
        fallback.prompt_analysis_summary = self._summarize_prompt_analysis(prompt_analysis)
        fallback.generated_at = datetime.utcnow().isoformat() + "Z"
        fallback.generation_method = "fallback"

        return fallback

    async def _get_cached_vector(self, cache_key: str) -> Optional[BrandStyleVector]:
        """Retrieve style vector from Redis cache"""
        try:
            if not self.redis_client:
                return None

            cached_data = await self.redis_client.get(f"style_vector:{cache_key}")
            if cached_data:
                data = json.loads(cached_data)
                return BrandStyleVector(**data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached style vector: {str(e)}")

        return None

    async def _cache_vector(self, cache_key: str, vector: BrandStyleVector) -> None:
        """Cache style vector in Redis"""
        try:
            if not self.redis_client:
                return

            cache_data = vector.dict()
            await self.redis_client.setex(
                f"style_vector:{cache_key}",
                self.cache_ttl,
                json.dumps(cache_data)
            )
            logger.debug(f"Cached style vector: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache style vector: {str(e)}")


def create_style_vector_cache_key(brand_config: BrandConfig, prompt_hash: str) -> str:
    """
    Create a cache key for style vector based on brand and content.

    Args:
        brand_config: Brand configuration
        prompt_hash: Hash of the prompt content

    Returns:
        Cache key string
    """
    import hashlib

    # Create a hash of brand configuration
    brand_str = f"{brand_config.name}_{brand_config.category}_{len(brand_config.colors.primary) if brand_config.colors else 0}"
    brand_hash = hashlib.md5(brand_str.encode()).hexdigest()[:8]

    return f"{brand_hash}_{prompt_hash[:8]}"
