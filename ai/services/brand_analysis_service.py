"""
Brand Analysis Service - PR 102: Brand & Metadata Extraction Layer
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..core.openai_client import OpenAIClient
from ..models.brand_config import BrandConfig, get_default_brand_config
from ..models.prompt_analysis import PromptAnalysis


logger = logging.getLogger(__name__)


class BrandAnalysisService:
    """Service for analyzing and merging brand configuration with prompt analysis"""

    def __init__(self, openai_api_key: str, use_mock: bool = False):
        """
        Initialize the brand analysis service

        Args:
            openai_api_key: OpenAI API key
            use_mock: Whether to use mock responses for testing
        """
        self.use_mock = use_mock
        if not use_mock:
            self.openai_client = OpenAIClient(api_key=openai_api_key)

    async def analyze_brand(
        self,
        prompt_analysis: PromptAnalysis,
        brand_config: Optional[Dict[str, Any]] = None
    ) -> BrandConfig:
        """
        Analyze and merge brand configuration with prompt analysis

        Args:
            prompt_analysis: Results from prompt analysis (PR 101)
            brand_config: Optional brand configuration provided by user

        Returns:
            BrandConfig: Complete and validated brand configuration

        Raises:
            Exception: If brand analysis fails
        """
        try:
            logger.info("Starting brand analysis...")

            # If no brand config provided, check if prompt contains brand information
            if not brand_config:
                brand_config = self._extract_brand_from_prompt(prompt_analysis)

            # If we still don't have brand config, use defaults
            if not brand_config:
                logger.info("No brand configuration found, using default corporate brand")
                return get_default_brand_config("corporate")

            # Convert to BrandConfig object (this will validate the schema)
            try:
                brand_config_obj = BrandConfig(**brand_config)
            except Exception as e:
                logger.warning(f"Invalid brand config provided: {e}, attempting to complete missing fields")
                brand_config_obj = await self._complete_brand_config(brand_config, prompt_analysis)

            # If brand config is incomplete, fill in missing information
            if self._is_brand_config_incomplete(brand_config_obj):
                logger.info("Brand configuration is incomplete, filling missing information")
                brand_config_obj = await self._complete_brand_config(brand_config, prompt_analysis)

            # Merge brand config with prompt analysis insights
            merged_config = await self._merge_with_prompt_analysis(brand_config_obj, prompt_analysis)

            logger.info(f"Brand analysis completed for: {merged_config.name}")
            return merged_config

        except Exception as e:
            logger.error(f"Brand analysis failed: {str(e)}")
            # For MVP, fail the entire request as per requirements
            raise Exception(f"Brand analysis failed: {str(e)}")

    def _extract_brand_from_prompt(self, prompt_analysis: PromptAnalysis) -> Optional[Dict[str, Any]]:
        """
        Extract brand information from prompt analysis if present

        Args:
            prompt_analysis: Results from prompt analysis

        Returns:
            Optional brand configuration extracted from prompt
        """
        # Check if the prompt analysis detected any brand/product focus
        if not prompt_analysis.product_focus:
            return None

        # Create a minimal brand config based on prompt analysis
        brand_config = {
            "name": prompt_analysis.product_focus,
            "category": "other",  # Will be refined by GPT
            "colors": {
                "primary": ["#0066CC", "#333333"],  # Generic professional colors
                "background": "#ffffff"
            }
        }

        logger.info(f"Extracted basic brand info from prompt: {prompt_analysis.product_focus}")
        return brand_config

    def _is_brand_config_incomplete(self, brand_config: BrandConfig) -> bool:
        """
        Check if brand configuration is missing important information

        Args:
            brand_config: Brand configuration to check

        Returns:
            True if configuration needs completion
        """
        # Check for critical missing fields
        missing_critical = []

        if not brand_config.description:
            missing_critical.append("description")

        if not brand_config.target_audience:
            missing_critical.append("target_audience")

        if not brand_config.typography:
            missing_critical.append("typography")

        if not brand_config.visual_style:
            missing_critical.append("visual_style")

        if len(brand_config.colors.primary) < 2:
            missing_critical.append("secondary_colors")

        is_incomplete = len(missing_critical) > 0
        if is_incomplete:
            logger.info(f"Brand config missing critical fields: {missing_critical}")

        return is_incomplete

    async def _complete_brand_config(
        self,
        partial_config: Dict[str, Any],
        prompt_analysis: PromptAnalysis
    ) -> BrandConfig:
        """
        Complete missing brand configuration information using GPT-4o-mini

        Args:
            partial_config: Partial brand configuration
            prompt_analysis: Prompt analysis results for context

        Returns:
            Complete BrandConfig object
        """
        if self.use_mock:
            return self._get_mock_completed_brand_config(partial_config, prompt_analysis)

        try:
            # Create completion prompt
            system_prompt = self._create_completion_system_prompt()
            user_prompt = self._create_completion_user_prompt(partial_config, prompt_analysis)

            logger.info("Calling GPT-4o-mini to complete brand configuration")

            response = await self.openai_client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from GPT-4o-mini")

            # Parse and merge the completion
            completion_data = json.loads(content)

            # Merge completion with original config
            merged_config = {**partial_config, **completion_data}

            # Validate the merged configuration
            brand_config = BrandConfig(**merged_config)

            logger.info(f"Successfully completed brand configuration for: {brand_config.name}")
            return brand_config

        except Exception as e:
            logger.error(f"Failed to complete brand config: {e}")
            # Fallback to default config
            return get_default_brand_config("corporate")

    async def _merge_with_prompt_analysis(
        self,
        brand_config: BrandConfig,
        prompt_analysis: PromptAnalysis
    ) -> BrandConfig:
        """
        Merge brand configuration with insights from prompt analysis

        Args:
            brand_config: Brand configuration
            prompt_analysis: Prompt analysis results

        Returns:
            Merged BrandConfig with analysis insights
        """
        if self.use_mock:
            return self._get_mock_merged_brand_config(brand_config, prompt_analysis)

        try:
            # Create merge prompt
            system_prompt = self._create_merge_system_prompt()
            user_prompt = self._create_merge_user_prompt(brand_config, prompt_analysis)

            logger.info("Calling GPT-4o-mini to merge brand config with prompt analysis")

            response = await self.openai_client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent merging
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from GPT-4o-mini")

            # Parse merge suggestions
            merge_data = json.loads(content)

            # Apply merge suggestions while maintaining brand integrity
            merged_config = self._apply_merge_suggestions(brand_config, merge_data, prompt_analysis)

            logger.info(f"Successfully merged brand config with prompt analysis")
            return merged_config

        except Exception as e:
            logger.error(f"Failed to merge brand config with prompt analysis: {e}")
            # Return original brand config if merge fails
            return brand_config

    def _apply_merge_suggestions(
        self,
        brand_config: BrandConfig,
        merge_suggestions: Dict[str, Any],
        prompt_analysis: PromptAnalysis
    ) -> BrandConfig:
        """
        Apply merge suggestions while maintaining brand integrity

        Args:
            brand_config: Original brand configuration
            merge_suggestions: Suggestions from GPT-4o-mini
            prompt_analysis: Original prompt analysis

        Returns:
            Merged brand configuration
        """
        # Convert to dict for manipulation
        config_dict = brand_config.dict()

        # Apply merge suggestions selectively
        if "adjusted_colors" in merge_suggestions:
            # Only adjust colors if they complement the brand
            if self._colors_complement_brand(merge_suggestions["adjusted_colors"], brand_config):
                config_dict["colors"]["secondary"] = merge_suggestions["adjusted_colors"]

        if "typography_adjustments" in merge_suggestions and brand_config.typography:
            # Apply typography adjustments
            if "adjusted_fonts" in merge_suggestions["typography_adjustments"]:
                config_dict["typography"]["secondary_font"] = merge_suggestions["typography_adjustments"]["adjusted_fonts"]

        if "visual_style_enhancements" in merge_suggestions and brand_config.visual_style:
            # Enhance visual style based on prompt analysis
            enhancements = merge_suggestions["visual_style_enhancements"]
            if "mood_adjustment" in enhancements:
                config_dict["visual_style"]["mood"] = enhancements["mood_adjustment"]

        # Add analysis context
        if "other" not in config_dict:
            config_dict["other"] = {}

        config_dict["other"]["prompt_analysis_context"] = {
            "tone": prompt_analysis.tone,
            "style": prompt_analysis.style,
            "key_themes": prompt_analysis.key_themes[:3],  # Limit to top 3
            "merged_at": "brand_analysis_service"
        }

        return BrandConfig(**config_dict)

    def _colors_complement_brand(self, suggested_colors: List[str], brand_config: BrandConfig) -> bool:
        """
        Check if suggested colors complement the brand's primary colors

        Args:
            suggested_colors: Colors suggested for addition
            brand_config: Original brand configuration

        Returns:
            True if colors complement the brand
        """
        # Simple check: ensure suggested colors aren't too similar to existing primaries
        primary_colors = {color.lower() for color in brand_config.colors.primary}

        for suggested in suggested_colors:
            if suggested.lower() in primary_colors:
                return False  # Too similar to existing colors

        return True

    def _create_completion_system_prompt(self) -> str:
        """Create system prompt for brand config completion"""
        return """You are a brand strategy expert. Given partial brand information and context from a video generation prompt, complete the missing brand configuration details.

