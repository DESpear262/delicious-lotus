"""
Integration tests for Scene Decomposition - PR 103
Tests the full pipeline from prompt analysis to scene decomposition
"""

import pytest
from unittest.mock import AsyncMock, patch

from services.scene_decomposition_service import SceneDecompositionService
from services.prompt_analysis_service import PromptAnalysisService
from models.scene_decomposition import SceneDecompositionRequest, VideoType, SceneType


class TestSceneDecompositionIntegration:
    """Integration tests for the complete scene decomposition pipeline"""

    @pytest.fixture
    def prompt_service(self):
        """Create PromptAnalysisService with mock OpenAI"""
        service = PromptAnalysisService(openai_api_key="test_key", use_mock=True)
        return service

    @pytest.fixture
    def scene_service(self):
        """Create SceneDecompositionService"""
        return SceneDecompositionService()

    @pytest.mark.asyncio
    async def test_full_pipeline_ad_decomposition(self, prompt_service, scene_service):
        """Test the complete pipeline: prompt → analysis → scenes"""

        # Step 1: Analyze a sample prompt
        from models.prompt_analysis import AnalysisRequest

        prompt = """
        Create a 30-second advertisement for ChronoLux, a luxury watch brand.
        Show elegant gold watches with black dials, emphasize precision craftsmanship,
        timeless design, and call viewers to visit our showroom for an exclusive experience.
        """

        request = AnalysisRequest(
            prompt=prompt,
            context={"brand": "ChronoLux", "industry": "luxury_watches"}
        )

        analysis_response = await prompt_service.analyze_prompt(request)

        # Verify analysis worked
        assert analysis_response.analysis.tone.value == "professional"
        assert len(analysis_response.analysis.key_elements) > 0

        # Step 2: Decompose into scenes
        scene_request = SceneDecompositionRequest(
            video_type=VideoType.AD,
            total_duration=30,
            prompt_analysis=analysis_response.analysis.dict(),
            brand_config=None  # Test without brand config for simplicity
        )

        scene_response = await scene_service.decompose_video(scene_request)

        # Verify decomposition worked
        assert scene_response.video_type == VideoType.AD
        assert scene_response.total_duration == 30
        assert len(scene_response.scenes) == 3  # Intro, Development, CTA

        # Verify scene structure
        intro_scene = next(s for s in scene_response.scenes if s.scene_type == SceneType.INTRODUCTION)
        dev_scene = next(s for s in scene_response.scenes if s.scene_type == SceneType.DEVELOPMENT)
        cta_scene = next(s for s in scene_response.scenes if s.scene_type == SceneType.CTA)

        # Check timing
        assert intro_scene.start_time == 0.0
        assert dev_scene.start_time == intro_scene.end_time
        assert cta_scene.start_time == dev_scene.end_time
        assert cta_scene.end_time == pytest.approx(30.0, abs=0.1)

        # Check duration distribution (roughly 20/50/30)
        total_duration = sum(s.duration for s in scene_response.scenes)
        intro_pct = intro_scene.duration / total_duration
        dev_pct = dev_scene.duration / total_duration
        cta_pct = cta_scene.duration / total_duration

        assert intro_pct == pytest.approx(0.20, abs=0.05)
        assert dev_pct == pytest.approx(0.50, abs=0.05)
        assert cta_pct == pytest.approx(0.30, abs=0.05)

        print("🎬 Full pipeline test results:")
        print(f"   Total scenes: {len(scene_response.scenes)}")
        print(f"   Total duration: {total_duration:.1f}s")
        print(f"   Average scene duration: {scene_response.average_scene_duration:.1f}s")

        for scene in scene_response.scenes:
            print(f"   {scene.scene_type.value.title()}: {scene.duration:.1f}s - {scene.title}")
            if scene.key_elements:
                print(f"      Key elements: {len(scene.key_elements)}")

    @pytest.mark.asyncio
    async def test_brand_integration_in_scenes(self, scene_service):
        """Test that brand elements are properly integrated into scenes"""

        # Mock brand config
        brand_config = {
            "name": "ChronoLux",
            "category": "luxury",
            "color_palette": {
                "primary": ["#D4AF37", "#1A1A1A", "#F5F5F0"]
            },
            "typography": {
                "primary_font": "serif"
            }
        }

        # Mock prompt analysis
        prompt_analysis = {
            "tone": "professional",
            "style": "elegant",
            "narrative_structure": "demonstration",
            "target_audience": "luxury_consumers",
            "key_elements": [
                {"element_type": "product", "description": "Gold luxury watch", "importance": 5},
                {"element_type": "benefit", "description": "Precision craftsmanship", "importance": 4},
                {"element_type": "location", "description": "Luxury showroom", "importance": 3}
            ],
            "visual_themes": ["elegant", "luxurious", "timeless"],
            "color_palette": {"primary": ["#D4AF37"]},
            "imagery_styles": ["photography", "lifestyle"],
            "brand_alignment_score": 0.9
        }

        request = SceneDecompositionRequest(
            video_type=VideoType.AD,
            total_duration=30,
            prompt_analysis=prompt_analysis,
            brand_config=brand_config
        )

        response = await scene_service.decompose_video(request)

        # Verify brand integration
        for scene in response.scenes:
            # Each scene should have brand references
            assert scene.brand_references is not None

            # Introduction should have logo placement
            if scene.scene_type == SceneType.INTRODUCTION:
                assert scene.brand_references.logo_placement is not None

        # Check brand consistency score
        assert response.brand_consistency_score is not None
        assert 0.0 <= response.brand_consistency_score <= 1.0

    @pytest.mark.asyncio
    async def test_different_video_lengths(self, scene_service):
        """Test scene decomposition with different video lengths"""

        prompt_analysis = {
            "tone": "professional",
            "style": "modern",
            "narrative_structure": "problem_solution",
            "target_audience": "business",
            "key_elements": [],
            "visual_themes": [],
            "color_palette": {},
            "imagery_styles": [],
            "brand_alignment_score": 0.5
        }

        # Test various ad lengths
        for duration in [15, 30, 45, 60]:
            request = SceneDecompositionRequest(
                video_type=VideoType.AD,
                total_duration=duration,
                prompt_analysis=prompt_analysis
            )

            response = await scene_service.decompose_video(request)

            assert len(response.scenes) == 3  # Always 3 scenes for ads
            total_scene_duration = sum(s.duration for s in response.scenes)
            assert total_scene_duration == pytest.approx(duration, abs=0.1)

            print(f"✅ {duration}s ad: {len(response.scenes)} scenes, total duration {total_scene_duration:.1f}s")

    @pytest.mark.asyncio
    async def test_music_video_basic_structure(self, scene_service):
        """Test basic music video decomposition (placeholder)"""

        prompt_analysis = {
            "tone": "energetic",
            "style": "cinematic",
            "narrative_structure": "celebration",
            "target_audience": "young_adults",
            "key_elements": [],
            "visual_themes": ["dynamic", "colorful"],
            "color_palette": {},
            "imagery_styles": ["photography"],
            "brand_alignment_score": 0.7
        }

        request = SceneDecompositionRequest(
            video_type=VideoType.MUSIC_VIDEO,
            total_duration=90,
            prompt_analysis=prompt_analysis
        )

        response = await scene_service.decompose_video(request)

        assert response.video_type == VideoType.MUSIC_VIDEO
        assert response.total_duration == 90
        assert len(response.scenes) >= 8  # Should have multiple scenes

        total_duration = sum(s.duration for s in response.scenes)
        assert total_duration == pytest.approx(90.0, abs=0.1)

        # Check that scenes have basic structure
        for scene in response.scenes:
            assert scene.scene_id is not None
            assert scene.title is not None
            assert scene.visual_style is not None

        print(f"🎵 Music video: {len(response.scenes)} scenes, {total_duration:.1f}s total")

    @pytest.mark.asyncio
    async def test_error_handling(self, scene_service):
        """Test error handling in scene decomposition"""

        # Test with invalid video type (if we had more types)
        # For now, test with empty prompt analysis
        request = SceneDecompositionRequest(
            video_type=VideoType.AD,
            total_duration=30,
            prompt_analysis={},  # Empty analysis
            brand_config=None
        )

        # Should not crash, should handle gracefully
        response = await scene_service.decompose_video(request)
        assert response is not None
        assert len(response.scenes) == 3  # Should still create scenes

    def test_scene_model_validation(self):
        """Test that scene models validate correctly"""
        from models.scene_decomposition import Scene, SceneType, VisualStyle, BrandReference

        # Valid scene
        scene = Scene(
            scene_id="test_001",
            scene_type=SceneType.INTRODUCTION,
            start_time=0.0,
            duration=6.0,
            end_time=6.0,
            title="Welcome to ChronoLux",
            content_description="Introduce the luxury watch brand with elegant visuals",
            narrative_purpose="Hook the viewer and establish brand credibility",
            visual_style=VisualStyle.BRAND_SHOWCASE,
            key_elements=[],
            brand_references=BrandReference(colors=["#D4AF37", "#1A1A1A"])
        )

        assert scene.scene_id == "test_001"
        assert scene.scene_type == SceneType.INTRODUCTION

        # Test that end_time validation works
        assert scene.end_time == scene.start_time + scene.duration
