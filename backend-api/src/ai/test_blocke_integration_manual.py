#!/usr/bin/env python3
"""Manual integration test for Block E services"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.style_vector_builder_service import StyleVectorBuilderService
from services.brand_harmony_service import BrandHarmonyService
from services.micro_prompt_builder_service import MicroPromptBuilderService
from services.scene_decomposition_service import SceneDecompositionService
from services.prompt_analysis_service import PromptAnalysisService
from models.brand_config import BrandConfig
from models.prompt_analysis import AnalysisRequest
from models.scene_decomposition import SceneDecompositionRequest, VideoType


async def test_block_e_integration():
    """Test the full Block E integration: brand config → style vector → harmony → micro prompts"""
    print("Testing Block E Integration...")
    print("=" * 50)

    # Test brand configuration
    print("\n1. Setting up brand configuration...")
    brand_config = BrandConfig(
        name="TechFlow",
        colors=["#0066CC", "#FFFFFF", "#333333"],
        style="corporate",
        logo_url="https://example.com/logo.png"
    )
    print("✅ Brand configuration created")

    # Test prompt analysis
    print("\n2. Testing prompt analysis...")
    prompt_service = PromptAnalysisService(openai_api_key="dummy", use_mock=True)
    analysis_request = AnalysisRequest(
        prompt="Create a professional business video for a SaaS platform that helps companies streamline operations with elegant design and corporate branding."
    )
    analysis_response = await prompt_service.analyze_prompt(analysis_request)
    print("✅ Prompt analysis completed")

    # Test style vector builder
    print("\n3. Testing style vector builder...")
    style_service = StyleVectorBuilderService(use_mock=True)
    style_vector = await style_service.build_style_vector(
        brand_config=brand_config,
        prompt_analysis=analysis_response.analysis
    )
    print("✅ Style vector built")
    print(f"   Dimensions: {len(style_vector.dimensions)}")
    print(f"   Confidence: {style_vector.confidence_score:.2f}")

    # Test brand harmony analysis
    print("\n4. Testing brand harmony analysis...")
    harmony_service = BrandHarmonyService(use_mock=True)
    harmony_analysis = await harmony_service.analyze_harmony(
        brand_config=brand_config,
        style_vector=style_vector
    )
    print("✅ Brand harmony analysis completed")
    print(f"   Overall harmony: {harmony_analysis.overall_score:.2f}")
    print(f"   Accessibility score: {harmony_analysis.accessibility_score:.2f}")

    # Test scene decomposition
    print("\n5. Testing scene decomposition...")
    scene_service = SceneDecompositionService()
    scene_request = SceneDecompositionRequest(
        video_type=VideoType.AD,
        total_duration=30,
        min_scene_duration=3.0,
        prompt_analysis=analysis_response.model_dump(),
        brand_config=brand_config.model_dump()
    )
    scene_response = await scene_service.decompose_video(scene_request)
    print("✅ Scene decomposition completed")
    print(f"   Scenes generated: {len(scene_response.scenes)}")

    # Test micro prompt builder
    print("\n6. Testing micro prompt builder...")
    prompt_builder = MicroPromptBuilderService()
    micro_request = {
        "scenes": scene_response.scenes,
        "brand_config": brand_config.model_dump(),
        "brand_harmony_analysis": harmony_analysis.model_dump(),
        "brand_style_vector": style_vector.model_dump(),
        "prompt_analysis": analysis_response.model_dump()
    }

    # Convert to proper request format
    from models.micro_prompt import MicroPromptRequest
    micro_prompt_request = MicroPromptRequest(**micro_request)

    micro_response = await prompt_builder.build_micro_prompts(micro_prompt_request)
    print("✅ Micro prompts built")
    print(f"   Prompts generated: {len(micro_response.prompts)}")

    # Validate integration
    print("\n7. Validating Block E integration...")

    # Check that all services produced outputs
    services_worked = (
        style_vector is not None and
        harmony_analysis is not None and
        len(scene_response.scenes) > 0 and
        len(micro_response.prompts) > 0
    )

    # Check consistency enforcement
    consistency_enforced = all(
        prompt.confidence_score > 0.7 for prompt in micro_response.prompts
    )

    # Check brand integration
    brand_integrated = all(
        "TechFlow" in prompt.positive_prompt or "corporate" in prompt.positive_prompt
        for prompt in micro_response.prompts[:1]  # Check first prompt
    )

    print("\n8. Final Validation:")
    print(f"   All services working: {'✅' if services_worked else '❌'}")
    print(f"   Consistency enforced: {'✅' if consistency_enforced else '⚠️'}")
    print(f"   Brand integration: {'✅' if brand_integrated else '⚠️'}")

    print("\n" + "=" * 50)
    if services_worked:
        print("🎉 BLOCK E INTEGRATION TEST PASSED!")
        return True
    else:
        print("❌ BLOCK E INTEGRATION TEST FAILED!")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_block_e_integration())
    sys.exit(0 if success else 1)