Focus on:
1. Creating a cohesive brand identity that matches the provided information
2. Filling in gaps with reasonable assumptions based on brand category
3. Ensuring all required fields are populated with appropriate defaults
4. Maintaining brand consistency and professionalism

Return a complete brand configuration JSON object that follows the BrandConfig schema."""

    def _create_completion_user_prompt(
        self,
        partial_config: Dict[str, Any],
        prompt_analysis: PromptAnalysis
    ) -> str:
        """Create user prompt for brand config completion"""
        return f"""Complete this partial brand configuration based on the provided prompt analysis:

Partial Brand Config:
{json.dumps(partial_config, indent=2)}

Prompt Analysis Context:
- Tone: {prompt_analysis.tone}
- Style: {prompt_analysis.style}
- Target Audience: {prompt_analysis.target_audience}
- Key Themes: {prompt_analysis.key_themes}
- Visual Theme: {prompt_analysis.visual_theme}
- Product Focus: {prompt_analysis.product_focus or 'None specified'}

Provide a complete brand configuration with all missing fields filled in appropriately."""

    def _create_merge_system_prompt(self) -> str:
        """Create system prompt for brand config merging"""
        return """You are a brand strategist specializing in video content. Your task is to suggest how to adapt a brand's visual identity to complement specific video content while maintaining brand recognition.

