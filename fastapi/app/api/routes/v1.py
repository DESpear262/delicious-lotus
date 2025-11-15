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

# Import AI services (BLOCK A, C & D)
try:
    from ai.services.prompt_analysis_service import PromptAnalysisService
    from ai.services.brand_analysis_service import BrandAnalysisService
    from ai.services.micro_prompt_builder_service import MicroPromptBuilderService
    from ai.services.clip_assembly_service import ClipAssemblyService
    from ai.services.edit_intent_classifier_service import EditIntentClassifierService
    from ai.models.prompt_analysis import AnalysisRequest
    from ai.models.micro_prompt import MicroPromptRequest
    from ai.models.scene_decomposition import SceneDecompositionRequest, SceneDecompositionResponse
    from ai.models.clip_assembly import ClipAssemblyRequest, ClipRetrievalRequest
    from ai.models.edit_intent import EditRequest, EditResponse
    AI_SERVICES_AVAILABLE = True
except ImportError:
    AI_SERVICES_AVAILABLE = False

# Create API v1 router
api_v1_router = APIRouter(prefix="/api/v1", tags=["api-v1"])

# Initialize services
clip_assembly_service = None
edit_classifier_service = None
if AI_SERVICES_AVAILABLE:
    try:
        clip_assembly_service = ClipAssemblyService()
    except Exception as e:
        logger.warning(f"Failed to initialize clip assembly service: {str(e)}")

    try:
        edit_classifier_service = EditIntentClassifierService(
            openai_api_key="dummy_key",  # Will be configured with real key later
            use_mock=True  # Use mock for MVP
        )
    except Exception as e:
        logger.warning(f"Failed to initialize edit classifier service: {str(e)}")

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

    # Generate unique ID for the generation (needed for micro-prompt generation)
    generation_id = f"gen_{uuid.uuid4().hex[:16]}"

    # PR 101: Analyze the prompt for consistency
    prompt_analysis = None
    brand_config = None
    scenes = None
    micro_prompts = None

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

            # PR 301: Generate micro-prompts from scenes (PR 103 scene decomposition is conceptually complete)
            logger.info("Starting scene decomposition and micro-prompt generation...")
            from ai.models.scene_decomposition import decompose_video_scenes

            # Decompose video into scenes using PR 103 logic
            scene_request = SceneDecompositionRequest(
                video_type="ad",  # MVP focus on ads
                total_duration=generation_request.parameters.duration_seconds,
                prompt_analysis=prompt_analysis,
                brand_config=brand_config.dict() if brand_config else None
            )
            scene_response = decompose_video_scenes(scene_request)
            scenes = [scene.dict() for scene in scene_response.scenes]
            logger.info(f"Scene decomposition completed: {len(scenes)} scenes generated")

            # Build micro-prompts for each scene
            brand_style_vector = None
            if brand_config:
                # Create a basic style vector from brand analysis (simplified for MVP)
                from ai.models.brand_style_vector import create_default_style_vector
                brand_style_vector = create_default_style_vector("good_brand_adaptation")
                brand_style_vector.brand_name = brand_config.name
                brand_style_vector.content_description = generation_request.prompt[:100]

            micro_prompt_request = MicroPromptRequest(
                generation_id=generation_id,
                scenes=scenes,
                prompt_analysis=prompt_analysis,
                brand_config=brand_config.dict() if brand_config else None,
                brand_style_vector=brand_style_vector.dict() if brand_style_vector else None
            )

            prompt_builder = MicroPromptBuilderService()
            micro_prompt_response = await prompt_builder.build_micro_prompts(micro_prompt_request)
            micro_prompts = [mp.dict() for mp in micro_prompt_response.micro_prompts]
            logger.info(f"Micro-prompt generation completed: {len(micro_prompts)} prompts created")

        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            # For MVP: fail the entire request as specified
            raise HTTPException(status_code=500, detail=f"Failed to analyze content: {str(e)}")
    else:
        logger.warning("AI services not available, proceeding without analysis")

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
        "scenes": scenes,  # PR 103: Store decomposed scenes
        "micro_prompts": micro_prompts,  # PR 301: Store generated micro-prompts
        "created_at": response.created_at,
        "updated_at": response.created_at,
        "progress": None
    }

    logger.info(f"Generation {generation_id} created successfully")
    return response


@api_v1_router.post("/generations/{generation_id}/clips", status_code=201)
async def store_clips(
    generation_id: str,
    clip_request: ClipAssemblyRequest,
    request: Request
):
    """
    Store clips and update progress for a generation job.

    This endpoint is called by the clip generation service to persist
    completed clips and update generation progress.
    """
    logger = get_request_logger(request)
    logger.info(f"Storing clips for generation {generation_id}")

    if not clip_assembly_service:
        logger.error("Clip assembly service not available")
        raise HTTPException(status_code=503, detail="Clip storage service unavailable")

    try:
        response = await clip_assembly_service.assemble_clips(clip_request)

        if not response.success:
            logger.error(f"Clip assembly failed: {response.errors}")
            raise HTTPException(status_code=500, detail=f"Clip assembly failed: {response.errors}")

        logger.info(f"Successfully stored {response.clips_stored} clips for generation {generation_id}")
        return {
            "generation_id": generation_id,
            "clips_stored": response.clips_stored,
            "stored_clip_ids": response.stored_clip_ids
        }

    except Exception as e:
        logger.error(f"Failed to store clips for generation {generation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store clips: {str(e)}")


