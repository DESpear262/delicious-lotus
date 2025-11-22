#!/usr/bin/env python3
"""Simple test script for prompt analysis"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.prompt_analysis_service import PromptAnalysisService
from models.prompt_analysis import AnalysisRequest


async def test_prompt_analysis():
    """Test the prompt analysis service"""
    print("Testing Prompt Analysis Service...")

    # Test with mock service
    service = PromptAnalysisService(openai_api_key="dummy", use_mock=True)

    # Test business prompt
    request = AnalysisRequest(prompt="Create a professional business video showcasing our innovative SaaS platform that helps businesses streamline operations.")
    response = await service.analyze_prompt(request)

    print("PASS: Analysis completed successfully")
    print(f"  - Tone: {response.analysis.tone}")
    print(f"  - Style: {response.analysis.style}")
    print(f"  - Target Audience: {response.analysis.target_audience}")
    print(f"  - Confidence Score: {response.analysis.confidence_score}")
    print(f"  - Processing Time: {response.processing_time:.3f}s")
    print(f"  - Key Themes: {response.analysis.key_themes}")

    assert response.status == "success"
    assert response.analysis.confidence_score > 0.8
    assert len(response.analysis.key_themes) > 0

    print("PASS: All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_prompt_analysis())
