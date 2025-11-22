"""
Brand Harmony Service - PR #502: Brand Harmony Module
Analyzes compatibility between brand color palettes and style vector requirements.
"""

import uuid
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..models.brand_style_vector import BrandStyleVector
from ..models.brand_config import ColorPalette
from ..models.brand_harmony import (
    BrandHarmonyAnalysis,
    ColorPaletteAnalysis,
    ColorHarmonyIssue,
    ColorCompatibility,
    HarmonyRecommendation,
    ConflictType,
    ConflictSeverity,
    calculate_contrast_ratio,
    get_color_temperature,
    is_wcag_aa_compliant,
    is_wcag_aaa_compliant,
    hex_to_rgb
)


class BrandHarmonyService:
    """
    Service for analyzing brand color harmony and detecting conflicts.

    This service evaluates how well a brand's color palette works with
    style vector requirements, detecting accessibility issues, contrast
    problems, and temperature conflicts while providing actionable recommendations.
    """

    def __init__(self, redis_client=None, use_mock: bool = False):
        """
        Initialize the brand harmony service.

        Args:
            redis_client: Optional Redis client for caching
            use_mock: Whether to use mock responses for testing
        """
        self.redis_client = redis_client
        self.use_mock = use_mock
        self.cache_ttl = 7200  # 2 hours cache TTL (harmony analysis is more stable than style vectors)

    async def analyze_harmony(
        self,
        style_vector: BrandStyleVector,
        color_palette: ColorPalette,
        cache_key: Optional[str] = None
    ) -> BrandHarmonyAnalysis:
        """
        Analyze harmony between brand style vector and color palette.

        Args:
            style_vector: Brand style vector from PR #501
            color_palette: Brand color palette from brand config
            cache_key: Optional cache key for storing/retrieving analysis

        Returns:
            BrandHarmonyAnalysis: Comprehensive harmony analysis
        """
        try:
            # Check cache first if available
            if cache_key and self.redis_client and not self.use_mock:
                cached_analysis = await self._get_cached_analysis(cache_key)
                if cached_analysis:
                    return cached_analysis

            # Perform comprehensive analysis
            analysis = await self._perform_harmony_analysis(style_vector, color_palette)

            # Cache the result
            if cache_key and self.redis_client and not self.use_mock:
                await self._cache_analysis(cache_key, analysis)

            return analysis

        except Exception as e:
            # Always return a valid analysis, never fail
            return self._create_fallback_analysis(style_vector, color_palette, str(e))

    async def _perform_harmony_analysis(
        self,
        style_vector: BrandStyleVector,
        color_palette: ColorPalette
    ) -> BrandHarmonyAnalysis:
        """
        Perform comprehensive harmony analysis.

        Args:
            style_vector: Brand style vector
            color_palette: Color palette to analyze

        Returns:
            BrandHarmonyAnalysis: Complete analysis results
        """
        # Analyze the color palette properties
        palette_analysis = self._analyze_color_palette(color_palette)

        # Detect specific conflicts
        conflicts = self._detect_conflicts(style_vector, palette_analysis)

        # Generate recommendations
        recommendations = self._generate_recommendations(conflicts, style_vector, palette_analysis)

        # Calculate component scores
        accessibility_score = self._calculate_accessibility_score(palette_analysis, conflicts)
        contrast_score = self._calculate_contrast_score(palette_analysis)
        temperature_score = self._calculate_temperature_harmony_score(palette_analysis)
        brand_recognition_score = self._calculate_brand_recognition_score(style_vector, palette_analysis)

        # Calculate overall weighted score
        overall_score = self._calculate_overall_harmony_score(
            accessibility_score, contrast_score, temperature_score, brand_recognition_score
        )

        # Create usage guidelines
        safe_combinations, risk_combinations = self._create_usage_guidelines(palette_analysis)

        return BrandHarmonyAnalysis(
            brand_name=style_vector.brand_name,
            analysis_id=str(uuid.uuid4()),
            style_vector_id=getattr(style_vector, 'id', 'unknown'),
            overall_harmony_score=overall_score,
            accessibility_score=accessibility_score,
            contrast_score=contrast_score,
            temperature_harmony_score=temperature_score,
            brand_recognition_score=brand_recognition_score,
            palette_analysis=palette_analysis,
            detected_conflicts=conflicts,
            recommendations=recommendations,
            safe_color_combinations=safe_combinations,
            risk_color_combinations=risk_combinations,
            created_at=datetime.utcnow().isoformat() + "Z",
            confidence_score=0.9  # High confidence for this analysis
        )

    def _analyze_color_palette(self, color_palette: ColorPalette) -> ColorPaletteAnalysis:
        """
        Perform detailed analysis of the color palette.

        Args:
            color_palette: Color palette to analyze

        Returns:
            ColorPaletteAnalysis: Comprehensive palette analysis
        """
        all_colors = color_palette.primary.copy()
        if color_palette.secondary:
            all_colors.extend(color_palette.secondary)
        if color_palette.background:
            all_colors.append(color_palette.background)

        # Analyze temperature properties
        temperatures = [get_color_temperature(color) for color in all_colors]
        avg_temperature = sum(temperatures) / len(temperatures) if temperatures else 0.5

        # Calculate temperature variance (how spread out temperatures are)
        if len(temperatures) > 1:
            variance = sum((t - avg_temperature) ** 2 for t in temperatures) / len(temperatures)
            temperature_variance = min(1.0, variance * 4)  # Scale and cap
        else:
            temperature_variance = 0.0

        # Calculate warm/cool balance (0.5 = perfect balance)
        warm_colors = sum(1 for t in temperatures if t > 0.5)
        cool_colors = sum(1 for t in temperatures if t <= 0.5)
        total_colors = len(temperatures)
        warm_cool_balance = 0.5 if total_colors == 0 else min(warm_colors, cool_colors * 2) / max(warm_colors, cool_colors * 2, 1)

        # Analyze accessibility and compatibility
        compatibility_matrix = []
        accessibility_issues = 0
        total_comparisons = 0

        # Check all pairwise combinations
        for i, color_a in enumerate(all_colors):
            for j, color_b in enumerate(all_colors):
                if i >= j:  # Avoid duplicate comparisons
                    continue

                total_comparisons += 1
                contrast_ratio = calculate_contrast_ratio(color_a, color_b)
                temp_diff = abs(get_color_temperature(color_a) - get_color_temperature(color_b))
                harmony_score = self._calculate_color_pair_harmony(color_a, color_b, contrast_ratio, temp_diff)

                compatibility_matrix.append(ColorCompatibility(
                    color_a=color_a,
                    color_b=color_b,
                    contrast_ratio=round(contrast_ratio, 2),
                    temperature_difference=round(temp_diff, 2),
                    harmony_score=round(harmony_score, 2),
                    recommended_usage=self._get_pair_usage_recommendations(color_a, color_b, contrast_ratio)
                ))

                # Count accessibility issues
                if not is_wcag_aa_compliant(contrast_ratio):
                    accessibility_issues += 1

        # Calculate accessibility score (percentage of compliant combinations)
        accessibility_score = 1.0 if total_comparisons == 0 else (total_comparisons - accessibility_issues) / total_comparisons

        # Determine WCAG compliance (need to check text/background specifically)
        wcag_aa_compliant = self._check_wcag_compliance(color_palette, compatibility_matrix, level="AA")
        wcag_aaa_compliant = self._check_wcag_compliance(color_palette, compatibility_matrix, level="AAA")

        return ColorPaletteAnalysis(
            palette_name=f"{color_palette.primary[0] if color_palette.primary else 'Unknown'}_palette",
            primary_colors=color_palette.primary,
            secondary_colors=color_palette.secondary,
            background_color=color_palette.background,
            warm_cool_balance=round(warm_cool_balance, 2),
            average_temperature=round(avg_temperature, 2),
            temperature_variance=round(temperature_variance, 2),
            accessibility_score=round(accessibility_score, 2),
            wcag_aa_compliant=wcag_aa_compliant,
            wcag_aaa_compliant=wcag_aaa_compliant,
            color_compatibility_matrix=compatibility_matrix
        )

    def _detect_conflicts(
        self,
        style_vector: BrandStyleVector,
        palette_analysis: ColorPaletteAnalysis
    ) -> List[ColorHarmonyIssue]:
        """
        Detect specific conflicts in the color palette.

        Args:
            style_vector: Brand style vector
            palette_analysis: Color palette analysis

        Returns:
            List[ColorHarmonyIssue]: All detected conflicts
        """
        conflicts = []

        # 1. Accessibility conflicts
        if not palette_analysis.wcag_aa_compliant:
            conflicts.append(ColorHarmonyIssue(
                conflict_type=ConflictType.ACCESSIBILITY,
                severity=ConflictSeverity.CRITICAL,
                description="Color palette does not meet WCAG AA accessibility standards for text contrast",
                affected_colors=self._get_accessibility_problematic_colors(palette_analysis),
                wcag_level="AA",
                measured_value=palette_analysis.accessibility_score,
                recommended_threshold=0.8
            ))

        # 2. Contrast ratio issues
        low_contrast_pairs = [
            compat for compat in palette_analysis.color_compatibility_matrix
            if compat.contrast_ratio < 3.0  # Below WCAG AAA for large text
        ]
        if low_contrast_pairs:
            conflicts.append(ColorHarmonyIssue(
                conflict_type=ConflictType.CONTRAST_RATIO,
                severity=ConflictSeverity.HIGH,
                description=f"Found {len(low_contrast_pairs)} color pairs with insufficient contrast ratios",
                affected_colors=list(set(
                    pair.color_a for pair in low_contrast_pairs
                ).union(
                    pair.color_b for pair in low_contrast_pairs
                )),
                measured_value=min(pair.contrast_ratio for pair in low_contrast_pairs),
                recommended_threshold=4.5
            ))

        # 3. Color temperature clashes
        if palette_analysis.temperature_variance > 0.7:  # High variance indicates clashes
            conflicts.append(ColorHarmonyIssue(
                conflict_type=ConflictType.TEMPERATURE_CLASH,
                severity=ConflictSeverity.MEDIUM,
                description="Wide range of color temperatures may create visual inconsistency",
                affected_colors=palette_analysis.primary_colors + (palette_analysis.secondary_colors or []),
                measured_value=palette_analysis.temperature_variance,
                recommended_threshold=0.5
            ))

        # 4. Brand recognition issues (based on style vector)
        if style_vector.dimensions.brand_recognition < 0.6:
            conflicts.append(ColorHarmonyIssue(
                conflict_type=ConflictType.BRAND_DILUTION,
                severity=ConflictSeverity.MEDIUM,
                description="Color palette may weaken brand recognition based on style requirements",
                affected_colors=palette_analysis.primary_colors,
                measured_value=style_vector.dimensions.brand_recognition,
                recommended_threshold=0.8
            ))

        # 5. Saturation mismatch
        saturation_issues = self._detect_saturation_issues(palette_analysis)
        if saturation_issues:
            conflicts.append(ColorHarmonyIssue(
                conflict_type=ConflictType.SATURATION_MISMATCH,
                severity=ConflictSeverity.LOW,
                description="Color saturation levels may not align with brand style requirements",
                affected_colors=saturation_issues,
                measured_value=style_vector.dimensions.visual_appeal,
                recommended_threshold=0.7
            ))

        return conflicts

    def _generate_recommendations(
        self,
        conflicts: List[ColorHarmonyIssue],
        style_vector: BrandStyleVector,
        palette_analysis: ColorPaletteAnalysis
    ) -> List[HarmonyRecommendation]:
        """
        Generate actionable recommendations based on detected conflicts.

        Args:
            conflicts: Detected conflicts
            style_vector: Brand style vector
            palette_analysis: Color palette analysis

        Returns:
            List[HarmonyRecommendation]: Actionable recommendations
        """
        recommendations = []

        # Handle accessibility issues
        accessibility_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.ACCESSIBILITY]
        if accessibility_conflicts:
            recommendations.append(HarmonyRecommendation(
                priority="critical",
                category="accessibility",
                action="Add high-contrast color combinations for text readability",
                rationale="WCAG AA compliance is essential for accessibility and legal compliance",
                affected_elements=["text", "buttons", "icons"],
                alternative_colors=self._suggest_accessible_alternatives(palette_analysis)
            ))

        # Handle contrast issues
        contrast_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.CONTRAST_RATIO]
        if contrast_conflicts:
            recommendations.append(HarmonyRecommendation(
                priority="high",
                category="contrast",
                action="Use recommended color pairs for text and background combinations",
                rationale="Better contrast improves readability and visual hierarchy",
                affected_elements=["text", "backgrounds", "call-to-action elements"]
            ))

        # Handle temperature issues
        temperature_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.TEMPERATURE_CLASH]
        if temperature_conflicts:
            recommendations.append(HarmonyRecommendation(
                priority="medium",
                category="aesthetics",
                action="Consider color temperature grouping for consistent visual themes",
                rationale="Harmonious color temperatures create more cohesive visual designs",
                affected_elements=["backgrounds", "accents", "section dividers"]
            ))

        # General brand strengthening recommendations
        if style_vector.dimensions.brand_recognition < 0.7:
            recommendations.append(HarmonyRecommendation(
                priority="medium",
                category="branding",
                action="Prioritize primary brand colors in key visual elements",
                rationale="Consistent use of primary colors strengthens brand recognition",
                affected_elements=["logos", "headers", "primary buttons"]
            ))

        # Always include positive reinforcement
        if not conflicts:  # No conflicts detected
            recommendations.append(HarmonyRecommendation(
                priority="low",
                category="maintenance",
                action="Continue using current color palette - excellent harmony detected",
                rationale="Current palette meets all harmony and accessibility requirements",
                affected_elements=["all visual elements"]
            ))

        return recommendations

    def _calculate_accessibility_score(
        self,
        palette_analysis: ColorPaletteAnalysis,
        conflicts: List[ColorHarmonyIssue]
    ) -> float:
        """Calculate accessibility score (0-1)"""
        base_score = palette_analysis.accessibility_score

        # Reduce score for critical accessibility conflicts
        critical_accessibility = sum(1 for c in conflicts
                                   if c.conflict_type == ConflictType.ACCESSIBILITY
                                   and c.severity == ConflictSeverity.CRITICAL)

        penalty = critical_accessibility * 0.3
        return max(0.0, base_score - penalty)

    def _calculate_contrast_score(self, palette_analysis: ColorPaletteAnalysis) -> float:
        """Calculate overall contrast quality score"""
        if not palette_analysis.color_compatibility_matrix:
            return 0.5

        contrast_ratios = [compat.contrast_ratio for compat in palette_analysis.color_compatibility_matrix]
        avg_contrast = sum(contrast_ratios) / len(contrast_ratios)

        # Score based on how many pairs meet different thresholds
        excellent_pairs = sum(1 for r in contrast_ratios if r >= 7.0)  # WCAG AAA
        good_pairs = sum(1 for r in contrast_ratios if 4.5 <= r < 7.0)  # WCAG AA
        poor_pairs = sum(1 for r in contrast_ratios if r < 4.5)

        total_pairs = len(contrast_ratios)
        score = (excellent_pairs * 1.0 + good_pairs * 0.7 + poor_pairs * 0.3) / total_pairs

        return min(1.0, score)

    def _calculate_temperature_harmony_score(self, palette_analysis: ColorPaletteAnalysis) -> float:
        """Calculate color temperature harmony score"""
        # Prefer balanced warm/cool ratios, penalize extreme imbalances
        balance_score = 1.0 - abs(palette_analysis.warm_cool_balance - 0.5) * 2

        # Prefer moderate variance (not too spread out, not too uniform)
        variance_score = 1.0 - abs(palette_analysis.temperature_variance - 0.3) * 2

        return (balance_score + variance_score) / 2

    def _calculate_brand_recognition_score(
        self,
        style_vector: BrandStyleVector,
        palette_analysis: ColorPaletteAnalysis
    ) -> float:
        """Calculate how well colors support brand recognition"""
        # Based on style vector's brand recognition dimension
        base_score = style_vector.dimensions.brand_recognition

        # Boost if palette has good accessibility (accessible brands are more recognizable)
        if palette_analysis.wcag_aa_compliant:
            base_score = min(1.0, base_score + 0.1)

        # Boost if primary colors are well-defined
        if len(palette_analysis.primary_colors) >= 2:
            base_score = min(1.0, base_score + 0.05)

        return base_score

    def _calculate_overall_harmony_score(
        self,
        accessibility: float,
        contrast: float,
        temperature: float,
        brand_recognition: float
    ) -> float:
        """Calculate weighted overall harmony score"""
        # Weights: accessibility is most important, then contrast, then others
        weights = {
            'accessibility': 0.4,    # Most critical
            'contrast': 0.3,         # Very important for usability
            'temperature': 0.15,     # Important for aesthetics
            'brand_recognition': 0.15 # Important for consistency
        }

        weighted_score = (
            accessibility * weights['accessibility'] +
            contrast * weights['contrast'] +
            temperature * weights['temperature'] +
            brand_recognition * weights['brand_recognition']
        )

        return round(weighted_score, 3)

    def _calculate_color_pair_harmony(
        self,
        color_a: str,
        color_b: str,
        contrast_ratio: float,
        temp_diff: float
    ) -> float:
        """Calculate harmony score for a specific color pair"""
        # Start with contrast score (accessibility-focused)
        if contrast_ratio >= 7.0:  # WCAG AAA
            contrast_score = 1.0
        elif contrast_ratio >= 4.5:  # WCAG AA
            contrast_score = 0.8
        elif contrast_ratio >= 3.0:  # Large text minimum
            contrast_score = 0.6
        else:
            contrast_score = contrast_ratio / 3.0  # Linear scale below minimum

        # Temperature harmony (prefer complementary or similar temperatures)
        temp_harmony = 1.0 - min(temp_diff, 0.5) * 2  # Max penalty for 0.5 difference

        # Weighted combination
        return (contrast_score * 0.7) + (temp_harmony * 0.3)

    def _get_pair_usage_recommendations(
        self,
        color_a: str,
        color_b: str,
        contrast_ratio: float
    ) -> List[str]:
        """Get recommended usage patterns for a color pair"""
        recommendations = []

        if contrast_ratio >= 7.0:
            recommendations.extend(["text on background", "icons", "borders"])
        elif contrast_ratio >= 4.5:
            recommendations.extend(["large text", "buttons", "interactive elements"])
        elif contrast_ratio >= 3.0:
            recommendations.extend(["large text only", "decorative elements"])
        else:
            recommendations.append("decorative use only - not for text")

        return recommendations

    def _check_wcag_compliance(
        self,
        color_palette: ColorPalette,
        compatibility_matrix: List[ColorCompatibility],
        level: str = "AA"
    ) -> bool:
        """Check if palette meets WCAG compliance standards"""
        # For WCAG compliance, we need to check text/background combinations
        # This is a simplified check - in practice would need more sophisticated analysis

        if not color_palette.background:
            return False  # Can't check without background

        background = color_palette.background
        text_colors = color_palette.primary + (color_palette.secondary or [])

        for text_color in text_colors:
            contrast = calculate_contrast_ratio(text_color, background)
            if level == "AAA":
                if not is_wcag_aaa_compliant(contrast):
                    return False
            else:  # AA
                if not is_wcag_aa_compliant(contrast):
                    return False

        return True

    def _get_accessibility_problematic_colors(
        self,
        palette_analysis: ColorPaletteAnalysis
    ) -> List[str]:
        """Get colors that have accessibility issues"""
        problematic = set()

        for compat in palette_analysis.color_compatibility_matrix:
            if not is_wcag_aa_compliant(compat.contrast_ratio):
                problematic.add(compat.color_a)
                problematic.add(compat.color_b)

        return list(problematic)

    def _detect_saturation_issues(self, palette_analysis: ColorPaletteAnalysis) -> List[str]:
        """Detect colors with saturation issues"""
        # This is a simplified check - would need more sophisticated color analysis
        # For now, just return empty list (saturation analysis would be complex)
        return []

    def _suggest_accessible_alternatives(
        self,
        palette_analysis: ColorPaletteAnalysis
    ) -> List[str]:
        """Suggest more accessible color alternatives"""
        # This would typically involve color theory to suggest better alternatives
        # For now, return some generic high-contrast suggestions
        return ["#000000", "#FFFFFF", "#0066CC", "#004499"]

    def _create_usage_guidelines(
        self,
        palette_analysis: ColorPaletteAnalysis
    ) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """Create safe and risky color combination guidelines"""
        safe_combinations = {}
        risk_combinations = {}

        # Categorize combinations by usage
        for compat in palette_analysis.color_compatibility_matrix:
            pair_key = f"{compat.color_a}_{compat.color_b}"

            if compat.contrast_ratio >= 4.5:  # WCAG AA
                safe_combinations["text_on_background"] = safe_combinations.get("text_on_background", [])
                safe_combinations["text_on_background"].append(pair_key)
            elif compat.contrast_ratio < 3.0:  # Poor contrast
                risk_combinations["text_combinations"] = risk_combinations.get("text_combinations", [])
                risk_combinations["text_combinations"].append(pair_key)

        return safe_combinations, risk_combinations

    def _create_fallback_analysis(
        self,
        style_vector: BrandStyleVector,
        color_palette: ColorPalette,
        error_msg: str
    ) -> BrandHarmonyAnalysis:
        """Create a fallback analysis when computation fails"""
        return BrandHarmonyAnalysis(
            brand_name=style_vector.brand_name,
            analysis_id=str(uuid.uuid4()),
            style_vector_id="fallback",
            overall_harmony_score=0.5,  # Neutral score
            accessibility_score=0.5,
            contrast_score=0.5,
            temperature_harmony_score=0.5,
            brand_recognition_score=0.5,
            palette_analysis=ColorPaletteAnalysis(
                palette_name="fallback_palette",
                primary_colors=color_palette.primary,
                secondary_colors=color_palette.secondary,
                background_color=color_palette.background,
                warm_cool_balance=0.5,
                average_temperature=0.5,
                temperature_variance=0.5,
                accessibility_score=0.5,
                wcag_aa_compliant=True,  # Assume compliant for fallback
                wcag_aaa_compliant=False,
                color_compatibility_matrix=[]
            ),
            detected_conflicts=[],
            recommendations=[HarmonyRecommendation(
                priority="low",
                category="system",
                action="Analysis temporarily unavailable - using conservative defaults",
                rationale=f"Analysis failed: {error_msg}",
                affected_elements=["all"]
            )],
            safe_color_combinations={},
            risk_color_combinations={},
            created_at=datetime.utcnow().isoformat() + "Z",
            confidence_score=0.3  # Low confidence for fallback
        )

    async def _get_cached_analysis(self, cache_key: str) -> Optional[BrandHarmonyAnalysis]:
        """Retrieve harmony analysis from Redis cache"""
        try:
            if not self.redis_client:
                return None

            cached_data = await self.redis_client.get(f"harmony_analysis:{cache_key}")
            if cached_data:
                data = cached_data.decode('utf-8') if isinstance(cached_data, bytes) else cached_data
                import json
                analysis_data = json.loads(data)
                return BrandHarmonyAnalysis(**analysis_data)
        except Exception as e:
            print(f"Failed to retrieve cached harmony analysis: {str(e)}")

        return None

    async def _cache_analysis(self, cache_key: str, analysis: BrandHarmonyAnalysis) -> None:
        """Cache harmony analysis in Redis"""
        try:
            if not self.redis_client:
                return

            import json
            cache_data = json.dumps(analysis.dict())
            await self.redis_client.setex(
                f"harmony_analysis:{cache_key}",
                self.cache_ttl,
                cache_data
            )
        except Exception as e:
            print(f"Failed to cache harmony analysis: {str(e)}")


def create_harmony_cache_key(brand_name: str, color_palette: ColorPalette, style_vector_hash: str) -> str:
    """
    Create a cache key for harmony analysis.

    Args:
        brand_name: Brand name
        color_palette: Color palette
        style_vector_hash: Hash of the style vector

    Returns:
        Cache key string
    """
    # Create hash of color palette
    colors_str = "_".join(sorted(color_palette.primary + (color_palette.secondary or [])))
    colors_hash = hashlib.md5(colors_str.encode()).hexdigest()[:8]

    return f"{brand_name}_{colors_hash}_{style_vector_hash[:8]}"
