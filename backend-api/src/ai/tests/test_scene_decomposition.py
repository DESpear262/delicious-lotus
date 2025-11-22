"""
Unit tests for Scene Decomposition Service - PR 103
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from services.scene_decomposition_service import SceneDecompositionService
from models.scene_decomposition import (
    SceneDecompositionRequest,
    VideoType,
    SceneType,
    Scene,
    AD_SCENE_RULES
)


@pytest.fixture
def scene_service():
    """Create SceneDecompositionService instance"""
    return SceneDecompositionService()


@pytest.fixture
def mock_prompt_analysis():
    """Mock prompt analysis data"""
    return {
        "tone": "professional",
        "style": "modern",
        "narrative_structure": "problem_solution",
        "target_audience": "business",
        "key_elements": [
            {
                "element_type": "product",
                "description": "Luxury watch with gold dial",
                "importance": 5
            },
            {
                "element_type": "benefit",
                "description": "Timeless elegance and precision",
                "importance": 4
            },
            {
                "element_type": "call_to_action",
                "description": "Visit our showroom today",
                "importance": 3
            }
        ],
        "visual_themes": ["elegant", "luxurious"],
        "color_palette": {"primary": ["#D4AF37", "#1A1A1A"]},
        "imagery_styles": ["photography", "lifestyle"],
        "brand_alignment_score": 0.8
    }


@pytest.fixture
def mock_brand_config():
    """Mock brand configuration data"""
    return {
        "name": "ChronoLux",
        "category": "luxury",
        "color_palette": {
            "primary": ["#D4AF37", "#1A1A1A"],
            "secondary": ["#F5F5F0"]
        },
        "typography": {
            "primary_font": "serif",
            "secondary_font": "sans-serif"
        }
    }


class TestSceneDecompositionService:
    """Test cases for SceneDecompositionService"""

    @pytest.mark.asyncio
    async def test_decompose_ad_30_seconds(self, scene_service, mock_prompt_analysis, mock_brand_config):
        """Test decomposing a 30-second ad"""
        request = SceneDecompositionRequest(
            video_type=VideoType.AD,
            total_duration=30,
            prompt_analysis=mock_prompt_analysis,
            brand_config=mock_brand_config
        )

        response = await scene_service.decompose_video(request)

        assert response.video_type == VideoType.AD
        assert response.total_duration == 30
        assert len(response.scenes) == 3  # Introduction, Development, CTA

        # Check scene types
        scene_types = [scene.scene_type for scene in response.scenes]
        assert SceneType.INTRODUCTION in scene_types
        assert SceneType.DEVELOPMENT in scene_types
        assert SceneType.CTA in scene_types

        # Check timing continuity
        expected_start = 0.0
        for scene in response.scenes:
            assert scene.start_time == pytest.approx(expected_start, abs=0.1)
            expected_start += scene.duration

        # Check total duration coverage
        total_scene_duration = sum(scene.duration for scene in response.scenes)
        assert total_scene_duration == pytest.approx(30.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_decompose_ad_15_seconds(self, scene_service, mock_prompt_analysis):
        """Test decomposing a 15-second ad"""
        request = SceneDecompositionRequest(
            video_type=VideoType.AD,
            total_duration=15,
            prompt_analysis=mock_prompt_analysis
        )

        response = await scene_service.decompose_video(request)

        assert len(response.scenes) == 3
        total_duration = sum(scene.duration for scene in response.scenes)
        assert total_duration == pytest.approx(15.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_ad_scene_duration_distribution(self, scene_service):
        """Test that ad scenes follow the expected duration distribution"""
        durations = scene_service._calculate_ad_scene_durations(30, 3.0)

        # Check that all scene types are present
        assert SceneType.INTRODUCTION in durations
        assert SceneType.DEVELOPMENT in durations
        assert SceneType.CTA in durations

        # Check approximate distribution (20%, 50%, 30%)
        intro_duration = durations[SceneType.INTRODUCTION]
        dev_duration = durations[SceneType.DEVELOPMENT]
        cta_duration = durations[SceneType.CTA]

        total = intro_duration + dev_duration + cta_duration
        assert intro_duration / total == pytest.approx(0.20, abs=0.05)
        assert dev_duration / total == pytest.approx(0.50, abs=0.05)
        assert cta_duration / total == pytest.approx(0.30, abs=0.05)

    def test_calculate_ad_scene_durations_minimums(self, scene_service):
        """Test that minimum scene durations are respected"""
        # Very short video should still respect minimums
        durations = scene_service._calculate_ad_scene_durations(5, 3.0)

        for duration in durations.values():
            assert duration >= 3.0

    @pytest.mark.asyncio
    async def test_music_video_placeholder(self, scene_service, mock_prompt_analysis):
        """Test music video decomposition (placeholder implementation)"""
        request = SceneDecompositionRequest(
            video_type=VideoType.MUSIC_VIDEO,
            total_duration=90,
            prompt_analysis=mock_prompt_analysis
        )

        response = await scene_service.decompose_video(request)

        assert response.video_type == VideoType.MUSIC_VIDEO
        assert response.total_duration == 90
        assert len(response.scenes) >= 8  # Should have multiple scenes

        total_duration = sum(scene.duration for scene in response.scenes)
        assert total_duration == pytest.approx(90.0, abs=0.1)

    def test_select_scene_elements_by_importance(self, scene_service, mock_prompt_analysis):
        """Test that scene elements are selected based on importance and scene type"""
        from models.prompt_analysis import PromptAnalysis, KeyElement

        # Create a proper PromptAnalysis object
        key_elements = [
            KeyElement(element_type="hero_product", description="Main product", importance=5),
            KeyElement(element_type="benefit", description="Key benefit", importance=4),
            KeyElement(element_type="detail", description="Minor detail", importance=2),
            KeyElement(element_type="cta", description="Call to action", importance=3)
        ]

        prompt_analysis = PromptAnalysis(
            tone="professional",
            style="modern",
            narrative_structure="problem_solution",
            target_audience="business",
            key_elements=key_elements,
            visual_themes=[],
            color_palette=MagicMock(),
            imagery_styles=[],
            brand_alignment_score=0.8
        )

        # Test introduction scene (high importance)
        intro_elements = scene_service._select_scene_elements(SceneType.INTRODUCTION, prompt_analysis)
        assert len(intro_elements) > 0
        # Should prioritize high importance elements
        high_importance = [e for e in intro_elements if e.importance >= 4]
        assert len(high_importance) > 0

        # Test CTA scene (lower priority)
        cta_elements = scene_service._select_scene_elements(SceneType.CTA, prompt_analysis)
        assert len(cta_elements) >= 0  # May include lower priority elements

    def test_determine_visual_style(self, scene_service, mock_prompt_analysis):
        """Test visual style determination"""
        from models.prompt_analysis import PromptAnalysis
        from models.scene_decomposition import SceneDistributionRule, VisualStyle

        prompt_analysis = PromptAnalysis(
            tone="professional",
            style="modern",
            narrative_structure="problem_solution",
            target_audience="business",
            key_elements=[],
            visual_themes=[],
            color_palette=MagicMock(),
            imagery_styles=[],
            brand_alignment_score=0.8
        )

        # Test with rule that has visual style hint
        rule_with_hint = SceneDistributionRule(
            scene_type=SceneType.INTRODUCTION,
            duration_percentage=0.2,
            content_priority=4,
            visual_style_hint=VisualStyle.BRAND_SHOWCASE,
            description_template="Test"
        )

        style = scene_service._determine_visual_style(
            SceneType.INTRODUCTION,
            rule_with_hint,
            prompt_analysis
        )
        assert style == VisualStyle.BRAND_SHOWCASE

        # Test fallback logic
        rule_without_hint = SceneDistributionRule(
            scene_type=SceneType.DEVELOPMENT,
            duration_percentage=0.5,
            content_priority=5,
            description_template="Test"
        )

        style = scene_service._determine_visual_style(
            SceneType.DEVELOPMENT,
            rule_without_hint,
            prompt_analysis
        )
        assert style == VisualStyle.PRODUCT_SHOT  # Default for development

    def test_determine_pacing(self, scene_service):
        """Test pacing determination logic"""
        # Short introduction should be fast
        pacing = scene_service._determine_pacing(SceneType.INTRODUCTION, 3.0)
        assert pacing == "fast"

        # Long scene should be slow
        pacing = scene_service._determine_pacing(SceneType.DEVELOPMENT, 15.0)
        assert pacing == "slow"

        # Medium scene should be medium
        pacing = scene_service._determine_pacing(SceneType.DEVELOPMENT, 6.0)
        assert pacing == "medium"

        # Climax should be fast regardless of duration
        pacing = scene_service._determine_pacing(SceneType.CLIMAX, 10.0)
        assert pacing == "fast"

    def test_scene_validation(self):
        """Test scene model validation"""
        from models.scene_decomposition import Scene, SceneType, VisualStyle

        # Valid scene
        scene = Scene(
            scene_id="test_scene",
            scene_type=SceneType.INTRODUCTION,
            start_time=0.0,
            duration=6.0,
            end_time=6.0,  # Should equal start_time + duration
            title="Test Scene",
            content_description="Test description",
            narrative_purpose="Test purpose",
            visual_style=VisualStyle.PRODUCT_SHOT,
            key_elements=[],
            brand_references=MagicMock()
        )
        assert scene.end_time == 6.0

        # Invalid scene (end_time doesn't match)
        with pytest.raises(ValueError):
            Scene(
                scene_id="invalid_scene",
                scene_type=SceneType.INTRODUCTION,
                start_time=0.0,
                duration=6.0,
                end_time=7.0,  # Doesn't match start_time + duration
                title="Test Scene",
                content_description="Test description",
                narrative_purpose="Test purpose",
                visual_style=VisualStyle.PRODUCT_SHOT,
                key_elements=[],
                brand_references=MagicMock()
            )

    @pytest.mark.asyncio
    async def test_integration_with_mock_data(self, scene_service, mock_prompt_analysis):
        """Integration test with realistic mock data"""
        request = SceneDecompositionRequest(
            video_type=VideoType.AD,
            total_duration=30,
            prompt_analysis=mock_prompt_analysis,
            brand_config=None  # Test without brand config
        )

        response = await scene_service.decompose_video(request)

        assert response.scenes is not None
        assert len(response.scenes) == 3

        # Check that scenes have required fields
        for scene in response.scenes:
            assert scene.scene_id is not None
            assert scene.title is not None
            assert scene.content_description is not None
            assert scene.narrative_purpose is not None
            assert scene.visual_style is not None

        # Check brand consistency calculation
        assert response.brand_consistency_score is not None

        print(f"Decomposed into {len(response.scenes)} scenes:")
        for scene in response.scenes:
            print(f"  {scene.scene_type.value}: {scene.duration:.1f}s - {scene.title}")
