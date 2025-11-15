"""
API v1 routes
Block 0: API Skeleton & Core Infrastructure
"""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException
from app.core.logging import get_request_logger
from app.models.schemas import (
    GenerationRequest,
    CreateGenerationResponse,
    GenerationResponse,
    GenerationStatus,
    GenerationProgress
)
from app.core.errors import NotFoundError

# Import AI services (BLOCK A)
try:
    from ai.services.prompt_analysis_service import PromptAnalysisService
    from ai.services.brand_analysis_service import BrandAnalysisService
    from ai.models.prompt_analysis import AnalysisRequest
    AI_SERVICES_AVAILABLE = True
except ImportError:
    AI_SERVICES_AVAILABLE = False

# Create API v1 router
api_v1_router = APIRouter(prefix="/api/v1", tags=["api-v1"])

# Placeholder storage (will be replaced with Redis/Postgres)
_generation_store = {}


@api_v1_router.get("/")
async def api_v1_root():
    """API v1 root endpoint"""
    return {"message": "AI Video Generation Pipeline API v1", "status": "active"}


@api_v1_router.post("/generations", response_model=CreateGenerationResponse, status_code=201)
async def create_generation(
    generation_request: GenerationRequest,
    request: Request
) -> CreateGenerationResponse:
    """
    Create a new video generation job.

    This endpoint accepts a generation request and creates a new job for processing.
    The job is initially queued and will be processed asynchronously.

    Includes prompt analysis for consistent video generation.
    """
    logger = get_request_logger(request)
    logger.info(f"Creating new generation with prompt: {generation_request.prompt[:50]}...")

    # PR 101: Analyze the prompt for consistency
    prompt_analysis = None
    brand_config = None

    if AI_SERVICES_AVAILABLE:
        try:
            logger.info("Starting prompt analysis...")
            # Initialize service with mock mode for MVP (will be configured with real OpenAI key later)
            analysis_service = PromptAnalysisService(openai_api_key="dummy_key", use_mock=True)
            analysis_request = AnalysisRequest(prompt=generation_request.prompt)
            analysis_response = await analysis_service.analyze_prompt(analysis_request)
            prompt_analysis = analysis_response.analysis.dict()
            logger.info(f"Prompt analysis completed (confidence: {prompt_analysis.get('confidence_score', 0)})")

            # PR 102: Analyze brand configuration if available
            if generation_request.parameters.brand:
                logger.info("Starting brand analysis...")
                brand_service = BrandAnalysisService(openai_api_key="dummy_key", use_mock=True)
                brand_config = await brand_service.analyze_brand(
                    analysis_response.analysis,
                    generation_request.parameters.brand
                )
                logger.info(f"Brand analysis completed for: {brand_config.name}")
            elif prompt_analysis.get('product_focus'):
                # Even if no explicit brand config, check if prompt contains brand info
                logger.info("Checking prompt for implicit brand information...")
                brand_service = BrandAnalysisService(openai_api_key="dummy_key", use_mock=True)
                brand_config = await brand_service.analyze_brand(analysis_response.analysis)
                if brand_config.name != "Corporate Brand":  # Not using default
                    logger.info(f"Found implicit brand info: {brand_config.name}")
                else:
                    brand_config = None
            else:
                logger.info("No brand configuration needed for this generation")

        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            # For MVP: fail the entire request as specified
            raise HTTPException(status_code=500, detail=f"Failed to analyze content: {str(e)}")
    else:
        logger.warning("AI services not available, proceeding without analysis")

    # Generate unique ID for the generation
    generation_id = f"gen_{uuid.uuid4().hex[:16]}"

    # Calculate estimated completion time (placeholder logic)
    duration_seconds = generation_request.parameters.duration_seconds
    base_processing_time = 60  # Base processing time in seconds
    estimated_completion = datetime.utcnow() + timedelta(seconds=base_processing_time)

    # Create response
    response = CreateGenerationResponse(
        generation_id=generation_id,
        status=GenerationStatus.QUEUED,
        created_at=datetime.utcnow(),
        estimated_completion=estimated_completion,
        websocket_url=f"/ws/generations/{generation_id}"
    )

    # TODO: Add Redis integration point
    # - Store generation metadata in Redis with TTL
    # - Add to processing queue
    # Placeholder: Store in memory for now
    _generation_store[generation_id] = {
        "id": generation_id,
        "status": GenerationStatus.QUEUED,
        "request": generation_request.dict(),
        "prompt_analysis": prompt_analysis,  # PR 101: Store analysis results
        "brand_config": brand_config.dict() if brand_config else None,  # PR 102: Store brand config
        "created_at": response.created_at,
        "updated_at": response.created_at,
        "progress": None
    }

    logger.info(f"Generation {generation_id} created successfully")
    return response


@api_v1_router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation(generation_id: str, request: Request) -> GenerationResponse:
    """
    Get the status and progress of a video generation job.

    Returns detailed information about the generation including current status,
    progress, and any generated clips.
    """
    logger = get_request_logger(request)
    logger.info(f"Retrieving generation {generation_id}")

    # TODO: Add Redis integration point
    # - Fetch generation data from Redis
    # Placeholder: Fetch from memory store
    generation_data = _generation_store.get(generation_id)
    if not generation_data:
        # TODO: Add Postgres integration point
        # - Check persistent storage for completed generations
        raise NotFoundError("generation", generation_id)

    # Build progress information (placeholder logic)
    progress = None
    if generation_data["status"] == GenerationStatus.PROCESSING:
        progress = GenerationProgress(
            current_step="generating_clips",
            steps_completed=3,
            total_steps=8,
            percentage=37.5,
            current_clip=2,
            total_clips=5
        )

    # Build response
    response = GenerationResponse(
        generation_id=generation_id,
        status=generation_data["status"],
        progress=progress,
        metadata={
            "prompt": generation_data["request"]["prompt"],
            "parameters": generation_data["request"]["parameters"],
            "created_at": generation_data["created_at"].isoformat() + "Z",
            "updated_at": generation_data["updated_at"].isoformat() + "Z"
        },
        created_at=generation_data["created_at"],
        updated_at=generation_data["updated_at"],
        clips_generated=None  # Will be populated when clips are generated
    )

    logger.info(f"Generation {generation_id} retrieved successfully")
    return response
