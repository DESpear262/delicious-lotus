"""
Tests for Prompt Analysis Service - PR 101
"""

import pytest
from ai.services.prompt_analysis_service import PromptAnalysisService
from ai.services.brand_analysis_service import BrandAnalysisService
from ai.models.prompt_analysis import AnalysisRequest, Tone, Style, PromptAnalysis
from ai.models.brand_config import BrandConfig, VisualTheme


class TestPromptAnalysisService:
    """Test the prompt analysis service"""

    @pytest.fixture
    def mock_service(self):
        """Create a service instance with mock mode enabled"""
        return PromptAnalysisService(openai_api_key="dummy", use_mock=True)

    @pytest.mark.asyncio
    async def test_analyze_business_prompt(self, mock_service):
        """Test analysis of a business/professional prompt"""
        request = AnalysisRequest(
            prompt="Create a professional video showcasing our innovative SaaS platform that helps businesses streamline their operations and increase productivity."
        )

        response = await mock_service.analyze_prompt(request)

        assert response.status == "success"
        assert response.analysis.tone == Tone.PROFESSIONAL
        assert response.analysis.target_audience.name == "BUSINESS"
        assert "productivity" in response.analysis.key_themes
        assert response.analysis.confidence_score > 0.8

    @pytest.mark.asyncio
    async def test_analyze_creative_prompt(self, mock_service):
        """Test analysis of a creative/enthusiastic prompt"""
        request = AnalysisRequest(
            prompt="Make an exciting video about our new energy drink that gives you wings! Perfect for young adults who want to live life to the fullest."
        )

        response = await mock_service.analyze_prompt(request)

        assert response.status == "success"
        assert response.analysis.tone in [Tone.ENTHUSIASTIC, Tone.ENERGETIC]
        assert response.analysis.visual_theme == VisualTheme.VIBRANT
        assert response.analysis.target_audience.name in ["TEENS", "CONSUMERS"]

    @pytest.mark.asyncio
    async def test_analyze_minimalist_prompt(self, mock_service):
        """Test analysis of a minimalist/calm prompt"""
        request = AnalysisRequest(
            prompt="A serene video meditation app that helps users find peace and mindfulness in their daily lives."
        )

        response = await mock_service.analyze_prompt(request)

        assert response.status == "success"
        assert response.analysis.tone == Tone.CALM
        assert response.analysis.style in [Style.MINIMALIST, Style.CLASSIC]
        assert response.analysis.pacing == "slow"

    @pytest.mark.asyncio
    async def test_processing_time_tracking(self, mock_service):
        """Test that processing time is tracked"""
        request = AnalysisRequest(prompt="Test prompt for processing time")

        response = await mock_service.analyze_prompt(request)

        assert response.processing_time > 0
        assert response.processing_time < 1.0  # Should be very fast for mock

    @pytest.mark.asyncio
    async def test_mock_response_structure(self, mock_service):
        """Test that mock responses have all required fields"""
        request = AnalysisRequest(prompt="Test prompt")

        response = await mock_service.analyze_prompt(request)

        # Check all required fields are present
        analysis = response.analysis
        assert analysis.tone
        assert analysis.style
        assert analysis.narrative_intent
        assert analysis.narrative_structure
        assert analysis.target_audience
        assert analysis.visual_theme
        assert analysis.imagery_style
        assert analysis.color_palette
        assert analysis.pacing
        assert analysis.music_style
        assert analysis.confidence_score >= 0.0
        assert analysis.confidence_score <= 1.0
        assert analysis.original_prompt == "Test prompt"
        assert analysis.model_version == "mock-v1.0"

    @pytest.mark.asyncio
    async def test_key_elements_extraction(self, mock_service):
        """Test that key elements are properly extracted"""
        request = AnalysisRequest(
            prompt="Showcase our amazing new smartphone with incredible camera features and long battery life."
        )

        response = await mock_service.analyze_prompt(request)

        # Should identify product as key element
        key_elements = response.analysis.key_elements
        assert len(key_elements) > 0
        assert any("smartphone" in elem.description.lower() or "product" in elem.element_type.lower()
                  for elem in key_elements)

    @pytest.mark.asyncio
    async def test_theme_consistency(self, mock_service):
        """Test that themes are extracted for consistency"""
        request = AnalysisRequest(
            prompt="A video about innovation and technology transforming the future of healthcare."
        )

        response = await mock_service.analyze_prompt(request)

        themes = response.analysis.key_themes
        assert "technology" in themes or "innovation" in themes
        assert len(themes) > 0


