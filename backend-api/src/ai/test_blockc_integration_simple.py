#!/usr/bin/env python3
"""Simple integration test for Block C components"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.micro_prompt_builder_service import MicroPromptBuilderService
from services.clip_assembly_service import ClipAssemblyService
from core.replicate_client import ReplicateModelClient
from models.micro_prompt import MicroPromptRequest
from models.clip_assembly import ClipAssemblyRequest
from models.replicate_client import ClientConfig, GenerateClipRequest
from models.scene_decomposition import Scene, SceneType, VisualStyle


async def test_block_c_simple_integration():
    """Test core Block C functionality with mock data"""
    print("Testing Block C Simple Integration...")
    print("=" * 50)

    # Create mock scene
    mock_scene = Scene(
        scene_id="test_scene_001",
        scene_type=SceneType.DEVELOPMENT,
        start_time=0.0,
        duration=6.0,
        end_time=6.0,
        title="Main Content Scene",
        content_description="Demonstrate product features with professional styling",
        narrative_purpose="Showcase key product benefits",
        visual_style=VisualStyle.DEMONSTRATION,
        key_elements=[],
        brand_references=None,
        pacing="moderate",
        transition_hint="fade"
    )

    # Create mock brand and analysis data
    mock_brand_config = {
        "name": "TechFlow",
        "colors": ["#0066CC", "#FFFFFF"],
        "style": "corporate"
    }

    mock_brand_style_vector = {
        "dimensions": {
            "brand_recognition": 0.8,
            "consistency": 0.9,
            "adaptability": 0.7
        },
        "confidence_score": 0.85
    }

    mock_brand_harmony = {
        "overall_score": 0.82,
        "accessibility_score": 0.95,
        "recommendations": []
    }

    mock_prompt_analysis = {
        "tone": "professional",
        "style": "corporate",
        "target_audience": "business_professionals"
    }

    # Test 1: Micro Prompt Builder
    print("\n1. Testing Micro Prompt Builder...")
    try:
        prompt_builder = MicroPromptBuilderService()

        micro_request = MicroPromptRequest(
            scenes=[mock_scene],
            brand_config=mock_brand_config,
            brand_harmony_analysis=mock_brand_harmony,
            brand_style_vector=mock_brand_style_vector,
            prompt_analysis=mock_prompt_analysis
        )

        micro_response = await prompt_builder.build_micro_prompts(micro_request)

        print("✅ Micro prompt builder works")
        print(f"   Generated {len(micro_response.prompts)} prompts")
        if micro_response.prompts:
            first_prompt = micro_response.prompts[0]
            print(f"   First prompt confidence: {first_prompt.confidence_score:.2f}")
            print(f"   Has positive prompt: {bool(first_prompt.positive_prompt)}")
            print(f"   Has negative prompt: {bool(first_prompt.negative_prompt)}")

        micro_prompts_worked = len(micro_response.prompts) > 0

    except Exception as e:
        print(f"❌ Micro prompt builder failed: {e}")
        micro_prompts_worked = False

    # Test 2: Replicate Client (with mock)
    print("\n2. Testing Replicate Client (mock)...")
    try:
        client_config = ClientConfig(
            api_token="mock_token",
            default_model="google/veo-3.1-fast",
            max_retries=1,
            timeout_seconds=30
        )

        replicate_client = ReplicateModelClient(client_config)
        print("✅ Replicate client initialized")

        # Test input preparation (without actual API call)
        test_request = GenerateClipRequest(
            prompt="Test prompt",
            duration_seconds=6.0,
            aspect_ratio="16:9",
            style="professional"
        )

        prepared_inputs = replicate_client._prepare_model_inputs(test_request)
        print("✅ Input preparation works")
        print(f"   Prepared inputs keys: {list(prepared_inputs.keys())}")

        replicate_client_works = True

    except Exception as e:
        print(f"❌ Replicate client failed: {e}")
        replicate_client_works = False

    # Test 3: Clip Assembly Service (basic functionality)
    print("\n3. Testing Clip Assembly Service...")
    try:
        # Create service without actual Redis/DB connections
        clip_service = ClipAssemblyService(redis_url="mock://", db_config={})
        print("✅ Clip assembly service initialized")

        # Test basic properties
        has_redis_property = hasattr(clip_service, 'redis_client')
        has_db_property = hasattr(clip_service, 'db_connection')

        print(f"   Has Redis client property: {has_redis_property}")
        print(f"   Has DB connection property: {has_db_property}")

        clip_assembly_works = has_redis_property and has_db_property

    except Exception as e:
        print(f"❌ Clip assembly service failed: {e}")
        clip_assembly_works = False

    # Summary
    print("\n" + "=" * 50)
    print("4. Block C Integration Summary:")
    print(f"   Micro Prompt Builder: {'✅' if micro_prompts_worked else '❌'}")
    print(f"   Replicate Client: {'✅' if replicate_client_works else '❌'}")
    print(f"   Clip Assembly Service: {'✅' if clip_assembly_works else '❌'}")

    all_components_work = micro_prompts_worked and replicate_client_works and clip_assembly_works

    if all_components_work:
        print("\n🎉 BLOCK C COMPONENTS WORKING CORRECTLY!")
        return True
    else:
        print("\n❌ BLOCK C INTEGRATION HAS ISSUES!")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_block_c_simple_integration())
    sys.exit(0 if success else 1)
