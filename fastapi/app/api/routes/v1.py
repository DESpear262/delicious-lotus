"""
API v1 routes
Block 0: API Skeleton & Core Infrastructure
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from app.core.logging import get_request_logger
from app.core.config import settings
from app.models.schemas import (
    GenerationRequest,
    CreateGenerationResponse,
    GenerationResponse,
    GenerationStatus,
    GenerationProgress
)
from app.core.errors import NotFoundError

# Set up module-level logger
logger = logging.getLogger(__name__)

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
except ImportError as e:
    AI_SERVICES_AVAILABLE = False
    # Define fallback types for when AI services are not available
    # These are used in function signatures but won't be used at runtime
    from typing import Any
    AnalysisRequest = Any
    MicroPromptRequest = Any
    SceneDecompositionRequest = Any
    SceneDecompositionResponse = Any
    ClipAssemblyRequest = Any
    ClipRetrievalRequest = Any
    EditRequest = Any
    EditResponse = Any
    PromptAnalysisService = None
    BrandAnalysisService = None
    MicroPromptBuilderService = None
    ClipAssemblyService = None
    EditIntentClassifierService = None
    logger.warning(f"AI services not available: {e}")

# Create API v1 router
api_v1_router = APIRouter(prefix="/api/v1", tags=["api-v1"])

# Initialize services
clip_assembly_service = None
edit_classifier_service = None
storage_service = None
generation_storage_service = None

# Initialize storage services
try:
    from app.services.storage import StorageService
    from app.core.config import settings
    
    storage_service = StorageService(
        use_local=settings.use_local_storage,
        local_storage_path=settings.local_storage_path,
        s3_bucket=settings.s3_bucket,
        aws_region=settings.aws_region
    )
    logger.info("StorageService initialized")
except Exception as e:
    logger.warning(f"Failed to initialize StorageService: {str(e)}")

# Initialize generation storage service
try:
    from app.services.generation_storage import GenerationStorageService
    from app.core.config import settings
    
    if settings.database_url:
        generation_storage_service = GenerationStorageService(database_url=settings.database_url)
        logger.info("GenerationStorageService initialized")
    else:
        logger.warning("DATABASE_URL not set - generation storage will use in-memory fallback")
except Exception as e:
    logger.warning(f"Failed to initialize GenerationStorageService: {str(e)}")

if AI_SERVICES_AVAILABLE:
    try:
        # If we have a database URL, reuse its config for clip assembly service so it
        # connects to the same PostgreSQL instance as GenerationStorageService.
        clip_db_config = None
        if generation_storage_service:
            clip_db_config = getattr(generation_storage_service, "db_config", None)

        clip_assembly_service = ClipAssemblyService(db_config=clip_db_config)
    except Exception as e:
        logger.warning(f"Failed to initialize clip assembly service: {str(e)}")

    try:
        edit_classifier_service = EditIntentClassifierService(
            openai_api_key="dummy_key",  # Will be configured with real key later
            use_mock=True  # Use mock for MVP
        )
    except Exception as e:
        logger.warning(f"Failed to initialize edit classifier service: {str(e)}")

# Placeholder storage (fallback if database not available)
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
    print(f"\n[START] Processing prompt: {generation_request.prompt[:100]}{'...' if len(generation_request.prompt) > 100 else ''}")

    # Generate unique ID for the generation (needed for micro-prompt generation)
    generation_id = f"gen_{uuid.uuid4().hex[:16]}"
    print(f"[INFO] Generation ID: {generation_id}")

    # PR 101: Analyze the prompt for consistency
    prompt_analysis = None
    brand_config = None
    scenes = None
    micro_prompts = None

    if AI_SERVICES_AVAILABLE:
        try:
            print("\n[STEP 1] Analyzing prompt...")
            logger.info("Starting prompt analysis...")
            # Initialize service with mock mode for MVP (will be configured with real OpenAI key later)
            analysis_service = PromptAnalysisService(openai_api_key="dummy_key", use_mock=True)
            analysis_request = AnalysisRequest(prompt=generation_request.prompt)
            analysis_response = await analysis_service.analyze_prompt(analysis_request)
            prompt_analysis = analysis_response.analysis.dict()
            logger.info(f"Prompt analysis completed (confidence: {prompt_analysis.get('confidence_score', 0)})")
            print(f"[OK] Prompt analysis complete (confidence: {prompt_analysis.get('confidence_score', 0):.2f})")

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
            print("\n[STEP 2] Decomposing into scenes...")
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
            print(f"[OK] Generated {len(scenes)} scenes")

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

            print("\n[STEP 3] Building micro-prompts...")
            prompt_builder = MicroPromptBuilderService()
            micro_prompt_response = await prompt_builder.build_micro_prompts(micro_prompt_request)
            micro_prompts = [mp.dict() for mp in micro_prompt_response.micro_prompts]
            logger.info(f"Micro-prompt generation completed: {len(micro_prompts)} prompts created")
            print(f"[OK] Generated {len(micro_prompts)} micro-prompts")

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

    # Always store basic generation metadata in in-memory store so that
    # GET /api/v1/generations/{id} can return a record even if database
    # or clip storage are unavailable.
    _generation_store[generation_id] = {
        "id": generation_id,
        "status": GenerationStatus.QUEUED,
        "request": generation_request.dict(),
        "prompt_analysis": prompt_analysis,
        "brand_config": brand_config.dict() if brand_config else None,
        "scenes": scenes,
        "micro_prompts": micro_prompts,
        "created_at": response.created_at,
        "updated_at": response.created_at,
        "progress": None,
    }

    # Store generation metadata in database
    if generation_storage_service:
        try:
            generation_storage_service.create_generation(
                generation_id=generation_id,
                prompt=generation_request.prompt,
                status=GenerationStatus.QUEUED.value,
                metadata={
                    "prompt_analysis": prompt_analysis,
                    "brand_config": brand_config.dict() if brand_config else None,
                    "scenes": scenes,
                    "micro_prompts": micro_prompts,
                    "parameters": generation_request.parameters.dict(),
                    "options": generation_request.options.dict() if generation_request.options else None
                },
                duration_seconds=generation_request.parameters.duration_seconds
            )
            logger.info(f"Stored generation {generation_id} in database")
        except Exception as e:
            logger.error(f"Failed to store generation in database: {str(e)}")

    # Generate video clips using the centralized function
    # TODO: Move this to a background task/worker for production
    if scenes and micro_prompts and len(scenes) == len(micro_prompts):
        try:
            # Import the video generation function
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent.parent
            
            # Add the ffmpeg-backend src directory to path so relative imports work
            ffmpeg_backend_src = project_root / 'ffmpeg-backend' / 'src'
            if str(ffmpeg_backend_src) not in sys.path:
                sys.path.insert(0, str(ffmpeg_backend_src))
            
            # Import as a proper module (app.api.v1.replicate)
            from app.api.v1.replicate import generate_video_clips
            
            # Get parallelization setting from request
            parallelize = generation_request.options.parallelize_generations if generation_request.options else False
            
            # Extract aspect ratio - AspectRatio enum values are already strings like "16:9"
            aspect_ratio = str(generation_request.parameters.aspect_ratio.value) if hasattr(generation_request.parameters.aspect_ratio, 'value') else str(generation_request.parameters.aspect_ratio)
            
            print(f"\n[STEP 4] Generating videos...")
            logger.info(f"Starting video generation for {len(micro_prompts)} clips (parallelize={parallelize}, aspect_ratio={aspect_ratio})")
            print(f"[INFO] Generating {len(micro_prompts)} clips (parallelize={parallelize}, aspect_ratio={aspect_ratio})")
            
            # Extract prompt_text from micro_prompts (they're dicts with 'prompt_text' field)
            micro_prompt_texts = []
            for mp in micro_prompts:
                if isinstance(mp, dict):
                    prompt_text = mp.get('prompt_text', '')
                    if not prompt_text:
                        # Fallback: try to get from nested structure
                        prompt_text = mp.get('prompt', '') or str(mp)
                    micro_prompt_texts.append(prompt_text)
                else:
                    # If it's already a string or has prompt_text attribute
                    micro_prompt_texts.append(getattr(mp, 'prompt_text', str(mp)))
            
            # Get webhook base URL from settings or environment
            webhook_base_url = settings.webhook_base_url or os.getenv('WEBHOOK_BASE_URL')
            if not webhook_base_url:
                # Try to construct from request if available
                try:
                    webhook_base_url = f"{request.url.scheme}://{request.url.hostname}"
                    if request.url.port and request.url.port not in [80, 443]:
                        webhook_base_url += f":{request.url.port}"
                except:
                    logger.warning("Could not determine webhook base URL - webhooks will not work")
                    webhook_base_url = None
            
            # Generate clips using the centralized function (with storage service and webhooks)
            video_results = await generate_video_clips(
                scenes=scenes,
                micro_prompts=micro_prompt_texts,
                generation_id=generation_id,
                aspect_ratio=aspect_ratio,
                parallelize=parallelize,
                use_mock=False,
                storage_service=storage_service,
                webhook_base_url=webhook_base_url
            )
            
            # Store prediction_id mappings for webhook handler
            if webhook_base_url:
                try:
                    from app.api.routes.webhooks import store_prediction_mapping
                    for result in video_results:
                        if result.get('prediction_id') and result.get('clip_id'):
                            store_prediction_mapping(
                                prediction_id=result['prediction_id'],
                                generation_id=generation_id,
                                clip_id=result['clip_id'],
                                scene_id=result.get('scene_id', '')
                            )
                except ImportError:
                    logger.warning("Could not import store_prediction_mapping - webhook mappings not stored")
                except Exception as e:
                    logger.error(f"Failed to store prediction mappings: {e}")
            
            # Store initial video results (all will be "queued" status with webhooks)
            # Webhook handler will update status to "completed" when each clip finishes
            queued_count = len([r for r in video_results if r.get('status') == 'queued'])
            if generation_storage_service:
                try:
                    # Update status to PROCESSING (generation started, waiting for webhooks)
                    generation_storage_service.update_generation(
                        generation_id=generation_id,
                        status=GenerationStatus.PROCESSING.value,
                        metadata={"video_results": video_results}
                    )
                    logger.info(f"Updated generation {generation_id} status to PROCESSING ({queued_count} clips queued)")
                except Exception as e:
                    logger.error(f"Failed to update generation status in database: {str(e)}")
            
            # Also update in-memory store (fallback)
            if generation_id in _generation_store:
                _generation_store[generation_id]["video_results"] = video_results
                _generation_store[generation_id]["status"] = GenerationStatus.PROCESSING
            
            logger.info(f"Video generation started: {queued_count}/{len(video_results)} clips queued (webhooks will update status when complete)")
            print(f"[OK] Video generation started: {queued_count}/{len(video_results)} clips queued")
            print(f"[INFO] Webhooks will update status when each clip completes")
            
        except ImportError as e:
            logger.warning(f"Could not import generate_video_clips: {e}. Video generation will need to be handled separately.")
            print(f"[ERROR] Could not import generate_video_clips: {e}")
        except Exception as e:
            logger.error(f"Video generation failed: {str(e)}")
            print(f"[ERROR] Video generation failed: {str(e)}")
            # Don't fail the entire request, just log the error
            _generation_store[generation_id]["video_generation_error"] = str(e)

    logger.info(f"Generation {generation_id} created successfully")
    print(f"\n[SUCCESS] Generation {generation_id} created successfully")
    return response


@api_v1_router.get("/generations", status_code=200)
async def list_generations(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None)
):
    """
    List all generations with pagination
    
    Returns a paginated list of generation records with metadata.
    """
    logger = get_request_logger(request)
    logger.info(f"Listing generations (limit={limit}, offset={offset}, status={status})")
    
    try:
        # Try to get from database first
        if generation_storage_service:
            generations = generation_storage_service.list_generations(
                limit=limit,
                offset=offset,
                status=status
            )
            total = generation_storage_service.count_generations(status=status)
        else:
            # Fallback to in-memory store
            all_generations = list(_generation_store.values())
            
            # Filter by status if provided
            if status:
                all_generations = [g for g in all_generations if g.get("status") == status]
            
            # Sort by created_at descending
            all_generations.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
            
            # Paginate
            total = len(all_generations)
            generations = all_generations[offset:offset + limit]
            
            # Convert to API format
            generations = [
                {
                    "generation_id": g["id"],
                    "status": g.get("status", "unknown"),
                    "prompt": g.get("request", {}).get("prompt", "")[:100],  # Truncate for list view
                    "thumbnail_url": None,  # TODO: Generate thumbnails
                    "created_at": g.get("created_at", datetime.utcnow()).isoformat() + "Z",
                    "duration_seconds": g.get("request", {}).get("parameters", {}).get("duration_seconds", 30)
                }
                for g in generations
            ]
        
        # Calculate pagination metadata
        pages = (total + limit - 1) // limit if limit > 0 else 1
        page = (offset // limit) + 1 if limit > 0 else 1
        
        return {
            "generations": generations,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            }
        }
    except Exception as e:
        logger.error(f"Failed to list generations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list generations: {str(e)}")


@api_v1_router.post("/assets/upload", status_code=201)
async def upload_asset(
    request: Request,
    file: UploadFile = File(...),
    type: str = Form("image")
):
    """
    Upload an asset (logo, image, audio, etc.)
    
    This is a stub endpoint that returns a mock response.
    In production, this should:
    - Validate file type and size
    - Upload to S3 or storage service
    - Store metadata in database
    - Return asset URL and metadata
    """
    logger = get_request_logger(request)
    logger.info(f"Asset upload requested: {file.filename}, type: {type}")
    
    # Stub implementation - return mock response
    asset_id = f"asset_{uuid.uuid4().hex[:16]}"
    
    # In production, would:
    # 1. Validate file (size, type, etc.)
    # 2. Upload to S3/storage
    # 3. Store metadata in database
    # 4. Return actual URL
    
    return JSONResponse(
        status_code=201,
        content={
            "asset_id": asset_id,
            "url": f"https://storage.example.com/assets/{asset_id}/{file.filename}",
            "filename": file.filename,
            "type": type,
            "size": 0,  # Would be actual file size
            "status": "uploaded"
        }
    )


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