class TestBrandAnalysisService:
    """Test the brand analysis service"""

    @pytest.fixture
    def mock_brand_service(self):
        """Create a brand analysis service instance with mock mode enabled"""
        return BrandAnalysisService(openai_api_key="dummy", use_mock=True)

    @pytest.fixture
    def sample_prompt_analysis(self):
        """Create a sample prompt analysis for testing"""
        return PromptAnalysis(
            tone=Tone.PROFESSIONAL,
            style=Style.MODERN,
            narrative_intent="Create engaging professional content",
            narrative_structure="problem_solution",
            target_audience="business",
            key_themes=["technology", "efficiency"],
            key_messages=["Improve productivity", "Save time"],
            visual_theme=VisualTheme.NEUTRAL,
            imagery_style="photorealistic",
            color_palette={"primary": ["#0066CC"], "secondary": ["#333333"]},
            product_focus="SaaS Platform",
            pacing="moderate",
            music_style="corporate",
            confidence_score=0.85,
            original_prompt="Test prompt",
            analysis_timestamp="2025-11-14T15:00:00Z",
            model_version="mock-v1.0"
        )

    @pytest.mark.asyncio
    async def test_analyze_with_explicit_brand_config(self, mock_brand_service, sample_prompt_analysis):
        """Test brand analysis with explicit brand configuration"""
        brand_config = {
            "name": "TechCorp",
            "category": "technology",
            "colors": {
                "primary": ["#0066CC", "#003366"],
                "secondary": ["#FF6600"]
            }
        }

        result = await mock_brand_service.analyze_brand(sample_prompt_analysis, brand_config)

        assert isinstance(result, BrandConfig)
        assert result.name == "TechCorp"
        assert result.category == "technology"
        assert len(result.colors.primary) >= 1

    @pytest.mark.asyncio
    async def test_analyze_with_implicit_brand_from_prompt(self, mock_brand_service, sample_prompt_analysis):
        """Test brand analysis when brand info is inferred from prompt"""
        # Prompt analysis indicates product focus
        result = await mock_brand_service.analyze_brand(sample_prompt_analysis)

        # Should create a brand config based on the product focus
        assert isinstance(result, BrandConfig)
        assert "SaaS" in result.name or result.name != "Corporate Brand"

    @pytest.mark.asyncio
    async def test_analyze_no_brand_info(self, mock_brand_service):
        """Test brand analysis when no brand information is available"""
        # Create prompt analysis with no product focus
        prompt_analysis = PromptAnalysis(
            tone=Tone.CASUAL,
            style=Style.CINEMATIC,
            narrative_intent="Create entertaining content",
            narrative_structure="storytelling",
            target_audience="general",
            key_themes=["entertainment"],
            visual_theme=VisualTheme.BRIGHT,
            imagery_style="animation",
            color_palette={"primary": ["#FF0000"]},
            pacing="fast",
            music_style="energetic",
            confidence_score=0.8,
            original_prompt="Fun animation video",
            analysis_timestamp="2025-11-14T15:00:00Z",
            model_version="mock-v1.0"
        )

        result = await mock_brand_service.analyze_brand(prompt_analysis)

        # Should return default corporate brand when no specific brand info
        assert isinstance(result, BrandConfig)
        assert result.name == "Corporate Brand"

    @pytest.mark.asyncio
    async def test_incomplete_brand_config_completion(self, mock_brand_service, sample_prompt_analysis):
        """Test completion of incomplete brand configuration"""
        incomplete_config = {
            "name": "TestBrand",
            "colors": {
                "primary": ["#FF0000"]
            }
            # Missing description, typography, visual_style, etc.
        }

        result = await mock_brand_service.analyze_brand(sample_prompt_analysis, incomplete_config)

        assert isinstance(result, BrandConfig)
        assert result.name == "TestBrand"
        # Mock service should fill in missing fields
        assert result.description is not None
        assert result.typography is not None

    @pytest.mark.asyncio
    async def test_brand_config_validation(self):
        """Test that brand config validation works"""
        # Valid config should work
        valid_config = {
            "name": "ValidBrand",
            "colors": {
                "primary": ["#FF0000", "#00FF00"]
            }
        }
        brand_config = BrandConfig(**valid_config)
        assert brand_config.name == "ValidBrand"

        # Invalid hex color should fail
        invalid_config = {
            "name": "InvalidBrand",
            "colors": {
                "primary": ["invalid-color"]
            }
        }

        with pytest.raises(Exception):  # ValidationError
            BrandConfig(**invalid_config)

    @pytest.mark.asyncio
    async def test_brand_merge_with_prompt_insights(self, mock_brand_service, sample_prompt_analysis):
        """Test that brand config gets enhanced with prompt analysis insights"""
        brand_config = {
            "name": "TechBrand",
            "category": "technology",
            "colors": {
                "primary": ["#0066CC"]
            }
        }

        result = await mock_brand_service.analyze_brand(sample_prompt_analysis, brand_config)

        # Should have added prompt analysis context
        assert result.other is not None
        assert "prompt_analysis_context" in result.other
        context = result.other["prompt_analysis_context"]
        assert context["tone"] == "professional"
        assert "technology" in context["key_themes"]