@api_v1_router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation(generation_id: str, request: Request) -> GenerationResponse:
    """
    Get the status and progress of a video generation job.

    Returns detailed information about the generation including current status,
    progress, and any generated clips.
    """
    logger = get_request_logger(request)
    logger.info(f"Retrieving generation {generation_id}")

    # First try to get data from clip assembly service (database/Redis)
    clips_data = None
    progress_data = None

    if clip_assembly_service:
        try:
            # Retrieve clips and progress from persistent storage
            retrieval_request = ClipRetrievalRequest(generation_id=generation_id)
            clips_response = clip_assembly_service.retrieve_clips(retrieval_request)
            clips_data = clips_response.clips
            progress_data = clips_response.progress
            logger.info(f"Retrieved {len(clips_data)} clips from persistent storage")
        except Exception as e:
            logger.warning(f"Failed to retrieve from persistent storage: {str(e)}")

    # Fallback to in-memory store if no persistent data
    generation_data = _generation_store.get(generation_id)
    if not generation_data and not clips_data:
        raise NotFoundError("generation", generation_id)

    # Determine status and progress
    if progress_data:
        # Use progress from Redis
        progress = GenerationProgress(
            current_step=progress_data.current_step,
            steps_completed=progress_data.completed_clips,
            total_steps=progress_data.total_clips,
            percentage=progress_data.progress_percentage,
            current_clip=progress_data.current_clip_index,
            total_clips=progress_data.total_clips
        )
        status = progress_data.status
    elif generation_data:
        # Fallback to in-memory logic
        status = generation_data["status"]
        progress = None
        if status == GenerationStatus.PROCESSING:
            progress = GenerationProgress(
                current_step="generating_clips",
                steps_completed=3,
                total_steps=8,
                percentage=37.5,
                current_clip=2,
                total_clips=5
            )
    else:
        # Default status if no data available
        status = GenerationStatus.QUEUED
        progress = None

    # Convert clips data to API format
    clips_generated = None
    if clips_data:
        clips_generated = []
        for clip in clips_data:
            clips_generated.append(ClipMetadata(
                clip_id=clip.clip_id,
                url=clip.video_url or "",
                thumbnail_url=clip.thumbnail_url,
                duration=clip.duration_seconds,
                start_time=clip.start_time_seconds,
                end_time=clip.end_time_seconds,
                prompt=clip.prompt_used
            ))

    # Build metadata
    metadata = {}
    if generation_data:
        metadata.update({
            "prompt": generation_data["request"]["prompt"],
            "parameters": generation_data["request"]["parameters"],
            "created_at": generation_data["created_at"].isoformat() + "Z",
            "updated_at": generation_data["updated_at"].isoformat() + "Z"
        })

    # Add clip statistics to metadata
    if clips_data:
        total_clips = len(clips_data)
        completed_clips = sum(1 for c in clips_data if c.is_successful())
        failed_clips = sum(1 for c in clips_data if c.storage_status.value == "failed")

        metadata.update({
            "total_clips": total_clips,
            "completed_clips": completed_clips,
            "failed_clips": failed_clips,
            "completion_percentage": (completed_clips / total_clips * 100) if total_clips > 0 else 0
        })

    # Determine timestamps
    if generation_data:
        created_at = generation_data["created_at"]
        updated_at = generation_data["updated_at"]
    else:
        # Fallback timestamps
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

    # Build response
    response = GenerationResponse(
        generation_id=generation_id,
        status=status,
        progress=progress,
        metadata=metadata,
        created_at=created_at,
        updated_at=updated_at,
        clips_generated=clips_generated
    )

    logger.info(f"Generation {generation_id} retrieved successfully")
    return response


@api_v1_router.post("/generations/{generation_id}/edit", response_model=EditResponse)
async def classify_edit_intent(
    generation_id: str,
    edit_request: EditRequest,
    request: Request
):
    """
    Classify a natural language edit request and generate an edit plan.

    This endpoint uses AI to interpret user edit requests and convert them
    into structured FFmpeg operations that can be executed by the video processing backend.
    """
    logger = get_request_logger(request)
    logger.info(f"Classifying edit intent for generation {generation_id}")

    if not edit_classifier_service:
        logger.error("Edit classifier service not available")
        raise HTTPException(status_code=503, detail="Edit classification service unavailable")

    # Validate that the generation exists
    if clip_assembly_service:
        try:
            # Check if generation exists in persistent storage
            retrieval_request = ClipRetrievalRequest(generation_id=generation_id)
            clips_response = clip_assembly_service.retrieve_clips(retrieval_request)
            if clips_response.total_clips > 0:
                # Use clip count from persistent storage
                edit_request.current_clip_count = clips_response.total_clips
                edit_request.total_duration_seconds = sum(
                    clip.duration_seconds for clip in clips_response.clips
                )
        except Exception as e:
            logger.warning(f"Could not retrieve generation data: {str(e)}")

    # Ensure generation_id matches
    edit_request.generation_id = generation_id

    try:
        response = await edit_classifier_service.classify_edit_intent(edit_request)

        if not response.success:
            logger.warning(f"Edit classification failed: {response.error_message}")
            raise HTTPException(status_code=400, detail=response.error_message)

        logger.info(f"Edit classification completed for generation {generation_id}: {len(response.edit_plan.operations)} operations")
        return response

    except Exception as e:
        logger.error(f"Failed to classify edit intent for generation {generation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to classify edit request: {str(e)}")
