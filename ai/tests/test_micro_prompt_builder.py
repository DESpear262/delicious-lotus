"""
Tests for Micro-Prompt Builder Service - PR 301
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from ..models.micro_prompt import (
    MicroPrompt,
    MicroPromptRequest,
    MicroPromptResponse,
    PromptBuilderConfig,
    PromptPriority,
    PromptElement
)
from ..models.scene_decomposition import Scene, SceneType, VisualStyle
from ..models.brand_style_vector import BrandStyleVector, StyleDimensions
from ..services.micro_prompt_builder_service import MicroPromptBuilderService


class TestMicroPromptBuilderService:
    """Test cases for the MicroPromptBuilderService"""

    @pytest.fixture
    def mock_brand_style_vector(self):
        """Create a mock brand style vector"""
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
            brand_name="Test Brand",
            content_description="Test video content",
            confidence_score=0.8,
            original_brand_config={"name": "Test Brand", "colors": ["#FF0000", "#0000FF"]},
            prompt_analysis_summary={"tone": "professional", "style": "modern"},
            generated_at=datetime.utcnow().isoformat() + "Z",
            generation_method="test",
            version="1.0"
        )

    @pytest.fixture
    def mock_scene(self):
        """Create a mock scene"""
        return Scene(
            scene_id="scene_1",
            scene_type=SceneType.DEVELOPMENT,
            start_time=5.0,
            duration=10.0,
            end_time=15.0,
            title="Product Demonstration",
            content_description="Show the product in action with key features",
            narrative_purpose="Demonstrate the product and key benefits",
            visual_style=VisualStyle.PRODUCT_SHOT,
            key_elements=[],
            brand_references=None,
            pacing="medium"
        )

    @pytest.fixture
    def service(self):
        """Create a service instance with test config"""
        config = PromptBuilderConfig(
            target_model="google/veo-3.1-fast",
            max_prompt_length=300,
            include_negative_prompts=True
        )
        return MicroPromptBuilderService(config)

    def test_service_initialization(self):
        """Test that service initializes with correct defaults"""
        service = MicroPromptBuilderService()

        assert service.config.target_model == "google/veo-3.1-fast"
        assert service.config.max_prompt_length == 500
        assert service.config.include_negative_prompts is True

        # Check that templates are initialized
        assert "introduction" in service.config.base_templates
        assert "development" in service.config.base_templates

    @pytest.mark.asyncio
    async def test_build_micro_prompts_basic(self, service, mock_scene, mock_brand_style_vector):
        """Test basic micro-prompt building"""
        request = MicroPromptRequest(
            generation_id="test_gen_123",
            scenes=[mock_scene.dict()],
            prompt_analysis={
                "tone": "professional",
                "style": "modern",
                "key_themes": ["innovation", "quality"],
                "primary_product": "Test Product"
            },
            brand_config={
                "name": "Test Brand",
                "colors": ["#FF0000", "#0000FF"],
                "typography": {"primary_font": "Arial"}
            },
            brand_style_vector=mock_brand_style_vector.dict()
        )

        response = await service.build_micro_prompts(request)

        assert isinstance(response, MicroPromptResponse)
        assert response.generation_id == "test_gen_123"
        assert len(response.micro_prompts) == 1
        assert response.total_scenes == 1
        assert response.average_confidence > 0

        # Check the generated prompt
        prompt = response.micro_prompts[0]
        assert isinstance(prompt, MicroPrompt)
        assert prompt.scene_id == "scene_1"
        assert prompt.prompt_text
        assert len(prompt.prompt_text) > 0
        assert prompt.confidence_score > 0
        assert prompt.style_vector_score == mock_brand_style_vector.overall_score

    def test_prompt_element_creation(self, service):
        """Test that prompt elements are created correctly"""
        # This tests the internal _build_core_description method indirectly
        # by checking that elements are properly categorized

        # Create a mock scene with brand references
        scene = Scene(
            scene_id="scene_1",
            scene_type=SceneType.INTRODUCTION,
            start_time=0.0,
            duration=5.0,
            end_time=5.0,
            title="Brand Intro",
            content_description="Introduce the brand",
            narrative_purpose="Hook the viewer",
            visual_style=VisualStyle.BRAND_SHOWCASE,
            key_elements=[],
            brand_references=None,
            pacing="medium"
        )

        # Test core description building
        prompt_analysis = {"tone": "professional", "style": "modern"}
        core_desc = service._build_core_description(scene, prompt_analysis)

        assert "Introduce the brand" in core_desc
        assert "professional modern style" in core_desc

    def test_brand_integration(self, service, mock_brand_style_vector):
        """Test brand element integration in prompts"""
        brand_config = {
            "name": "Test Brand",
            "colors": ["#FF0000", "#0000FF", "#00FF00"],
            "typography": {"primary_font": "Helvetica"}
        }

        scene = Scene(
            scene_id="scene_1",
            scene_type=SceneType.DEVELOPMENT,
            start_time=0.0,
            duration=10.0,
            end_time=10.0,
            title="Demo",
            content_description="Demo content",
            narrative_purpose="Demonstrate product",
            visual_style=VisualStyle.PRODUCT_SHOT,
            key_elements=[],
            brand_references=None,
            pacing="medium"
        )

        brand_elements = service._build_brand_elements(scene, brand_config, mock_brand_style_vector)

        assert brand_elements
        assert "Test Brand" in brand_elements or "color scheme" in brand_elements

    def test_negative_prompt_generation(self, service):
        """Test negative prompt generation"""
        scene = Scene(
            scene_id="scene_1",
            scene_type=SceneType.DEVELOPMENT,
            start_time=0.0,
            duration=10.0,
            end_time=10.0,
            title="Demo",
            content_description="Demo content",
            narrative_purpose="Demonstrate product",
            visual_style=VisualStyle.PRODUCT_SHOT,
            key_elements=[],
            brand_references=None,
            pacing="medium"
        )

        prompt_analysis = {"tone": "professional"}

        negative_prompt = service._build_negative_prompt(scene, prompt_analysis)

        # Should contain quality-related negative terms
        assert "blurry" in negative_prompt
        assert "low quality" in negative_prompt
        assert "generic branding" in negative_prompt

    def test_prompt_validation(self, service):
        """Test prompt validation functionality"""
        # Create a valid prompt
        valid_prompt = MicroPrompt(
            scene_id="scene_1",
            prompt_id="mp_123",
            prompt_text="Professional video demonstration of the product in modern style with high quality production",
            negative_prompt="blurry, low quality, amateur",
            estimated_duration=10.0,
            aspect_ratio="16:9",
            resolution="1024x576",
            style_vector_score=0.8,
            brand_elements=["Test Brand"],
            confidence_score=0.9,
            generation_hints={},
            source_elements=[],
            original_scene_data={}
        )

        validation = valid_prompt.validate_prompt_quality()

        assert validation["is_valid"] is True
        assert len(validation["issues"]) == 0
        assert validation["overall_quality"] == "good"

    def test_prompt_validation_short_prompt(self, service):
        """Test validation of too-short prompts"""
        short_prompt = MicroPrompt(
            scene_id="scene_1",
            prompt_id="mp_123",
            prompt_text="Short",  # Too short
            negative_prompt=None,
            estimated_duration=10.0,
            aspect_ratio="16:9",
            resolution="1024x576",
            style_vector_score=0.8,
            brand_elements=[],
            confidence_score=0.5,
            generation_hints={},
            source_elements=[],
            original_scene_data={}
        )

        validation = short_prompt.validate_prompt_quality()

        assert validation["is_valid"] is False
        assert "too short" in " ".join(validation["issues"]).lower()

    def test_confidence_score_calculation(self, service, mock_brand_style_vector):
        """Test confidence score calculation"""
        # Create elements with different priorities
        elements = [
            PromptElement(content="Core description", priority=PromptPriority.CRITICAL, category="narrative", source="scene"),
            PromptElement(content="Brand elements", priority=PromptPriority.HIGH, category="brand", source="brand_config"),
            PromptElement(content="Visual hints", priority=PromptPriority.MEDIUM, category="visual", source="scene")
        ]

        confidence = service._calculate_confidence_score(elements, mock_brand_style_vector)

        assert 0 < confidence <= 1.0
        # Should be boosted by critical elements, brand elements, and style vector
        assert confidence > 0.7  # Expect relatively high confidence

    def test_batch_validation(self, service):
        """Test batch prompt validation"""
        prompts = [
            MicroPrompt(
                scene_id=f"scene_{i}",
                prompt_id=f"mp_{i}",
                prompt_text=f"Valid prompt {i} with sufficient length for testing purposes",
                negative_prompt="blurry, low quality",
                estimated_duration=10.0,
                aspect_ratio="16:9",
                resolution="1024x576",
                style_vector_score=0.8,
                brand_elements=["Brand"],
                confidence_score=0.9,
                generation_hints={},
                source_elements=[],
                original_scene_data={}
            )
            for i in range(3)
        ]

        validation = service._validate_prompt_batch(prompts)

        assert validation["total_prompts"] == 3
        assert validation["valid_prompts"] == 3
        assert validation["validation_rate"] == 1.0

    def test_empty_batch_validation(self, service):
        """Test validation with empty prompt batch"""
        validation = service._validate_prompt_batch([])

        assert validation["total_prompts"] == 0
        assert validation["valid_prompts"] == 0

    def test_model_hints_generation(self, service):
        """Test model-specific hints generation"""
        hints = service._get_model_hints()

        # Should contain hints for the configured model
        assert isinstance(hints, dict)

    def test_brand_keywords_extraction(self, service):
        """Test extraction of brand keywords for tracking"""
        brand_config = {
            "name": "Test Brand",
            "tagline": "Quality Products",
            "colors": ["#FF0000", "#0000FF", "#00FF00"]
        }

        keywords = service._extract_brand_keywords(brand_config)

        assert "Test Brand" in keywords
        assert "Quality Products" in keywords
        assert len(keywords) <= 5  # Should be limited

    @pytest.mark.asyncio
    async def test_error_handling_no_scenes(self, service):
        """Test error handling with empty scenes"""
        request = MicroPromptRequest(
            generation_id="test_gen_123",
            scenes=[],  # Empty scenes
            prompt_analysis={},
            brand_config=None,
            brand_style_vector=None
        )

        response = await service.build_micro_prompts(request)

        assert response.total_scenes == 0
        assert len(response.micro_prompts) == 0
        assert response.average_confidence == 0.0


class TestMicroPromptIntegration:
    """Integration tests for the complete scenes → prompts pipeline"""

    @pytest.mark.asyncio
    async def test_full_pipeline_ad_video(self):
        """Test complete pipeline from scene decomposition to micro-prompts"""
        from ..models.scene_decomposition import decompose_video_scenes, SceneDecompositionRequest

        # Step 1: Create scene decomposition request
        scene_request = SceneDecompositionRequest(
            video_type="ad",
            total_duration=30,  # 30 second ad
            prompt_analysis={
                "tone": "enthusiastic",
                "style": "modern",
                "key_themes": ["innovation", "speed", "quality"],
                "primary_product": "Super Widget",
                "key_features": ["fast", "reliable", "durable"],
                "product_focus": True
            },
            brand_config={
                "name": "TechCorp",
                "colors": ["#0066CC", "#FFFFFF"],
                "typography": {"primary_font": "Helvetica Bold"},
                "tagline": "Innovation at Speed"
            }
        )

        # Step 2: Decompose into scenes
        scene_response = decompose_video_scenes(scene_request)

        assert scene_response.video_type == "ad"
        assert len(scene_response.scenes) == 3  # Intro, Development, CTA
        assert scene_response.total_duration == 30
        assert scene_response.brand_consistency_score is not None

        # Verify scene structure
        intro_scene = scene_response.scenes[0]
        assert intro_scene.scene_type.value == "introduction"
        assert intro_scene.duration > 0
        assert intro_scene.title

        dev_scene = scene_response.scenes[1]
        assert dev_scene.scene_type.value == "development"
        assert dev_scene.key_elements  # Should have product elements

        # Step 3: Create micro-prompts from scenes
        from ..models.brand_style_vector import create_default_style_vector

        brand_style_vector = create_default_style_vector("good_brand_adaptation")
        brand_style_vector.brand_name = "TechCorp"
        brand_style_vector.content_description = "TechCorp Super Widget advertisement"

        micro_prompt_request = MicroPromptRequest(
            generation_id="integration_test_123",
            scenes=[scene.dict() for scene in scene_response.scenes],
            prompt_analysis=scene_request.prompt_analysis,
            brand_config=scene_request.brand_config,
            brand_style_vector=brand_style_vector.dict()
        )

        service = MicroPromptBuilderService()
        prompt_response = await service.build_micro_prompts(micro_prompt_request)

        # Step 4: Verify results
        assert prompt_response.generation_id == "integration_test_123"
        assert len(prompt_response.micro_prompts) == 3
        assert prompt_response.total_scenes == 3
        assert prompt_response.average_confidence > 0

        # Check each micro-prompt
        for i, prompt in enumerate(prompt_response.micro_prompts):
            assert prompt.scene_id == f"scene_{i+1}"
            assert prompt.prompt_text
            assert len(prompt.prompt_text) > 50  # Should be substantial
            assert prompt.negative_prompt  # Should have negative prompts
            assert prompt.confidence_score > 0
            assert prompt.brand_elements  # Should include brand elements

            # Validate prompt quality
            validation = prompt.validate_prompt_quality()
            assert validation["is_valid"] is True

        # Step 5: Check brand integration across prompts
        all_brand_elements = []
        for prompt in prompt_response.micro_prompts:
            all_brand_elements.extend(prompt.brand_elements)

        # Should have TechCorp brand elements
        assert any("TechCorp" in element for element in all_brand_elements)

    @pytest.mark.asyncio
    async def test_pipeline_without_brand_config(self):
        """Test pipeline without brand configuration"""
        from ..models.scene_decomposition import decompose_video_scenes, SceneDecompositionRequest

        # Create request without brand config
        scene_request = SceneDecompositionRequest(
            video_type="ad",
            total_duration=15,
            prompt_analysis={
                "tone": "professional",
                "style": "minimalist",
                "key_themes": ["simplicity", "elegance"],
                "product_focus": False
            },
            brand_config=None
        )

        # Decompose scenes
        scene_response = decompose_video_scenes(scene_request)
        assert len(scene_response.scenes) == 3

        # Create micro-prompts without brand info
        micro_prompt_request = MicroPromptRequest(
            generation_id="no_brand_test_456",
            scenes=[scene.dict() for scene in scene_response.scenes],
            prompt_analysis=scene_request.prompt_analysis,
            brand_config=None,
            brand_style_vector=None
        )

        service = MicroPromptBuilderService()
        prompt_response = await service.build_micro_prompts(micro_prompt_request)

        # Should still generate valid prompts
        assert len(prompt_response.micro_prompts) == 3
        for prompt in prompt_response.micro_prompts:
            assert prompt.prompt_text
            assert prompt.style_vector_score == 0.7  # Default score
            assert len(prompt.brand_elements) == 0  # No brand elements

    @pytest.mark.asyncio
    async def test_pipeline_different_video_lengths(self):
        """Test pipeline with different video lengths"""
        from ..models.scene_decomposition import decompose_video_scenes, SceneDecompositionRequest

        test_cases = [
            (15, "short ad"),
            (30, "standard ad"),
            (60, "long ad")
        ]

        service = MicroPromptBuilderService()

        for duration, description in test_cases:
            scene_request = SceneDecompositionRequest(
                video_type="ad",
                total_duration=duration,
                prompt_analysis={"tone": "professional", "style": "modern"},
                brand_config={"name": f"Test Brand {duration}s"}
            )

            scene_response = decompose_video_scenes(scene_request)
            total_scene_duration = sum(scene.duration for scene in scene_response.scenes)

            # Should fit within the target duration (allowing small tolerance)
            assert abs(total_scene_duration - duration) < 1.0

            # Generate prompts
            micro_prompt_request = MicroPromptRequest(
                generation_id=f"duration_test_{duration}",
                scenes=[scene.dict() for scene in scene_response.scenes],
                prompt_analysis=scene_request.prompt_analysis,
                brand_config=scene_request.brand_config,
                brand_style_vector=None
            )

            prompt_response = await service.build_micro_prompts(micro_prompt_request)
            assert len(prompt_response.micro_prompts) == len(scene_response.scenes)

            # Check that prompt durations match scene durations
            for prompt, scene in zip(prompt_response.micro_prompts, scene_response.scenes):
                assert prompt.estimated_duration == scene.duration
