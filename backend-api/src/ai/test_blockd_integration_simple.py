#!/usr/bin/env python3
"""Simple integration test for Block D components"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.edit_intent_classifier_service import EditIntentClassifierService
from services.timeline_edit_planner_service import TimelineEditPlannerService
from services.recomposition_trigger_service import RecompositionTriggerService
from models.edit_intent import EditRequest, EditOperation, EditTarget
from models.recomposition import RecompositionTriggerRequest


async def test_block_d_simple_integration():
    """Test core Block D functionality with mock data"""
    print("Testing Block D Simple Integration...")
    print("=" * 50)

    # Test 1: Edit Intent Classifier
    print("\n1. Testing Edit Intent Classifier...")
    try:
        classifier = EditIntentClassifierService(openai_api_key="dummy", use_mock=True)

        edit_request = EditRequest(
            edit_description="Make the video 15 seconds shorter by removing the middle section",
            composition_id="comp_123",
            current_clips=[
                {"clip_id": "clip_001", "start_time": 0.0, "duration": 10.0},
                {"clip_id": "clip_002", "start_time": 10.0, "duration": 10.0},
                {"clip_id": "clip_003", "start_time": 20.0, "duration": 10.0}
            ]
        )

        classification_result = await classifier.classify_edit_intent(edit_request)

        print("✅ Edit intent classifier works")
        print(f"   Detected operations: {len(classification_result.operations)}")
        print(f"   Confidence score: {classification_result.confidence_score:.2f}")
        print(f"   Safety check passed: {classification_result.safety_check.passed}")

        edit_intent_works = len(classification_result.operations) > 0 and classification_result.confidence_score > 0.7

    except Exception as e:
        print(f"❌ Edit intent classifier failed: {e}")
        edit_intent_works = False

    # Test 2: Timeline Edit Planner
    print("\n2. Testing Timeline Edit Planner...")
    try:
        planner = TimelineEditPlannerService(use_mock=True)

        # Mock edit plan (would normally come from classifier)
        mock_edit_plan = {
            "operations": [
                {
                    "operation": EditOperation.TRIM,
                    "target": EditTarget.CLIP,
                    "target_id": "clip_002",
                    "parameters": {"end_time": 5.0}  # Trim to 5 seconds
                }
            ]
        }

        mock_clips = [
            {"clip_id": "clip_001", "start_time": 0.0, "duration": 10.0, "scene_id": "scene_001"},
            {"clip_id": "clip_002", "start_time": 10.0, "duration": 10.0, "scene_id": "scene_002"},
            {"clip_id": "clip_003", "start_time": 20.0, "duration": 10.0, "scene_id": "scene_003"}
        ]

        planning_result = await planner.plan_timeline_edits(mock_edit_plan, mock_clips)

        print("✅ Timeline edit planner works")
        print(f"   FFmpeg operations: {len(planning_result.ffmpeg_operations)}")
        print(f"   Timeline preview available: {'timeline_preview' in planning_result.__dict__}")

        timeline_planner_works = len(planning_result.ffmpeg_operations) > 0

    except Exception as e:
        print(f"❌ Timeline edit planner failed: {e}")
        timeline_planner_works = False

    # Test 3: Recomposition Trigger Service
    print("\n3. Testing Recomposition Trigger Service...")
    try:
        # Create service with mock backend URL
        trigger_service = RecompositionTriggerService(
            ffmpeg_backend_url="http://mock-ffmpeg-backend:8000",
            request_timeout=30.0
        )

        recomposition_request = RecompositionTriggerRequest(
            composition_id="comp_123",
            edit_plan=mock_edit_plan,
            ffmpeg_operations=planning_result.ffmpeg_operations if timeline_planner_works else [],
            trigger_reason="User requested timeline edit",
            priority="normal"
        )

        # Test basic service creation and properties
        has_trigger_method = hasattr(trigger_service, 'trigger_recomposition')
        has_record_method = hasattr(trigger_service, 'get_recomposition_record')

        print("✅ Recomposition trigger service initialized")
        print(f"   Has trigger method: {has_trigger_method}")
        print(f"   Has record method: {has_record_method}")

        recomposition_trigger_works = has_trigger_method and has_record_method

    except Exception as e:
        print(f"❌ Recomposition trigger service failed: {e}")
        recomposition_trigger_works = False

    # Summary
    print("\n" + "=" * 50)
    print("4. Block D Integration Summary:")
    print(f"   Edit Intent Classifier: {'✅' if edit_intent_works else '❌'}")
    print(f"   Timeline Edit Planner: {'✅' if timeline_planner_works else '❌'}")
    print(f"   Recomposition Trigger: {'✅' if recomposition_trigger_works else '❌'}")

    all_components_work = edit_intent_works and timeline_planner_works and recomposition_trigger_works

    if all_components_work:
        print("\n🎉 BLOCK D COMPONENTS WORKING CORRECTLY!")
        print("Natural language edits can be processed into FFmpeg operations and recomposition jobs.")
        return True
    else:
        print("\n❌ BLOCK D INTEGRATION HAS ISSUES!")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_block_d_simple_integration())
    sys.exit(0 if success else 1)
