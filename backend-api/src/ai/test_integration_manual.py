#!/usr/bin/env python3
"""Manual integration test for Block A services"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.prompt_analysis_service import PromptAnalysisService
from services.scene_decomposition_service import SceneDecompositionService
from services.brand_analysis_service import BrandAnalysisService
from models.prompt_analysis import AnalysisRequest
from models.scene_decomposition import SceneDecompositionRequest, VideoType


async def test_block_a_integration():
    """Test the full Block A integration: prompt → analysis → scenes"""
    print("Testing Block A Integration...")
    print("=" * 50)

    # Test prompt analysis
    print("\n1. Testing Prompt Analysis...")
    prompt_service = PromptAnalysisService(openai_api_key="dummy", use_mock=True)
    analysis_request = AnalysisRequest(
        prompt="Create a professional business video for a SaaS platform that helps companies streamline operations with elegant design and corporate branding."
    )
    analysis_response = await prompt_service.analyze_prompt(analysis_request)

    print("✅ Prompt analysis completed")
    print(f"   Tone: {analysis_response.analysis.tone}")
    print(f"   Style: {analysis_response.analysis.style}")
    print(f"   Target Audience: {analysis_response.analysis.target_audience}")

    # Test brand analysis
    print("\n2. Testing Brand Analysis...")
    brand_service = BrandAnalysisService()
    brand_config = {
        "name": "TechFlow",
        "colors": ["#0066CC", "#FFFFFF", "#333333"],
        "style": "corporate",
        "logo_url": "https://example.com/logo.png"
    }
    brand_response = await brand_service.analyze_brand(brand_config)

    print("✅ Brand analysis completed")
    print(f"   Brand Name: {brand_response.brand_config.name}")
    print(f"   Style Vector: {len(brand_response.style_vector)} dimensions")

    # Test scene decomposition
    print("\n3. Testing Scene Decomposition...")
    scene_service = SceneDecompositionService()
    scene_request = SceneDecompositionRequest(
        video_type=VideoType.AD,
        total_duration=30,
        min_scene_duration=3.0,
        prompt_analysis=analysis_response.model_dump(),
        brand_config=brand_response.model_dump()
    )

    scene_response = await scene_service.decompose_video(scene_request)

    print("✅ Scene decomposition completed")
    print(f"   Video Type: {scene_response.video_type}")
    print(f"   Total Scenes: {len(scene_response.scenes)}")
    print(f"   Total Duration: {scene_response.total_duration}s")
    print(f"   Average Scene Duration: {scene_response.average_scene_duration:.1f}s")
    # Validate scene structure
    print("\n4. Validating Scene Structure...")
    for i, scene in enumerate(scene_response.scenes):
        print(f"   Scene {i+1}: {scene.scene_type.value} ({scene.duration:.1f}s)")
        print(f"      Title: {scene.title}")
        print(f"      Key Elements: {len(scene.key_elements)}")

    # Validate total duration
    total_scene_duration = sum(scene.duration for scene in scene_response.scenes)
    duration_match = abs(total_scene_duration - scene_response.total_duration) < 0.1

    print("\n5. Final Validation:")
    print(f"   Duration Match: {'✅' if duration_match else '❌'} ({total_scene_duration:.1f}s vs {scene_response.total_duration}s)")
    print(f"   Scenes Generated: {'✅' if len(scene_response.scenes) > 0 else '❌'}")
    print(f"   Brand Consistency: {'✅' if scene_response.brand_consistency_score > 0.7 else '⚠️'} ({scene_response.brand_consistency_score:.2f})")

    print("\n" + "=" * 50)
    if duration_match and len(scene_response.scenes) > 0:
        print("🎉 BLOCK A INTEGRATION TEST PASSED!")
        return True
    else:
        print("❌ BLOCK A INTEGRATION TEST FAILED!")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_block_a_integration())
    sys.exit(0 if success else 1)
