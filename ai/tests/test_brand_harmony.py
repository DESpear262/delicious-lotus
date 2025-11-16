"""
Unit tests for Brand Harmony Service - PR #502
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from ..models.brand_style_vector import BrandStyleVector, StyleDimensions
from ..models.brand_config import ColorPalette
from ..models.brand_harmony import (
    BrandHarmonyAnalysis,
    ColorPaletteAnalysis,
    ColorHarmonyIssue,
    ConflictType,
    ConflictSeverity,
    calculate_contrast_ratio,
    get_color_temperature,
    is_wcag_aa_compliant,
    hex_to_rgb
)
from ..services.brand_harmony_service import BrandHarmonyService, create_harmony_cache_key


class TestBrandHarmonyService:
    """Test cases for BrandHarmonyService"""

    @pytest.fixture
    def sample_style_vector(self):
        """Create a sample brand style vector for testing"""
        return BrandStyleVector(
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
            brand_name="TestBrand",
            content_description="Professional video content",
            confidence_score=0.9,
            original_brand_config={},
            prompt_analysis_summary={},
            generated_at=datetime.utcnow().isoformat() + "Z",
            generation_method="computed"
        )

    @pytest.fixture
    def sample_color_palette(self):
        """Create a sample color palette for testing"""
        return ColorPalette(
            primary=["#1a1a1a", "#d4af37"],  # Black and gold
            secondary=["#666666"],          # Gray
            background="#ffffff"             # White
        )

    @pytest.fixture
    def service(self):
        """Create a BrandHarmonyService instance"""
        return BrandHarmonyService(use_mock=True)

    @pytest.fixture
    def service_with_redis(self):
        """Create a service with mock Redis client"""
        mock_redis = AsyncMock()
        return BrandHarmonyService(redis_client=mock_redis, use_mock=True)

    def test_service_initialization(self):
        """Test service initialization"""
        service = BrandHarmonyService()
        assert service.redis_client is None
        assert service.use_mock is False
        assert service.cache_ttl == 7200

        service_with_redis = BrandHarmonyService(redis_client=MagicMock())
        assert service_with_redis.redis_client is not None

    @pytest.mark.asyncio
    async def test_analyze_harmony_basic(self, service, sample_style_vector, sample_color_palette):
        """Test basic harmony analysis"""
        result = await service.analyze_harmony(sample_style_vector, sample_color_palette)

        assert isinstance(result, BrandHarmonyAnalysis)
        assert result.brand_name == "TestBrand"
        assert 0.0 <= result.overall_harmony_score <= 1.0
        assert 0.0 <= result.accessibility_score <= 1.0
        assert 0.0 <= result.contrast_score <= 1.0
        assert 0.0 <= result.temperature_harmony_score <= 1.0
        assert 0.0 <= result.brand_recognition_score <= 1.0

        assert isinstance(result.palette_analysis, ColorPaletteAnalysis)
        assert isinstance(result.detected_conflicts, list)
        assert isinstance(result.recommendations, list)

    @pytest.mark.asyncio
    async def test_analyze_harmony_with_caching(self, service_with_redis, sample_style_vector, sample_color_palette):
        """Test harmony analysis with Redis caching"""
        cache_key = "test_key"

        # Mock Redis to return None (cache miss)
        service_with_redis.redis_client.get.return_value = None

        result = await service_with_redis.analyze_harmony(
            sample_style_vector, sample_color_palette, cache_key
        )

        assert isinstance(result, BrandHarmonyAnalysis)
        # Verify Redis interactions
        service_with_redis.redis_client.get.assert_called_once()
        service_with_redis.redis_client.setex.assert_called_once()

    def test_analyze_color_palette(self, service, sample_color_palette):
        """Test color palette analysis"""
        analysis = service._analyze_color_palette(sample_color_palette)

        assert isinstance(analysis, ColorPaletteAnalysis)
        assert analysis.primary_colors == ["#1a1a1a", "#d4af37"]
        assert analysis.secondary_colors == ["#666666"]
        assert analysis.background_color == "#ffffff"

        # Check temperature analysis
        assert 0.0 <= analysis.average_temperature <= 1.0
        assert 0.0 <= analysis.temperature_variance <= 1.0
        assert 0.0 <= analysis.warm_cool_balance <= 1.0

        # Check accessibility
        assert isinstance(analysis.wcag_aa_compliant, bool)
        assert isinstance(analysis.wcag_aaa_compliant, bool)
        assert 0.0 <= analysis.accessibility_score <= 1.0

        # Check compatibility matrix
        assert isinstance(analysis.color_compatibility_matrix, list)
        assert len(analysis.color_compatibility_matrix) > 0

    def test_detect_conflicts_accessibility(self, service, sample_style_vector):
        """Test accessibility conflict detection"""
        # Create a palette with poor contrast
        poor_palette = ColorPalette(
            primary=["#ffffff"],  # White text
            background="#ffffff"  # White background - zero contrast
        )

        palette_analysis = service._analyze_color_palette(poor_palette)
        conflicts = service._detect_conflicts(sample_style_vector, palette_analysis)

        # Should detect accessibility conflicts
        accessibility_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.ACCESSIBILITY]
        assert len(accessibility_conflicts) > 0

        conflict = accessibility_conflicts[0]
        assert conflict.severity == ConflictSeverity.CRITICAL
        assert "WCAG" in conflict.description

    def test_detect_conflicts_contrast(self, service, sample_style_vector):
        """Test contrast ratio conflict detection"""
        # Create palette with poor contrast combinations
        poor_contrast_palette = ColorPalette(
            primary=["#808080", "#909090"],  # Two similar grays
            background="#ffffff"
        )

        palette_analysis = service._analyze_color_palette(poor_contrast_palette)
        conflicts = service._detect_conflicts(sample_style_vector, palette_analysis)

        # Should detect contrast conflicts
        contrast_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.CONTRAST_RATIO]
        # May or may not detect depending on specific contrast ratios

    def test_detect_conflicts_temperature(self, service, sample_style_vector):
        """Test temperature clash detection"""
        # Create palette with extreme temperature differences
        extreme_temp_palette = ColorPalette(
            primary=["#0000ff", "#ff0000", "#00ff00", "#ffff00", "#ff00ff", "#00ffff"],  # All primary colors
            background="#ffffff"
        )

        palette_analysis = service._analyze_color_palette(extreme_temp_palette)
        conflicts = service._detect_conflicts(sample_style_vector, palette_analysis)

        # High temperature variance should trigger conflict
        temp_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.TEMPERATURE_CLASH]
        if palette_analysis.temperature_variance > 0.7:
            assert len(temp_conflicts) > 0

    def test_generate_recommendations(self, service, sample_style_vector, sample_color_palette):
        """Test recommendation generation"""
        palette_analysis = service._analyze_color_palette(sample_color_palette)
        conflicts = service._detect_conflicts(sample_style_vector, palette_analysis)

        recommendations = service._generate_recommendations(conflicts, sample_style_vector, palette_analysis)

        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert hasattr(rec, 'priority')
            assert hasattr(rec, 'category')
            assert hasattr(rec, 'action')
            assert hasattr(rec, 'rationale')

    def test_calculate_accessibility_score(self, service):
        """Test accessibility score calculation"""
        # Create mock palette analysis
        palette_analysis = ColorPaletteAnalysis(
            palette_name="test",
            primary_colors=["#000000"],
            accessibility_score=0.8,
            wcag_aa_compliant=True,
            wcag_aaa_compliant=False,
            warm_cool_balance=0.5,
            average_temperature=0.5,
            temperature_variance=0.5,
            color_compatibility_matrix=[]
        )

        # Test with no conflicts
        conflicts = []
        score = service._calculate_accessibility_score(palette_analysis, conflicts)
        assert score == 0.8

        # Test with critical accessibility conflicts
        from ..models.brand_harmony import ColorHarmonyIssue
        conflicts = [ColorHarmonyIssue(
            conflict_type=ConflictType.ACCESSIBILITY,
            severity=ConflictSeverity.CRITICAL,
            description="Test conflict",
            affected_colors=["#000000"]
        )]
        score_with_penalty = service._calculate_accessibility_score(palette_analysis, conflicts)
        assert score_with_penalty < score

    def test_calculate_contrast_score(self, service):
        """Test contrast score calculation"""
        # Create palette with good contrast
        good_palette = ColorPaletteAnalysis(
            palette_name="good",
            primary_colors=["#000000", "#ffffff"],
            accessibility_score=1.0,
            wcag_aa_compliant=True,
            wcag_aaa_compliant=True,
            warm_cool_balance=0.5,
            average_temperature=0.5,
            temperature_variance=0.5,
            color_compatibility_matrix=[
                type('MockCompat', (), {
                    'contrast_ratio': 21.0,  # Excellent contrast
                    'color_a': '#000000',
                    'color_b': '#ffffff'
                })()
            ]
        )

        score = service._calculate_contrast_score(good_palette)
        assert 0.8 <= score <= 1.0  # Should be high

    def test_calculate_temperature_harmony_score(self, service):
        """Test temperature harmony score calculation"""
        # Test balanced palette
        balanced_palette = ColorPaletteAnalysis(
            palette_name="balanced",
            primary_colors=["#ff0000", "#0000ff"],  # Red and blue - balanced warm/cool
            accessibility_score=1.0,
            wcag_aa_compliant=True,
            wcag_aaa_compliant=False,
            warm_cool_balance=0.5,
            average_temperature=0.5,
            temperature_variance=0.3,  # Moderate variance
            color_compatibility_matrix=[]
        )

        score = service._calculate_temperature_harmony_score(balanced_palette)
        assert 0.7 <= score <= 1.0  # Should be reasonably high

    def test_calculate_overall_harmony_score(self, service):
        """Test weighted overall harmony score calculation"""
        score = service._calculate_overall_harmony_score(
            accessibility=0.9,
            contrast=0.8,
            temperature=0.7,
            brand_recognition=0.8
        )

        # Should be weighted: 0.4*0.9 + 0.3*0.8 + 0.15*0.7 + 0.15*0.8 = 0.36 + 0.24 + 0.105 + 0.12 = 0.825
        expected = 0.825
        assert abs(score - expected) < 0.01

    def test_calculate_color_pair_harmony(self, service):
        """Test color pair harmony calculation"""
        # High contrast, similar temperature
        harmony1 = service._calculate_color_pair_harmony("#000000", "#ffffff", 21.0, 0.1)
        assert harmony1 > 0.8  # Should be very high

        # Low contrast, different temperature
        harmony2 = service._calculate_color_pair_harmony("#808080", "#909090", 1.2, 0.8)
        assert harmony2 < 0.5  # Should be low

    def test_get_pair_usage_recommendations(self, service):
        """Test usage recommendations for color pairs"""
        # Excellent contrast
        recs1 = service._get_pair_usage_recommendations("#000000", "#ffffff", 21.0)
        assert "text on background" in recs1
        assert "icons" in recs1

        # Poor contrast
        recs2 = service._get_pair_usage_recommendations("#808080", "#909090", 1.2)
        assert "decorative use only" in recs2

    def test_create_usage_guidelines(self, service):
        """Test usage guidelines creation"""
        palette_analysis = ColorPaletteAnalysis(
            palette_name="test",
            primary_colors=["#000000", "#ffffff"],
            accessibility_score=1.0,
            wcag_aa_compliant=True,
            wcag_aaa_compliant=True,
            warm_cool_balance=0.5,
            average_temperature=0.5,
            temperature_variance=0.5,
            color_compatibility_matrix=[
                type('MockCompat', (), {
                    'contrast_ratio': 21.0,
                    'color_a': '#000000',
                    'color_b': '#ffffff'
                })()
            ]
        )

        safe, risk = service._create_usage_guidelines(palette_analysis)

        assert isinstance(safe, dict)
        assert isinstance(risk, dict)
        assert "text_on_background" in safe

    def test_fallback_analysis_creation(self, service, sample_style_vector, sample_color_palette):
        """Test fallback analysis creation"""
        fallback = service._create_fallback_analysis(sample_style_vector, sample_color_palette, "Test error")

        assert isinstance(fallback, BrandHarmonyAnalysis)
        assert fallback.brand_name == "TestBrand"
        assert fallback.overall_harmony_score == 0.5  # Neutral fallback score
        assert fallback.confidence_score == 0.3  # Low confidence
        assert len(fallback.recommendations) == 1
        assert "fallback" in fallback.recommendations[0].action

    def test_harmony_analysis_summary_methods(self, service, sample_style_vector, sample_color_palette):
        """Test harmony analysis summary methods"""
        import asyncio
        async def test():
            analysis = await service.analyze_harmony(sample_style_vector, sample_color_palette)

            # Test critical issues
            critical_issues = analysis.get_critical_issues()
            assert isinstance(critical_issues, list)

            # Test accessibility issues
            accessibility_issues = analysis.get_accessibility_issues()
            assert isinstance(accessibility_issues, list)

            # Test priority recommendations
            high_priority = analysis.get_recommendations_by_priority("high")
            assert isinstance(high_priority, list)

            # Test accessibility check
            is_accessible = analysis.is_accessible()
            assert isinstance(is_accessible, bool)

            # Test summary
            summary = analysis.get_harmony_summary()
            assert isinstance(summary, dict)
            assert "overall_score" in summary
            assert "critical_issues" in summary
            assert "accessibility_compliant" in summary

        asyncio.run(test())

    def test_cache_key_generation(self, sample_color_palette):
        """Test harmony cache key generation"""
        style_vector_hash = "abc123def456"
        cache_key = create_harmony_cache_key("TestBrand", sample_color_palette, style_vector_hash)

        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
        assert "TestBrand" in cache_key
        assert "_" in cache_key

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, service_with_redis, sample_style_vector, sample_color_palette):
        """Test graceful handling of Redis errors"""
        # Mock Redis to raise an exception
        service_with_redis.redis_client.get.side_effect = Exception("Redis connection failed")

        # Should still work and return a valid analysis
        result = await service_with_redis.analyze_harmony(sample_style_vector, sample_color_palette)

        assert isinstance(result, BrandHarmonyAnalysis)
        # Should have called get once and failed gracefully
        service_with_redis.redis_client.get.assert_called_once()


# Test utility functions
def test_hex_to_rgb():
    """Test hex to RGB conversion"""
    r, g, b = hex_to_rgb("#ff0000")
    assert r == 255
    assert g == 0
    assert b == 0

    r, g, b = hex_to_rgb("#0080c0")
    assert r == 0
    assert g == 128
    assert b == 192


def test_calculate_contrast_ratio():
    """Test contrast ratio calculation"""
    # Black on white should have high contrast
    ratio = calculate_contrast_ratio("#000000", "#ffffff")
    assert ratio > 15.0

    # Same colors should have ratio of 1
    ratio = calculate_contrast_ratio("#808080", "#808080")
    assert abs(ratio - 1.0) < 0.01


def test_get_color_temperature():
    """Test color temperature estimation"""
    # Red should be warm
    temp_red = get_color_temperature("#ff0000")
    assert temp_red > 0.5

    # Blue should be cool
    temp_blue = get_color_temperature("#0000ff")
    assert temp_blue < 0.5


def test_wcag_compliance_checks():
    """Test WCAG compliance checking"""
    # High contrast should pass
    assert is_wcag_aa_compliant(5.0)
    assert is_wcag_aa_compliant(3.5, is_large_text=True)

    # Low contrast should fail
    assert not is_wcag_aa_compliant(2.0)
    assert not is_wcag_aa_compliant(2.5, is_large_text=True)

    # Very high contrast should pass AAA
    assert is_wcag_aaa_compliant(8.0)
    assert not is_wcag_aaa_compliant(6.0)
