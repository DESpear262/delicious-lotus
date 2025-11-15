"""
Unit tests for Style Vector Builder Service - PR #501
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from ..models.brand_config import BrandConfig, BrandCategory, ColorPalette, Typography
from ..models.prompt_analysis import PromptAnalysis
from ..models.brand_style_vector import BrandStyleVector, StyleDimensions
from ..services.style_vector_builder_service import StyleVectorBuilderService, create_style_vector_cache_key


class TestStyleVectorBuilderService:
    """Test cases for StyleVectorBuilderService"""

    @pytest.fixture
    def sample_brand_config(self):
        """Create a sample brand configuration for testing"""
        return BrandConfig(
            name="TestBrand",
            category=BrandCategory.CORPORATE,
            colors=ColorPalette(
                primary=["#1a1a1a", "#d4af37"],
                secondary=["#666666"],
                background="#ffffff"
            ),
            typography=Typography(
                primary_font="Arial",
                secondary_font="Helvetica"
            ),
            tone="Professional and trustworthy",
            personality_traits=["reliable", "innovative", "customer-focused"],
            values=["integrity", "excellence", "innovation"],
            audience=["business professionals", "tech-savvy consumers"],
            visual_style=None,
            content_guidelines="Maintain professional tone, focus on quality"
        )

    @pytest.fixture
    def sample_prompt_analysis(self):
        """Create a sample prompt analysis for testing"""
        return PromptAnalysis(
            primary_intent="Create a professional product demonstration video",
            tone="professional",
            content_type="advertisement",
            target_audience="business professionals",
            key_themes=["innovation", "quality", "trust"],
            sentiment="positive",
            confidence_score=0.85
        )

    @pytest.fixture
    def service(self):
        """Create a StyleVectorBuilderService instance"""
        return StyleVectorBuilderService(use_mock=True)

    @pytest.fixture
    def service_with_redis(self):
        """Create a service with mock Redis client"""
        mock_redis = AsyncMock()
        return StyleVectorBuilderService(redis_client=mock_redis, use_mock=True)

    def test_service_initialization(self):
        """Test service initialization"""
        service = StyleVectorBuilderService()
        assert service.redis_client is None
        assert service.use_mock is False
        assert service.cache_ttl == 3600

        service_with_redis = StyleVectorBuilderService(redis_client=MagicMock())
        assert service_with_redis.redis_client is not None

    @pytest.mark.asyncio
    async def test_build_style_vector_basic(self, service, sample_brand_config, sample_prompt_analysis):
        """Test basic style vector building"""
        result = await service.build_style_vector(sample_brand_config, sample_prompt_analysis)

        assert isinstance(result, BrandStyleVector)
        assert result.brand_name == "TestBrand"
        assert result.content_description == "Create a professional product demonstration video"
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.generation_method == "computed"

        # Check that dimensions are within valid ranges
        dims = result.dimensions
        assert 0.0 <= dims.brand_recognition <= 1.0
        assert 0.0 <= dims.brand_consistency <= 1.0
        assert 0.0 <= dims.color_harmony <= 1.0
        assert 0.0 <= dims.visual_appeal <= 1.0
        assert 0.0 <= dims.tone_alignment <= 1.0
        assert 0.0 <= dims.adaptability <= 1.0
        assert 0.0 <= dims.creativity <= 1.0
        assert 0.0 <= dims.audience_fit <= 1.0

    @pytest.mark.asyncio
    async def test_build_style_vector_with_caching(self, service_with_redis, sample_brand_config, sample_prompt_analysis):
        """Test style vector building with Redis caching"""
        cache_key = "test_key"

        # Mock Redis to return None (cache miss)
        service_with_redis.redis_client.get.return_value = None

        result = await service_with_redis.build_style_vector(
            sample_brand_config, sample_prompt_analysis, cache_key
        )

        assert isinstance(result, BrandStyleVector)
        # Verify Redis interactions
        service_with_redis.redis_client.get.assert_called_once()
        service_with_redis.redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_vector_retrieval(self, service_with_redis, sample_brand_config, sample_prompt_analysis):
        """Test retrieving cached style vector"""
        cache_key = "test_key"
        cached_vector = BrandStyleVector(
            dimensions=StyleDimensions(
                brand_recognition=0.8,
                brand_consistency=0.7,
                color_harmony=0.9,
                visual_appeal=0.8,
                tone_alignment=0.85,
                adaptability=0.75,
                creativity=0.7,
                audience_fit=0.8
            ),
            brand_name="CachedBrand",
            content_description="Cached content",
            confidence_score=0.9,
            original_brand_config={},
            prompt_analysis_summary={},
            generated_at=datetime.utcnow().isoformat() + "Z",
            generation_method="cached"
        )

        # Mock Redis to return cached data
        service_with_redis.redis_client.get.return_value = cached_vector.json()

        result = await service_with_redis.build_style_vector(
            sample_brand_config, sample_prompt_analysis, cache_key
        )

        assert result.brand_name == "CachedBrand"
        assert result.generation_method == "cached"
        service_with_redis.redis_client.get.assert_called_once()
        # Should not call setex since we got a cache hit
        service_with_redis.redis_client.setex.assert_not_called()

    def test_brand_recognition_calculation(self, service, sample_brand_config):
        """Test brand recognition score calculation"""
        score = service._calculate_brand_recognition(sample_brand_config)

        # Corporate category should give higher score
        assert 0.5 <= score <= 1.0

        # Test with luxury brand
        luxury_config = sample_brand_config.copy()
        luxury_config.category = BrandCategory.LUXURY
        luxury_score = service._calculate_brand_recognition(luxury_config)
        assert luxury_score >= score  # Should be higher

    def test_brand_consistency_calculation(self, service, sample_brand_config):
        """Test brand consistency score calculation"""
        score = service._calculate_brand_consistency(sample_brand_config)

        # Should be between 0 and 1
        assert 0.0 <= score <= 1.0

        # With our sample config, should be fairly high
        assert score > 0.5

    def test_color_harmony_calculation(self, service, sample_brand_config):
        """Test color harmony score calculation"""
        score = service._calculate_color_harmony(sample_brand_config)

        # Should have good harmony with primary + secondary colors
        assert 0.5 <= score <= 1.0

        # Test with minimal colors
        minimal_config = sample_brand_config.copy()
        minimal_config.colors = ColorPalette(primary=["#000000"])
        minimal_score = service._calculate_color_harmony(minimal_config)
        assert minimal_score < score

    def test_visual_appeal_calculation(self, service, sample_brand_config):
        """Test visual appeal score calculation"""
        score = service._calculate_visual_appeal(sample_brand_config)

        # Corporate category should give decent appeal
        assert 0.4 <= score <= 1.0

    def test_tone_alignment_calculation(self, service, sample_brand_config):
        """Test tone alignment score calculation"""
        score = service._calculate_tone_alignment(sample_brand_config)

        # Should be good with defined tone and personality traits
        assert 0.5 <= score <= 1.0

        # Test with no tone
        no_tone_config = sample_brand_config.copy()
        no_tone_config.tone = None
        no_tone_score = service._calculate_tone_alignment(no_tone_config)
        assert no_tone_score < score

    def test_adaptability_calculation(self, service, sample_brand_config):
        """Test adaptability score calculation"""
        score = service._calculate_adaptability(sample_brand_config)

        assert 0.0 <= score <= 1.0

        # Corporate brands should be reasonably adaptable
        assert 0.4 <= score <= 0.8

    def test_creativity_calculation(self, service, sample_brand_config):
        """Test creativity score calculation"""
        score = service._calculate_creativity(sample_brand_config)

        assert 0.0 <= score <= 1.0

        # Should be moderate for corporate brand
        assert 0.3 <= score <= 0.7

    def test_audience_fit_calculation(self, service, sample_brand_config):
        """Test audience fit score calculation"""
        score = service._calculate_audience_fit(sample_brand_config)

        # Should be good with defined audience
        assert 0.5 <= score <= 1.0

        # Test with no audience
        no_audience_config = sample_brand_config.copy()
        no_audience_config.audience = []
        no_audience_score = service._calculate_audience_fit(no_audience_config)
        assert no_audience_score < score

    def test_prompt_adjustments(self, service, sample_brand_config, sample_prompt_analysis):
        """Test that prompt analysis adjusts style dimensions"""
        base_dims = service._extract_brand_dimensions(sample_brand_config)
        adjusted_dims = service._adjust_for_prompt(base_dims, sample_prompt_analysis)

        # Professional tone should improve tone alignment
        assert adjusted_dims.tone_alignment >= base_dims.tone_alignment

        # Advertisement content should improve creativity
        assert adjusted_dims.creativity >= base_dims.creativity

    def test_confidence_score_calculation(self, service, sample_brand_config, sample_prompt_analysis):
        """Test confidence score calculation"""
        confidence = service._calculate_confidence_score(sample_brand_config, sample_prompt_analysis)

        assert 0.0 <= confidence <= 1.0
        # Should be fairly high with our complete test data
        assert confidence > 0.6

    def test_fallback_vector_creation(self, service, sample_brand_config, sample_prompt_analysis):
        """Test fallback vector creation"""
        fallback = service._create_fallback_vector(sample_brand_config, sample_prompt_analysis)

        assert isinstance(fallback, BrandStyleVector)
        assert fallback.brand_name == "TestBrand"
        assert fallback.confidence_score == 0.3  # Low confidence for fallback
        assert fallback.generation_method == "fallback"

    def test_feature_vector_generation(self, service, sample_brand_config, sample_prompt_analysis):
        """Test feature vector generation for ML models"""
        import asyncio
        async def test():
            vector = await service.build_style_vector(sample_brand_config, sample_prompt_analysis)
            feature_vector = vector.to_feature_vector()

            assert isinstance(feature_vector, list)
            assert len(feature_vector) == 10  # 8 dimensions + confidence + overall score
            assert all(isinstance(x, float) for x in feature_vector)
            assert all(0.0 <= x <= 1.0 for x in feature_vector)

        asyncio.run(test())

    def test_overall_score_calculation(self, service, sample_brand_config, sample_prompt_analysis):
        """Test overall score calculation"""
        import asyncio
        async def test():
            vector = await service.build_style_vector(sample_brand_config, sample_prompt_analysis)
            overall_score = vector.overall_score

            assert 0.0 <= overall_score <= 1.0
            # Should be reasonably high for our test data
            assert overall_score > 0.5

        asyncio.run(test())

    def test_recommendations_generation(self, service, sample_brand_config, sample_prompt_analysis):
        """Test human-readable recommendations generation"""
        import asyncio
        async def test():
            vector = await service.build_style_vector(sample_brand_config, sample_prompt_analysis)
            recommendations = vector.get_recommendations()

            assert "overall_alignment" in recommendations
            assert "strengths" in recommendations
            assert "improvements" in recommendations
            assert "risks" in recommendations

            assert isinstance(recommendations["strengths"], list)
            assert isinstance(recommendations["improvements"], list)
            assert isinstance(recommendations["risks"], list)

        asyncio.run(test())

    def test_cache_key_generation(self, sample_brand_config):
        """Test cache key generation"""
        prompt_hash = "abc123def456"
        cache_key = create_style_vector_cache_key(sample_brand_config, prompt_hash)

        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
        # Should contain truncated hashes
        assert "_" in cache_key

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, service_with_redis, sample_brand_config, sample_prompt_analysis):
        """Test graceful handling of Redis errors"""
        # Mock Redis to raise an exception
        service_with_redis.redis_client.get.side_effect = Exception("Redis connection failed")

        # Should still work and return a valid vector
        result = await service_with_redis.build_style_vector(sample_brand_config, sample_prompt_analysis)

        assert isinstance(result, BrandStyleVector)
        # Should have called get once and failed gracefully
        service_with_redis.redis_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_error_fallback(self, service, sample_brand_config, sample_prompt_analysis):
        """Test that service always returns a vector even when computation fails"""
        # Mock a computation failure
        original_compute = service._compute_style_vector
        async def failing_compute(*args, **kwargs):
            raise Exception("Computation failed")

        service._compute_style_vector = failing_compute

        try:
            result = await service.build_style_vector(sample_brand_config, sample_prompt_analysis)

            # Should still return a valid vector (fallback)
            assert isinstance(result, BrandStyleVector)
            assert result.generation_method == "fallback"
            assert result.confidence_score == 0.3
        finally:
            # Restore original method
            service._compute_style_vector = original_compute
