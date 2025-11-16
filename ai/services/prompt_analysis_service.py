"""
Prompt Analysis Service - PR 101: Prompt Parsing Module
"""

import logging
import time
from typing import Any, Dict, Optional

from ..core.openai_client import OpenAIClient
from ..models.prompt_analysis import (
    AnalysisRequest,
    AnalysisResponse,
    MockAnalysisResponse,
    PromptAnalysis,
    Tone,
    Style,
    VisualTheme,
    NarrativeStructure,
    TargetAudience,
    ImageryStyle,
    ColorPalette,
    KeyElement
)


logger = logging.getLogger(__name__)


class PromptAnalysisService:
    """Service for analyzing video generation prompts using AI"""

    def __init__(self, openai_api_key: str, use_mock: bool = False):
        """
        Initialize the prompt analysis service

        Args:
            openai_api_key: OpenAI API key
            use_mock: Whether to use mock responses for testing
        """
        self.use_mock = use_mock
        if not use_mock:
            self.openai_client = OpenAIClient(api_key=openai_api_key)

    async def analyze_prompt(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Analyze a video generation prompt

        Args:
            request: Analysis request containing prompt and optional context

        Returns:
            AnalysisResponse: Structured analysis of the prompt

        Raises:
            Exception: If analysis fails (for MVP, fail the entire request)
        """
        start_time = time.time()

        try:
            logger.info(f"Starting prompt analysis for prompt: {request.prompt[:100]}...")

            if self.use_mock:
                analysis = self._get_mock_analysis(request.prompt)
                processing_time = time.time() - start_time

                response = MockAnalysisResponse(
                    analysis=analysis,
                    is_mock=True,
                    mock_reason="testing"
                )
                logger.info(f"Mock analysis completed in {processing_time:.2f}s")
                return AnalysisResponse(
                    analysis=analysis,
                    processing_time=processing_time,
                    status="success"
                )

            # Real OpenAI analysis
            analysis = await self.openai_client.analyze_prompt(
                prompt=request.prompt,
                context=request.context
            )

            processing_time = time.time() - start_time
            logger.info(f"OpenAI analysis completed in {processing_time:.2f}s")

            return AnalysisResponse(
                analysis=analysis,
                processing_time=processing_time,
                status="success"
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Prompt analysis failed after {processing_time:.2f}s: {str(e)}")
            # For MVP: fail the entire request as requested
            raise Exception(f"Prompt analysis failed: {str(e)}")

    def _get_mock_analysis(self, prompt: str) -> PromptAnalysis:
        """
        Generate mock analysis for testing purposes
        This creates realistic analysis based on common patterns in prompts
        """
        # Simple keyword-based analysis for mock responses
        prompt_lower = prompt.lower()

        # Determine tone based on keywords
        if any(word in prompt_lower for word in ['professional', 'business', 'corporate', 'formal']):
            tone = Tone.PROFESSIONAL
        elif any(word in prompt_lower for word in ['fun', 'exciting', 'energetic', 'playful']):
            tone = Tone.ENTHUSIASTIC
        elif any(word in prompt_lower for word in ['calm', 'peaceful', 'relaxed']):
            tone = Tone.CALM
        else:
            tone = Tone.FRIENDLY

        # Determine style
        if 'modern' in prompt_lower:
            style = Style.MODERN
        elif any(word in prompt_lower for word in ['classic', 'traditional', 'vintage']):
            style = Style.CLASSIC
        elif any(word in prompt_lower for word in ['cinematic', 'movie', 'film']):
            style = Style.CINEMATIC
        else:
            style = Style.MODERN

        # Determine visual theme
        if any(word in prompt_lower for word in ['bright', 'colorful', 'vibrant']):
            visual_theme = VisualTheme.BRIGHT
        elif any(word in prompt_lower for word in ['dark', 'moody', 'dramatic']):
            visual_theme = VisualTheme.DARK
        elif any(word in prompt_lower for word in ['warm', 'cozy', 'sunny']):
            visual_theme = VisualTheme.WARM
        else:
            visual_theme = VisualTheme.NEUTRAL

        # Determine narrative structure
        if any(word in prompt_lower for word in ['problem', 'solution', 'challenge', 'fix']):
            narrative_structure = NarrativeStructure.PROBLEM_SOLUTION
        elif any(word in prompt_lower for word in ['story', 'journey', 'experience']):
            narrative_structure = NarrativeStructure.STORYTELLING
        elif any(word in prompt_lower for word in ['demo', 'show', 'how to', 'tutorial']):
            narrative_structure = NarrativeStructure.DEMONSTRATION
        else:
            narrative_structure = NarrativeStructure.EXPLANATION

        # Determine target audience
        if any(word in prompt_lower for word in ['business', 'professional', 'enterprise']):
            target_audience = TargetAudience.BUSINESS
        elif any(word in prompt_lower for word in ['family', 'kids', 'children']):
            target_audience = TargetAudience.FAMILIES
        elif any(word in prompt_lower for word in ['young', 'teen', 'millennial']):
            target_audience = TargetAudience.TEENS
        else:
            target_audience = TargetAudience.CONSUMERS

        # Determine imagery style
        if any(word in prompt_lower for word in ['photo', 'photography', 'realistic']):
            imagery_style = ImageryStyle.PHOTOGRAPHY
        elif any(word in prompt_lower for word in ['graphic', 'illustration', 'animated']):
            imagery_style = ImageryStyle.ILLUSTRATION
        elif any(word in prompt_lower for word in ['product', 'item', 'device']):
            imagery_style = ImageryStyle.PRODUCT_SHOTS
        else:
            imagery_style = ImageryStyle.LIFESTYLE

        # Extract key themes (simplified)
        key_themes = []
        if 'technology' in prompt_lower or 'tech' in prompt_lower:
            key_themes.append("technology")
        if 'innovation' in prompt_lower:
            key_themes.append("innovation")
        if 'quality' in prompt_lower:
            key_themes.append("quality")
        if not key_themes:
            key_themes = ["professionalism", "excellence"]

        # Extract key messages
        key_messages = ["Trust our solution", "Experience the difference"]
        if 'save' in prompt_lower or 'money' in prompt_lower:
            key_messages.append("Save time and money")
        if 'easy' in prompt_lower or 'simple' in prompt_lower:
            key_messages.append("Easy to use")

        # Create mock analysis
        return PromptAnalysis(
            tone=tone,
            style=style,
            narrative_intent="Create engaging video content that resonates with the target audience",
            narrative_structure=narrative_structure,
            target_audience=target_audience,
            key_themes=key_themes,
            key_messages=key_messages,
            visual_theme=visual_theme,
            imagery_style=imagery_style,
            color_palette=ColorPalette(
                primary_colors=["#0066CC", "#FFFFFF"],
                secondary_colors=["#333333", "#666666"],
                mood="professional"
            ),
            key_elements=[
                KeyElement(
                    element_type="main_subject",
                    description="Primary product or service being featured",
                    importance=5
                ),
                KeyElement(
                    element_type="call_to_action",
                    description="Clear call-to-action element",
                    importance=4
                )
            ],
            product_focus="Featured product/service" if 'product' in prompt_lower else None,
            pacing="moderate",
            music_style="corporate",
            confidence_score=0.85,
            analysis_notes=["Mock analysis for testing purposes"],
            original_prompt=prompt,
            analysis_timestamp="2025-11-14T15:00:00Z",
            model_version="mock-v1.0"
        )
