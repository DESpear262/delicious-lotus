"""
Recomposition Trigger Service - PR 403: Recomposition Trigger
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import httpx

from ..models.recomposition import (
    RecompositionTriggerRequest,
    RecompositionTriggerResponse,
    UpdatedCompositionConfig,
    RecompositionRecord,
    RecompositionStatus,
    ClipEditInstruction,
    TransitionEditInstruction,
    OverlayEditInstruction,
    FFmpegJobTriggerRequest,
    FFmpegJobTriggerResponse
)
from ..models.edit_intent import EditPlan, FFmpegOperation, EditOperation, EditTarget

logger = logging.getLogger(__name__)


class RecompositionTriggerService:
    """
    Service for triggering FFmpeg recomposition based on timeline edit plans

    Converts edit operations into composition configuration changes and triggers
    FFmpeg jobs via HTTP API calls to the FFmpeg backend service.
    """

    def __init__(self, ffmpeg_backend_url: str, request_timeout: float = 30.0):
        """
        Initialize the recomposition trigger service

        Args:
            ffmpeg_backend_url: Base URL for the FFmpeg backend service
            request_timeout: Timeout for HTTP requests to FFmpeg backend
        """
        self.ffmpeg_backend_url = ffmpeg_backend_url.rstrip('/')
        self.request_timeout = request_timeout

        # In-memory storage for recomposition records (would be database in production)
        self._recomposition_records: Dict[str, RecompositionRecord] = {}

        logger.info(f"RecompositionTriggerService initialized with FFmpeg backend: {ffmpeg_backend_url}")

    async def trigger_recomposition(
        self,
        request: RecompositionTriggerRequest
    ) -> RecompositionTriggerResponse:
        """
        Trigger a recomposition based on an edit plan

        Args:
            request: Recomposition trigger request with edit plan

        Returns:
            Response with tracking information

        Raises:
            Exception: If recomposition trigger fails
        """
        try:
            logger.info(f"Triggering recomposition for composition {request.composition_id}")

            # Generate unique ID for this recomposition
            recomposition_id = f"recomp_{uuid.uuid4().hex[:16]}"

            # Build updated composition config from edit plan
            updated_config = await self._build_updated_config(
                request.generation_id,
                request.composition_id,
                request.edit_plan
            )

            # Create recomposition record
            record = RecompositionRecord(
                recomposition_id=recomposition_id,
                composition_id=request.composition_id,
                generation_id=request.generation_id,
                edit_plan=request.edit_plan,
                updated_config=updated_config
            )

            # Store record
            self._recomposition_records[recomposition_id] = record

            # Trigger FFmpeg job
            ffmpeg_response = await self._trigger_ffmpeg_job(
                recomposition_id,
                updated_config,
                request.priority,
                request.webhook_url
            )

            # Update record with FFmpeg job info
            record.mark_triggered(ffmpeg_response.job_id)

            # Create response
            response = RecompositionTriggerResponse(
                recomposition_id=recomposition_id,
                ffmpeg_job_id=ffmpeg_response.job_id,
                status=record.status,
                estimated_duration_seconds=ffmpeg_response.estimated_duration,
                status_url=f"/api/v1/recompositions/{recomposition_id}/status",
                result_url=f"/api/v1/recompositions/{recomposition_id}/result"
            )

            logger.info(f"Recomposition {recomposition_id} triggered successfully with FFmpeg job {ffmpeg_response.job_id}")
            return response

        except Exception as e:
            logger.error(f"Failed to trigger recomposition for {request.composition_id}: {e}")
            raise Exception(f"Recomposition trigger failed: {str(e)}")

    async def _build_updated_config(
        self,
        generation_id: str,
        composition_id: str,
        edit_plan: EditPlan
    ) -> UpdatedCompositionConfig:
        """
        Build updated composition config from edit plan

        Args:
            generation_id: Generation job ID
            composition_id: Composition ID
            edit_plan: Timeline edit plan

        Returns:
            Updated composition configuration
        """
        # Get original composition config (mock for now - would come from database/storage)
        original_config = await self._get_original_composition_config(composition_id)

        # Convert FFmpeg operations to edit instructions
        clip_edits = []
        transition_edits = []
        overlay_edits = []

        for operation in edit_plan.operations:
            if operation.target_type == EditTarget.CLIP:
                clip_edit = self._convert_clip_operation(operation)
                if clip_edit:
                    clip_edits.append(clip_edit)

            elif operation.target_type == EditTarget.TRANSITION:
                transition_edit = self._convert_transition_operation(operation)
                if transition_edit:
                    transition_edits.append(transition_edit)

            elif operation.target_type == EditTarget.OVERLAY:
                overlay_edit = self._convert_overlay_operation(operation)
                if overlay_edit:
                    overlay_edits.append(overlay_edit)

        # Create updated config
        updated_config = UpdatedCompositionConfig(
            composition_id=composition_id,
            generation_id=generation_id,
            target_duration=original_config.get("target_duration", 30.0),
            resolution=original_config.get("resolution", "1920x1080"),
            frame_rate=original_config.get("frame_rate", 30),
            clip_edits=clip_edits,
            transition_edits=transition_edits,
            overlay_edits=overlay_edits,
            original_config=original_config
        )

        return updated_config

    def _convert_clip_operation(self, operation: FFmpegOperation) -> Optional[ClipEditInstruction]:
        """Convert FFmpeg operation to clip edit instruction"""
        if not operation.target_clips:
            return None

        clip_index = operation.target_clips[0]  # Assume single clip for now
        edit_instruction = ClipEditInstruction(clip_index=clip_index)

        if operation.operation_type == EditOperation.TRIM:
            if operation.target_time_range:
                start_time = operation.target_time_range.get("start", 0.0)
                end_time = operation.target_time_range.get("end")
                if end_time:
                    edit_instruction.trim_start = start_time
                    edit_instruction.trim_end = end_time

        elif operation.operation_type == EditOperation.SPLIT:
            # Split operations would create multiple clips - simplified for now
            logger.warning(f"Split operation not fully implemented for clip {clip_index}")

        elif operation.operation_type == EditOperation.MERGE:
            # Merge operations would combine clips - simplified for now
            logger.warning(f"Merge operation not fully implemented for clip {clip_index}")

        # Only return if we actually have edits
        if any([
            edit_instruction.new_index is not None,
            edit_instruction.trim_start is not None,
            edit_instruction.trim_end is not None,
            edit_instruction.duration_override is not None,
            edit_instruction.speed_multiplier is not None,
            edit_instruction.volume_multiplier is not None,
            edit_instruction.fade_in_duration is not None,
            edit_instruction.fade_out_duration is not None
        ]):
            return edit_instruction

        return None

    def _convert_transition_operation(self, operation: FFmpegOperation) -> Optional[TransitionEditInstruction]:
        """Convert FFmpeg operation to transition edit instruction"""
        if len(operation.target_clips or []) < 2:
            return None

        between_clips = (operation.target_clips[0], operation.target_clips[1])

        edit_instruction = TransitionEditInstruction(between_clips=between_clips)

        # Extract transition parameters from operation metadata
        if operation.operation_type == EditOperation.MERGE:  # Transitions often come from merge operations
            if hasattr(operation, 'parameters') and operation.parameters:
                params = operation.parameters
                edit_instruction.transition_type = params.get("transition_type")
                edit_instruction.duration = params.get("duration")
                edit_instruction.easing = params.get("easing")

        # Only return if we have actual changes
        if any([
            edit_instruction.transition_type is not None,
            edit_instruction.duration is not None,
            edit_instruction.easing is not None
        ]):
            return edit_instruction

        return None

    def _convert_overlay_operation(self, operation: FFmpegOperation) -> Optional[OverlayEditInstruction]:
        """Convert FFmpeg operation to overlay edit instruction"""
        if not hasattr(operation, 'parameters') or not operation.parameters:
            return None

        params = operation.parameters

        edit_instruction = OverlayEditInstruction(
            overlay_id=params.get("overlay_id", f"overlay_{operation.target_clips[0] if operation.target_clips else 'unknown'}")
        )

        # Extract overlay parameters
        edit_instruction.text_content = params.get("text_content")
        edit_instruction.position = params.get("position")
        edit_instruction.timing = params.get("timing")
        edit_instruction.style = params.get("style")

        # Only return if we have actual changes
        if any([
            edit_instruction.text_content is not None,
            edit_instruction.position is not None,
            edit_instruction.timing is not None,
            edit_instruction.style is not None
        ]):
            return edit_instruction

        return None

    async def _get_original_composition_config(self, composition_id: str) -> Dict[str, Any]:
        """
        Get original composition config (would come from database in production)

        Args:
            composition_id: Composition ID

        Returns:
            Original composition configuration
        """
        # Mock implementation - in production this would query the database
        # for the original composition config associated with the composition_id
        return {
            "target_duration": 30.0,
            "resolution": "1920x1080",
            "frame_rate": 30,
            "clips": [
                {"index": 0, "duration": 10.0, "source": "clip1.mp4"},
                {"index": 1, "duration": 10.0, "source": "clip2.mp4"},
                {"index": 2, "duration": 10.0, "source": "clip3.mp4"}
            ],
            "transitions": [],
            "overlays": []
        }

    async def _trigger_ffmpeg_job(
        self,
        recomposition_id: str,
        config: UpdatedCompositionConfig,
        priority: str = "normal",
        webhook_url: Optional[str] = None
    ) -> FFmpegJobTriggerResponse:
        """
        Trigger FFmpeg job via HTTP API

        Args:
            recomposition_id: Recomposition ID
            config: Updated composition config
            priority: Job priority
            webhook_url: Completion webhook URL

        Returns:
            FFmpeg job response

        Raises:
            Exception: If FFmpeg API call fails
        """
        try:
            # Build FFmpeg trigger request
            trigger_request = FFmpegJobTriggerRequest(
                composition_id=config.composition_id,
                config=config,
                priority=priority,
                webhook_url=webhook_url,
                generation_id=config.generation_id,
                edit_summary=self._create_edit_summary(config)
            )

            # Make HTTP request to FFmpeg backend
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.post(
                    f"{self.ffmpeg_backend_url}/api/v1/compositions",
                    json=trigger_request.dict(),
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    raise Exception(f"FFmpeg backend returned {response.status_code}: {response.text}")

                response_data = response.json()

                return FFmpegJobTriggerResponse(**response_data)

        except httpx.RequestError as e:
            logger.error(f"HTTP request failed to FFmpeg backend: {e}")
            raise Exception(f"Failed to communicate with FFmpeg backend: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to trigger FFmpeg job for recomposition {recomposition_id}: {e}")
            raise Exception(f"FFmpeg job trigger failed: {str(e)}")

    def _create_edit_summary(self, config: UpdatedCompositionConfig) -> str:
        """Create a human-readable summary of the edits applied"""
        summary_parts = []

        if config.clip_edits:
            summary_parts.append(f"{len(config.clip_edits)} clip edits")

        if config.transition_edits:
            summary_parts.append(f"{len(config.transition_edits)} transition changes")

        if config.overlay_edits:
            summary_parts.append(f"{len(config.overlay_edits)} overlay modifications")

        if not summary_parts:
            summary_parts.append("no changes")

        return ", ".join(summary_parts)

    def get_recomposition_record(self, recomposition_id: str) -> Optional[RecompositionRecord]:
        """
        Get recomposition record by ID

        Args:
            recomposition_id: Recomposition ID

        Returns:
            Recomposition record if found
        """
        return self._recomposition_records.get(recomposition_id)

    def update_recomposition_status(
        self,
        recomposition_id: str,
        status: RecompositionStatus,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the status of a recomposition record

        Args:
            recomposition_id: Recomposition ID
            status: New status
            error_message: Error message if failed
            error_details: Detailed error information

        Returns:
            True if update was successful
        """
        record = self._recomposition_records.get(recomposition_id)
        if not record:
            return False

        if status == RecompositionStatus.COMPLETED:
            record.mark_completed()
        elif status == RecompositionStatus.FAILED:
            record.mark_failed(error_message or "Unknown error", error_details)
        elif status == RecompositionStatus.CANCELLED:
            record.status = RecompositionStatus.CANCELLED
        else:
            record.status = status

        logger.info(f"Updated recomposition {recomposition_id} status to {status.value}")
        return True

    def get_all_recomposition_records(self) -> List[RecompositionRecord]:
        """Get all recomposition records (for debugging/admin)"""
        return list(self._recomposition_records.values())