Key principles:
1. The final result must be recognizable as the original brand (e.g., Nike swoosh with unusual texture/color is OK, but swoosh with rounded tips is not)
2. Adaptations should enhance rather than contradict the brand
3. Consider the video's tone, style, and target audience
4. Focus on color harmony, typography consistency, and visual coherence

Return specific, actionable suggestions for merging brand identity with video requirements."""

    def _create_merge_user_prompt(
        self,
        brand_config: BrandConfig,
        prompt_analysis: PromptAnalysis
    ) -> str:
        """Create user prompt for brand config merging"""
        return f"""Suggest how to merge this brand configuration with video content requirements:

Brand Configuration:
{json.dumps(brand_config.dict(), indent=2)}

Video Content Requirements (from prompt analysis):
- Tone: {prompt_analysis.tone}
- Style: {prompt_analysis.style}
- Target Audience: {prompt_analysis.target_audience}
- Key Themes: {prompt_analysis.key_themes}
- Visual Theme: {prompt_analysis.visual_theme}
- Imagery Style: {prompt_analysis.imagery_style}
- Key Messages: {prompt_analysis.key_messages}

Suggest specific adjustments to colors, typography, or visual style that would enhance the video while maintaining brand integrity."""

    # Mock implementations for testing
    def _get_mock_completed_brand_config(
        self,
        partial_config: Dict[str, Any],
        prompt_analysis: PromptAnalysis
    ) -> BrandConfig:
        """Mock implementation for testing"""
        completed_config = {
            **partial_config,
            "description": f"A {prompt_analysis.target_audience} brand focused on {prompt_analysis.key_themes[0] if prompt_analysis.key_themes else 'quality products'}",
            "target_audience": prompt_analysis.target_audience,
            "typography": {
                "primary_font": "Arial",
                "secondary_font": "Helvetica"
            },
            "visual_style": {
                "aesthetic": prompt_analysis.style,
                "mood": prompt_analysis.tone,
                "imagery_style": prompt_analysis.imagery_style
            }
        }
        return BrandConfig(**completed_config)

    def _get_mock_merged_brand_config(
        self,
        brand_config: BrandConfig,
        prompt_analysis: PromptAnalysis
    ) -> BrandConfig:
        """Mock implementation for testing"""
        # Add some mock merge data
        config_dict = brand_config.dict()
        if "other" not in config_dict:
            config_dict["other"] = {}

        config_dict["other"]["prompt_analysis_context"] = {
            "tone": prompt_analysis.tone,
            "style": prompt_analysis.style,
            "key_themes": prompt_analysis.key_themes[:2],
            "merged_at": "mock_brand_analysis_service"
        }

        return BrandConfig(**config_dict)
